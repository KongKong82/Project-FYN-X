"""
Streaming output handler for FYN-X.
Provides callbacks for processing response chunks as they're generated.
"""

import subprocess
import threading
import queue
from typing import Callable, Optional


class StreamingOutputHandler:
    """
    Handles streaming output from Ollama with chunk-based callbacks.
    Allows processing text as it's generated rather than waiting for completion.
    """
    
    def __init__(self, chunk_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize streaming handler.
        
        Args:
            chunk_callback: Function to call with each text chunk
                           Signature: callback(chunk: str) -> None
        """
        self.chunk_callback = chunk_callback
        self.chunk_queue = queue.Queue()
        self.full_response = []
        
    def process_stream(self, process: subprocess.Popen) -> str:
        """
        Process streaming output from Ollama subprocess.
        
        Args:
            process: Running Popen process
            
        Returns:
            Complete response text
        """
        self.full_response = []
        
        try:
            # Read output character by character or in small chunks
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                
                # Remove leading/trailing whitespace but keep newlines in content
                chunk = line
                
                if chunk:
                    self.full_response.append(chunk)
                    
                    # Call chunk callback if provided
                    if self.chunk_callback:
                        self.chunk_callback(chunk)
                    
                    # Also add to queue for other consumers
                    self.chunk_queue.put(chunk)
            
            # Wait for process to complete
            process.wait()
            
        except Exception as e:
            print(f"[ERROR] Streaming failed: {e}")
        
        # Signal end of stream
        self.chunk_queue.put(None)
        
        return ''.join(self.full_response)
    
    def get_chunks_iterator(self):
        """
        Get an iterator over chunks as they arrive.
        
        Yields:
            Text chunks, None when stream ends
        """
        while True:
            chunk = self.chunk_queue.get()
            if chunk is None:
                break
            yield chunk


class ChunkBuffer:
    """
    Buffers text chunks into sentence-like units for better TTS.
    Sends complete sentences to reduce choppy audio.
    """
    
    def __init__(self, callback: Callable[[str], None], 
                 sentence_endings: str = '.!?'):
        """
        Initialize chunk buffer.
        
        Args:
            callback: Function to call with buffered sentences
            sentence_endings: Characters that indicate sentence end
        """
        self.callback = callback
        self.sentence_endings = sentence_endings
        self.buffer = []
        
    def add_chunk(self, chunk: str):
        """Add a chunk to the buffer and flush if sentence complete."""
        self.buffer.append(chunk)
        
        # Check if we have a complete sentence
        current_text = ''.join(self.buffer)
        
        # Look for sentence endings
        for ending in self.sentence_endings:
            if ending in current_text:
                # Find the last sentence ending
                last_pos = current_text.rfind(ending)
                if last_pos != -1:
                    # Send everything up to and including the ending
                    complete_text = current_text[:last_pos + 1].strip()
                    
                    if complete_text:
                        self.callback(complete_text)
                    
                    # Keep remainder in buffer
                    remainder = current_text[last_pos + 1:]
                    self.buffer = [remainder] if remainder.strip() else []
                    return
    
    def flush(self):
        """Flush any remaining text in buffer."""
        if self.buffer:
            remaining = ''.join(self.buffer).strip()
            if remaining:
                self.callback(remaining)
            self.buffer = []


def create_sentence_chunker(output_callback: Callable[[str], None]) -> Callable[[str], None]:
    """
    Create a chunk callback that buffers into complete sentences.
    
    Args:
        output_callback: Function to call with complete sentences
        
    Returns:
        Chunk callback function
    """
    buffer = ChunkBuffer(output_callback)
    
    def chunk_callback(chunk: str):
        buffer.add_chunk(chunk)
    
    # Return a callback that also flushes on completion
    chunk_callback.flush = buffer.flush
    return chunk_callback


# Example usage for testing
if __name__ == "__main__":
    import time
    
    def print_chunk(chunk: str):
        """Example callback that prints chunks."""
        print(f"[CHUNK] {chunk}", end='', flush=True)
    
    def print_sentence(sentence: str):
        """Example callback that prints complete sentences."""
        print(f"\n[SENTENCE] {sentence}\n")
    
    # Test sentence chunker
    print("Testing sentence chunker:")
    chunker = create_sentence_chunker(print_sentence)
    
    test_chunks = [
        "Hello ", "there! ", "I am ", "FYN-X. ", 
        "How ", "may I ", "assist? ", "Let me ", "know."
    ]
    
    for chunk in test_chunks:
        chunker(chunk)
        time.sleep(0.1)
    
    chunker.flush()
