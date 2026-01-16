"""
FYN-X: Personal Memory-Enhanced Conversational Droid
Main execution script with RAG-based memory retrieval.
"""

import subprocess
from pathlib import Path

from src.memory import MemoryManager, ConversationSession
from src.tag_extraction import extract_tags
from src.search import format_memories_for_prompt
from src.face_recognition_module import FaceRecognizer, get_speaker_identity


MODEL_NAME = "FYN-X-02"  # Ollama model name
MEMORY_SEARCH_LIMIT = 3  # Number of memories to inject into prompt
MIN_TURNS_TO_SAVE = 4    # Minimum conversation turns before saving
AUTO_SAVE_INTERVAL = 10   # Save every N turns


class FynxRunner:
    """Main application controller for FYN-X."""
    
    def __init__(self, use_face_recognition: bool = False):
        self.memory_manager = MemoryManager()
        self.face_recognizer = FaceRecognizer() if use_face_recognition else None
        self.current_session: ConversationSession = None
        self.turn_counter = 0
        
        print("=" * 60)
        print("FYN-X PERSONAL MEMORY SYSTEM")
        print("=" * 60)
        self._print_stats()
        print()
    
    def _print_stats(self):
        """Display memory database statistics."""
        stats = self.memory_manager.get_stats()
        print(f"Memory Database Stats:")
        print(f"  Total memories: {stats['total_memories']}")
        print(f"  Unique people: {stats['unique_people']}")
        print(f"  Unique topics: {stats['unique_topics']}")
        
        if stats.get('people'):
            print(f"  Known people: {', '.join(stats['people'][:5])}")
    
    def start_conversation(self):
        """Begin a new conversation session."""
        # Get speaker identity (from face recognition or manual)
        speaker_identity = get_speaker_identity(self.face_recognizer)
        
        self.current_session = ConversationSession(speaker_identity)
        self.turn_counter = 0
        
        print(f"\n{'='*60}")
        print(f"New conversation started with: {speaker_identity}")
        print(f"Type 'exit' to end conversation and save")
        print(f"Type 'stats' to see memory statistics")
        print(f"Type 'search <query>' to search memories")
        print(f"{'='*60}\n")
    
    def end_conversation(self, save: bool = True):
        """End current conversation and optionally save to memory."""
        if not self.current_session:
            return
        
        if save and self.current_session.should_save(MIN_TURNS_TO_SAVE):
            memory = self.current_session.to_memory()
            memory_id = self.memory_manager.add_memory(memory)
            print(f"\n✓ Conversation saved to memory (ID: {memory_id})")
            print(f"  Topics: {', '.join(memory.get('topics_discussed', []))}")
            print(f"  People: {', '.join(memory.get('people_mentioned', []))}")
        else:
            print("\n✗ Conversation not saved (too short or skipped)")
        
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
        # Extract tags from input
        tags = extract_tags(user_input)
        
        if not tags:
            return "No relevant memories to retrieve."
        
        # Search memories
        relevant_memories = self.memory_manager.search_by_tags(
            tags, 
            limit=MEMORY_SEARCH_LIMIT
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
        
        # Memory context (from database)
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
    
    def run_ollama(self, prompt: str) -> str:
        """
        Execute Ollama model with prompt.
        
        Args:
            prompt: Full prompt text
            
        Returns:
            Model response
        """
        try:
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
        
        if command.startswith("search "):
            query = user_input[7:].strip()
            tags = extract_tags(query)
            results = self.memory_manager.search_by_tags(tags, limit=5)
            
            print(f"\nSearch results for: {query}")
            print(f"Tags extracted: {tags}\n")
            
            if results:
                for i, memory in enumerate(results, 1):
                    print(f"--- Result {i} ---")
                    print(f"Date: {memory['timestamp']}")
                    print(f"Topics: {', '.join(memory.get('topics_discussed', []))}")
                    print(f"Summary: {memory.get('summary', 'N/A')[:200]}...")
                    print()
            else:
                print("No matching memories found.\n")
            
            return True
        
        return False
    
    def process_turn(self, user_input: str):
        """Process a single conversational turn."""
        # Add user input to session
        self.current_session.add_turn('user', user_input)
        
        # Build prompt with memory context
        prompt = self.build_prompt(user_input)
        
        # Get response from model
        response = self.run_ollama(prompt)
        
        # Add response to session
        self.current_session.add_turn('fynx', response)
        
        # Increment turn counter
        self.turn_counter += 1
        
        # Auto-save periodically
        if self.turn_counter % AUTO_SAVE_INTERVAL == 0:
            print("\n[Auto-saving conversation progress...]")
            memory = self.current_session.to_memory()
            self.memory_manager.add_memory(memory)
            print("[Saved]\n")
        
        return response
    
    def run_interactive(self):
        """Main interactive loop."""
        self.start_conversation()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle exit
                if user_input.lower() == "exit":
                    self.end_conversation(save=True)
                    print("\nFYN-X shutting down. Memories preserved.")
                    break
                
                # Handle special commands
                if self.handle_command(user_input):
                    continue
                
                # Process normal conversation turn
                response = self.process_turn(user_input)
                
                # Display response
                print(f"\nFYN-X: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Saving conversation...")
                self.end_conversation(save=True)
                break
            except Exception as e:
                print(f"\n[ERROR] {str(e)}\n")


def main():
    """Entry point."""
    # Check if Ollama is available
    try:
        subprocess.run(["ollama", "list"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("ERROR: Ollama not found or not running.")
        print("Please install Ollama from https://ollama.ai")
        return
    
    # Initialize and run
    runner = FynxRunner(use_face_recognition=False)
    runner.run_interactive()


if __name__ == "__main__":
    main()
