"""
FYN-X: Personal Memory-Enhanced Conversational Droid
Main execution script with RAG-based memory retrieval and streaming output.
UPDATED: Automatic name detection, only saves memories for known speakers.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Callable

from src.memory import MemoryManager, ConversationSession
from src.tag_extraction import extract_tags
from src.search import format_memories_for_prompt
from src.face_recognition_module import FaceRecognizer
from src.streaming import StreamingOutputHandler, create_sentence_chunker
from src.network import NetworkPublisher, ROS2Publisher, create_network_callback, create_ros2_callback
from src import benchmarks


MODEL_NAME = "FYN-X"  # Ollama model name
MEMORY_SEARCH_LIMIT = 3  # Number of memories to inject into prompt
MIN_TURNS_TO_SAVE = 4    # Minimum conversation turns before saving
AUTO_SAVE_INTERVAL = 10   # Save every N turns

# Network configuration
ENABLE_NETWORK = False    # Set to True to enable network publishing
NETWORK_HOST = "raspberrypi.local"  # or IP address like "192.168.1.100"
NETWORK_PORT = 5555

# ROS2 configuration  
ENABLE_ROS2 = False       # Set to True to enable ROS2 publishing
ROS2_TOPIC = "/fynx/tts_input"


class FynxRunner:
    """Main application controller for FYN-X with streaming support."""
    
    def __init__(self, use_face_recognition: bool = False, 
                 enable_streaming: bool = True,
                 enable_network: bool = ENABLE_NETWORK,
                 enable_ros2: bool = ENABLE_ROS2,
                 enable_benchmarks: bool = True):
        self.memory_manager = MemoryManager()
        self.face_recognizer = FaceRecognizer() if use_face_recognition else None
        self.current_session: ConversationSession = None
        self.turn_counter = 0
        self.enable_streaming = enable_streaming
        self.enable_benchmarks = enable_benchmarks
        
        # Initialize network publishers
        self.network_publisher = None
        self.ros2_publisher = None
        
        if enable_network:
            self.network_publisher = NetworkPublisher(NETWORK_HOST, NETWORK_PORT)
            if not self.network_publisher.connect():
                print("[WARNING] Network publishing disabled due to connection failure")
                self.network_publisher = None
        
        if enable_ros2:
            self.ros2_publisher = ROS2Publisher(ROS2_TOPIC)
            if not self.ros2_publisher.initialize():
                print("[WARNING] ROS2 publishing disabled due to initialization failure")
                self.ros2_publisher = None
        
        print("=" * 60)
        print("FYN-X PERSONAL MEMORY SYSTEM")
        if enable_streaming:
            print("(Streaming Mode Enabled)")
        if enable_benchmarks:
            print("(Performance Benchmarking Enabled)")
        if self.network_publisher:
            print(f"(Network: {NETWORK_HOST}:{NETWORK_PORT})")
        if self.ros2_publisher:
            print(f"(ROS2: {ROS2_TOPIC})")
        print("=" * 60)
        self._print_stats()
        print()
    
    def _print_stats(self):
        """Display memory database statistics."""
        stats = self.memory_manager.get_stats()
        print(f"Memory Database Stats:")
        print(f"  Total memories: {stats['total_memories']}")
        print(f"  Unique speakers: {stats['unique_speakers']}")
        print(f"  Unique people: {stats['unique_people']}")
        print(f"  Unique topics: {stats['unique_topics']}")
        
        if stats.get('speakers'):
            print(f"  Known speakers: {', '.join(stats['speakers'][:5])}")
    
    def start_conversation(self):
        """Begin a new conversation session."""
        current_speaker_name = None
        
        # Try face recognition first if enabled
        if self.face_recognizer:
            with benchmarks.track_time("face_recognition"):
                speaker_name = self.face_recognizer.recognize()
            
            if speaker_name and speaker_name != "unknown":
                current_speaker_name = speaker_name
                print(f"[FYN-X] Recognized: {speaker_name}")
        
        # Start session (speaker name may be None)
        self.current_session = ConversationSession(speaker_name=current_speaker_name)
        self.turn_counter = 0
        
        print(f"\n{'='*60}")
        if current_speaker_name:
            print(f"Conversation started with: {current_speaker_name}")
        else:
            print("Conversation started")
            print("Note: I'll only remember our conversation if you introduce yourself")
        print(f"Type 'exit' to end conversation and save")
        print(f"Type 'stats' to see memory statistics")
        print(f"Type 'search <query>' to search memories")
        print(f"Type 'setname <name>' to set your name manually")
        if self.enable_benchmarks:
            print(f"Type 'benchmark' to see performance stats")
        print(f"{'='*60}\n")
    
    def end_conversation(self, save: bool = True):
        """End current conversation and optionally save to memory."""
        if not self.current_session:
            return
        
        # Only save if we know who we're talking to
        if save and self.current_session.should_save(MIN_TURNS_TO_SAVE):
            with benchmarks.track_time("save_memory"):
                memory = self.current_session.to_memory()
                memory_id = self.memory_manager.add_memory(memory)
            
            print(f"\n✓ Conversation saved to memory (ID: {memory_id})")
            print(f"  Speaker: {self.current_session.speaker_name}")
            print(f"  Topics: {', '.join(memory.get('topics_discussed', []))}")
            print(f"  People: {', '.join(memory.get('people_mentioned', []))}")
            
            # Show important sentences that were saved
            important = memory.get('important_sentences', [])
            if important:
                print(f"  Saved {len(important)} important sentence(s)")
        elif not self.current_session.can_save_memory():
            print("\n✗ Conversation not saved - I don't know who you are")
            print("  (Introduce yourself in future conversations so I can remember you)")
        else:
            print("\n✗ Conversation not saved (too short)")
        
        self.current_session = None
        self.turn_counter = 0
    
    def retrieve_relevant_memories(self, user_input: str) -> str:
        """
        Extract tags from input and retrieve relevant memories.
        
        Args:
            user_input: User's text input
            
        Returns:
            Formatted memory block for prompt injection
        """
        with benchmarks.track_time("tag_extraction", {"input_length": len(user_input)}):
            tags = extract_tags(user_input)
        
        if not tags:
            return "No relevant memories to retrieve."
        
        # Search memories (filtered by speaker if known)
        speaker_name = self.current_session.speaker_name if self.current_session else None
        
        with benchmarks.track_time("memory_search", {"tag_count": len(tags)}):
            relevant_memories = self.memory_manager.search_by_tags(
                tags, 
                limit=MEMORY_SEARCH_LIMIT,
                speaker_name=speaker_name
            )
        
        # Format for prompt
        return format_memories_for_prompt(relevant_memories, MEMORY_SEARCH_LIMIT)
    
    def build_prompt(self, user_input: str) -> str:
        """
        Construct full prompt with memory context and conversation history.
        
        Args:
            user_input: Current user input
            
        Returns:
            Complete prompt for LLM
        """
        parts = []
        
        # Speaker identity context
        if self.current_session:
            identity_context = self.current_session.get_speaker_identity_context()
            parts.append(identity_context)
            parts.append("")
        
        # Memory context (from database) - only if we know who we're talking to
        if self.current_session and self.current_session.speaker_name:
            memory_block = self.retrieve_relevant_memories(user_input)
            if memory_block and "No relevant" not in memory_block:
                parts.append("MEMORY ARCHIVES (relevant past interactions):")
                parts.append(memory_block)
                parts.append("")
        
        # Recent conversation context
        if self.current_session and len(self.current_session.history) > 0:
            context = self.current_session.get_context_summary(last_n_turns=4)
            parts.append("RECENT CONVERSATION CONTEXT:")
            parts.append(context)
            parts.append("")
        
        # Current interaction
        parts.append("=" * 40)
        parts.append("CURRENT INTERACTION")
        parts.append("=" * 40)
        parts.append(f"User: {user_input}")
        parts.append("FYN-X:")
        
        return "\n".join(parts)
    
    def _create_output_callback(self) -> Callable[[str], None]:
        """Create callback for handling output chunks."""
        callbacks = []
        
        # Always print to console
        def console_callback(chunk: str):
            print(chunk, end='', flush=True)
        callbacks.append(console_callback)
        
        # Add network publisher if enabled
        if self.network_publisher:
            callbacks.append(create_network_callback(self.network_publisher))
        
        # Add ROS2 publisher if enabled
        if self.ros2_publisher:
            callbacks.append(create_ros2_callback(self.ros2_publisher))
        
        # Create combined callback
        def combined_callback(chunk: str):
            for callback in callbacks:
                try:
                    callback(chunk)
                except Exception as e:
                    print(f"\n[ERROR in callback]: {e}")
        
        return combined_callback
    
    def run_ollama_streaming(self, prompt: str) -> str:
        """
        Execute Ollama model with streaming output.
        
        Args:
            prompt: Full prompt text
            
        Returns:
            Model response
        """
        try:
            # Start Ollama process
            with benchmarks.track_time("ollama_startup"):
                process = subprocess.Popen(
                    ["ollama", "run", MODEL_NAME],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    bufsize=1
                )
            
            # Send prompt
            process.stdin.write(prompt)
            process.stdin.close()
            
            # Create output callback
            output_callback = self._create_output_callback()
            sentence_callback = create_sentence_chunker(output_callback)
            
            # Create streaming handler
            handler = StreamingOutputHandler(chunk_callback=sentence_callback)
            
            # Process stream (this is the main inference time)
            with benchmarks.track_time("ollama_inference", {"prompt_length": len(prompt)}):
                response = handler.process_stream(process)
            
            # Flush any remaining buffered text
            if hasattr(sentence_callback, 'flush'):
                sentence_callback.flush()
            
            # Signal completion to publishers
            if self.network_publisher:
                self.network_publisher.publish_complete()
            if self.ros2_publisher:
                self.ros2_publisher.publish_complete()
            
            return response.strip()
            
        except FileNotFoundError:
            return "[ERROR] Ollama not found. Please install Ollama and ensure it's in your PATH."
        except Exception as e:
            return f"[ERROR] {str(e)}"
    
    def run_ollama(self, prompt: str) -> str:
        """
        Execute Ollama model (non-streaming fallback).
        
        Args:
            prompt: Full prompt text
            
        Returns:
            Model response
        """
        try:
            with benchmarks.track_time("ollama_inference_full", {"prompt_length": len(prompt)}):
                process = subprocess.run(
                    ["ollama", "run", MODEL_NAME],
                    input=prompt,
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    timeout=60
                )
            
            if process.returncode != 0:
                raise RuntimeError(f"Ollama error: {process.stderr}")
            
            return process.stdout.strip()
            
        except FileNotFoundError:
            return "[ERROR] Ollama not found. Please install Ollama and ensure it's in your PATH."
        except subprocess.TimeoutExpired:
            return "[ERROR] Response timeout. Model took too long to respond."
        except Exception as e:
            return f"[ERROR] {str(e)}"
    
    def handle_command(self, user_input: str) -> bool:
        """
        Handle special commands.
        
        Returns:
            True if command was handled, False otherwise
        """
        command = user_input.lower().strip()
        
        if command == "stats":
            print()
            self._print_stats()
            print()
            return True
        
        if command == "benchmark" and self.enable_benchmarks:
            benchmarks.print_all_module_stats(last_n=10)
            return True
        
        if command.startswith("setname "):
            name = user_input[8:].strip()
            if name:
                old_name = self.current_session.speaker_name
                self.current_session.set_speaker_name(name)
                print(f"\n✓ Name set to: {name}")
                
                if not old_name:
                    print("  I'll now start remembering our conversation!\n")
                else:
                    print()
            return True
        
        if command.startswith("search "):
            query = user_input[7:].strip()
            tags = extract_tags(query)
            speaker_name = self.current_session.speaker_name if self.current_session else None
            results = self.memory_manager.search_by_tags(
                tags, 
                limit=5,
                speaker_name=speaker_name
            )
            
            print(f"\nSearch results for: {query}")
            print(f"Tags extracted: {tags}\n")
            
            if results:
                for i, memory in enumerate(results, 1):
                    print(f"--- Result {i} ---")
                    print(f"Date: {memory['timestamp']}")
                    speaker = memory.get('speaker_name', 'Unknown')
                    print(f"Speaker: {speaker}")
                    print(f"Topics: {', '.join(memory.get('topics_discussed', []))}")
                    
                    # Show important sentences if available
                    important = memory.get('important_sentences', [])
                    if important:
                        print("Important sentences:")
                        for sent in important[:3]:
                            print(f"  • {sent['text']}")
                    else:
                        print(f"Summary: {memory.get('summary', 'N/A')[:200]}...")
                    print()
            else:
                print("No matching memories found.\n")
            
            return True
        
        return False
    
    def process_turn(self, user_input: str):
        """Process a single conversational turn."""
        # Check for name introduction BEFORE adding to history
        detected_name = self.current_session.detect_name_from_turn(user_input)
        
        if detected_name:
            print(f"\n[✓ Detected: {detected_name}. I'll remember you now!]\n")
        
        # Add user input to session
        self.current_session.add_turn('user', user_input)
        
        # Build prompt with memory context
        with benchmarks.track_time("prompt_building"):
            prompt = self.build_prompt(user_input)
        
        # Get response from model
        if self.enable_streaming:
            response = self.run_ollama_streaming(prompt)
        else:
            response = self.run_ollama(prompt)
        
        # Add response to session
        self.current_session.add_turn('fynx', response)
        
        # Increment turn counter
        self.turn_counter += 1
        
        # Auto-save periodically (only if we know who we're talking to)
        if self.turn_counter % AUTO_SAVE_INTERVAL == 0 and self.current_session.can_save_memory():
            print("\n[Auto-saving conversation progress...]")
            memory = self.current_session.to_memory()
            self.memory_manager.add_memory(memory)
            print("[Saved]\n")
        
        return response
    
    def run_interactive(self):
        """Main interactive loop."""
        # Start benchmark session if enabled
        if self.enable_benchmarks:
            benchmarks.start_session()
        
        self.start_conversation()
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                # Handle exit
                if user_input.lower() == "exit":
                    self.end_conversation(save=True)
                    
                    # Print benchmark summary
                    if self.enable_benchmarks:
                        benchmarks.end_session(print_summary=True)
                    
                    print("\nFYN-X shutting down. Memories preserved.")
                    break
                
                # Handle special commands
                if self.handle_command(user_input):
                    continue
                
                # Process normal conversation turn
                print("\nFYN-X: ", end='', flush=True)
                response = self.process_turn(user_input)
                
                # Response already printed by streaming
                if not self.enable_streaming:
                    print(response)
                
                print()  # Extra newline for readability
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Saving conversation...")
                self.end_conversation(save=True)
                
                if self.enable_benchmarks:
                    benchmarks.end_session(print_summary=True)
                
                break
            except Exception as e:
                print(f"\n[ERROR] {str(e)}\n")
        
        # Cleanup publishers
        if self.network_publisher:
            self.network_publisher.disconnect()
        if self.ros2_publisher:
            self.ros2_publisher.shutdown()


def main():
    """Entry point."""
    # Parse command line arguments
    enable_network = "--network" in sys.argv
    enable_ros2 = "--ros2" in sys.argv
    disable_streaming = "--no-streaming" in sys.argv
    disable_benchmarks = "--no-benchmarks" in sys.argv
    
    # Check if Ollama is available
    try:
        subprocess.run(["ollama", "list"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("ERROR: Ollama not found or not running.")
        print("Please install Ollama from https://ollama.ai")
        return
    
    # Initialize and run
    runner = FynxRunner(
        use_face_recognition=False,
        enable_streaming=not disable_streaming,
        enable_network=enable_network,
        enable_ros2=enable_ros2,
        enable_benchmarks=not disable_benchmarks
    )
    runner.run_interactive()


if __name__ == "__main__":
    main()
