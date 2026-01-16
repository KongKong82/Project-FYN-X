#!/usr/bin/env python3
"""
FYN-X Network TTS Receiver for Raspberry Pi
Receives text chunks over TCP socket and plays them through TTS.

This is a simpler alternative to ROS2 that uses raw TCP sockets.
"""

import socket
import json
import threading
import queue
import subprocess
import argparse
import signal
import sys


class NetworkTTSReceiver:
    """
    TCP server that receives text chunks and speaks them via TTS.
    """
    
    def __init__(self, host="0.0.0.0", port=5555, tts_engine="espeak"):
        self.host = host
        self.port = port
        self.tts_engine = tts_engine
        self.running = False
        
        # Text queue for TTS processing
        self.text_queue = queue.Queue()
        
        # Socket server
        self.server_socket = None
        
    def start(self):
        """Start the receiver server."""
        print(f"Starting FYN-X TTS Receiver on {self.host}:{self.port}")
        print(f"TTS Engine: {self.tts_engine}")
        
        # Create socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        
        self.running = True
        
        # Start TTS worker thread
        tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        tts_thread.start()
        
        print(f"✓ Server listening on {self.host}:{self.port}")
        print("Waiting for FYN-X connection...")
        
        # Accept connections
        try:
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"✓ Connected to FYN-X at {address}")
                    
                    # Handle connection in separate thread
                    connection_thread = threading.Thread(
                        target=self._handle_connection,
                        args=(client_socket,),
                        daemon=True
                    )
                    connection_thread.start()
                    
                except socket.timeout:
                    continue
                    
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.stop()
    
    def _handle_connection(self, client_socket):
        """Handle incoming connection from FYN-X."""
        try:
            while self.running:
                # Read length prefix (4 bytes)
                length_data = client_socket.recv(4)
                if not length_data:
                    break
                
                message_length = int.from_bytes(length_data, byteorder='big')
                
                # Read message data
                message_data = b''
                while len(message_data) < message_length:
                    chunk = client_socket.recv(message_length - len(message_data))
                    if not chunk:
                        break
                    message_data += chunk
                
                # Parse message
                message = json.loads(message_data.decode('utf-8'))
                
                msg_type = message.get('type')
                text = message.get('text', '')
                
                if msg_type == 'text_chunk' and text:
                    print(f"[RX] {text[:50]}{'...' if len(text) > 50 else ''}")
                    self.text_queue.put(text)
                    
                elif msg_type == 'response_complete':
                    print("[RX] Response complete")
                    
        except Exception as e:
            print(f"[ERROR] Connection error: {e}")
        finally:
            client_socket.close()
            print("✗ Connection closed")
    
    def _tts_worker(self):
        """Worker thread that processes TTS queue."""
        while True:
            try:
                # Get text from queue (blocking)
                text = self.text_queue.get(timeout=0.1)
                
                # Speak the text
                self._speak(text)
                
                # Mark task as done
                self.text_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ERROR] TTS error: {e}")
    
    def _speak(self, text: str):
        """Convert text to speech and play audio."""
        try:
            if self.tts_engine == "espeak":
                self._speak_espeak(text)
            elif self.tts_engine == "piper":
                self._speak_piper(text)
            elif self.tts_engine == "festival":
                self._speak_festival(text)
            else:
                print(f"[ERROR] Unknown TTS engine: {self.tts_engine}")
                
        except Exception as e:
            print(f"[ERROR] Failed to speak: {e}")
    
    def _speak_espeak(self, text: str):
        """Speak using espeak (robotic voice, perfect for droids!)."""
        try:
            subprocess.run(
                ['espeak', '-v', 'en', '-s', '160', '-p', '40', text],
                check=True,
                capture_output=True
            )
        except FileNotFoundError:
            print("[ERROR] espeak not found. Install with: sudo apt install espeak")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] espeak failed: {e}")
    
    def _speak_piper(self, text: str):
        """Speak using Piper TTS (high quality neural voice)."""
        # Note: Requires Piper installation and model
        voice_model = "/home/pi/piper/models/en_US-lessac-medium.onnx"
        
        try:
            # Generate audio with Piper
            piper_process = subprocess.Popen(
                ['piper', '--model', voice_model, '--output-raw'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Play audio with aplay
            aplay_process = subprocess.Popen(
                ['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw', '-'],
                stdin=piper_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Send text
            piper_process.stdin.write(text.encode('utf-8'))
            piper_process.stdin.close()
            
            # Wait
            aplay_process.wait()
            
        except FileNotFoundError:
            print("[ERROR] piper not found. Install Piper TTS first.")
    
    def _speak_festival(self, text: str):
        """Speak using Festival TTS."""
        try:
            process = subprocess.Popen(
                ['festival', '--tts'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            process.communicate(input=text.encode('utf-8'))
        except FileNotFoundError:
            print("[ERROR] festival not found. Install with: sudo apt install festival")
    
    def stop(self):
        """Stop the receiver server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("✓ Server stopped")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\nShutting down gracefully...")
    sys.exit(0)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='FYN-X Network TTS Receiver')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5555, help='Port to listen on (default: 5555)')
    parser.add_argument('--tts', default='espeak', choices=['espeak', 'piper', 'festival'],
                      help='TTS engine to use (default: espeak)')
    
    args = parser.parse_args()
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and start receiver
    receiver = NetworkTTSReceiver(
        host=args.host,
        port=args.port,
        tts_engine=args.tts
    )
    
    try:
        receiver.start()
    except Exception as e:
        print(f"[ERROR] Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
