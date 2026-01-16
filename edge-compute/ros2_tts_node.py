#!/usr/bin/env python3
"""
FYN-X ROS2 TTS Node for Raspberry Pi
Subscribes to text chunks and plays them through TTS.

This script runs on the Raspberry Pi and receives streaming text
from the main FYN-X system, converting it to speech in real-time.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import subprocess
import threading
import queue
import time


class FynxTTSNode(Node):
    """
    ROS2 node that receives text chunks and speaks them via TTS.
    """
    
    def __init__(self, tts_engine="piper", voice_model=None):
        super().__init__('fynx_tts_node')
        
        # Configuration
        self.tts_engine = tts_engine
        self.voice_model = voice_model
        
        # Text queue for TTS processing
        self.text_queue = queue.Queue()
        
        # TTS worker thread
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        
        # Create subscriber
        self.subscription = self.create_subscription(
            String,
            '/fynx/tts_input',
            self.text_callback,
            10
        )
        
        self.get_logger().info(f'FYN-X TTS Node initialized with {tts_engine} engine')
        self.get_logger().info('Listening on topic: /fynx/tts_input')
    
    def text_callback(self, msg):
        """Callback for received text chunks."""
        text = msg.data
        
        # Check for completion signal
        if text == "<RESPONSE_COMPLETE>":
            self.get_logger().info('Response complete signal received')
            return
        
        # Add to queue for TTS processing
        self.text_queue.put(text)
        self.get_logger().debug(f'Queued text: {text[:50]}...')
    
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
                self.get_logger().error(f'TTS error: {e}')
    
    def _speak(self, text: str):
        """
        Convert text to speech and play audio.
        
        Args:
            text: Text to speak
        """
        try:
            if self.tts_engine == "piper":
                self._speak_piper(text)
            elif self.tts_engine == "espeak":
                self._speak_espeak(text)
            elif self.tts_engine == "festival":
                self._speak_festival(text)
            else:
                self.get_logger().error(f'Unknown TTS engine: {self.tts_engine}')
                
        except Exception as e:
            self.get_logger().error(f'Failed to speak text: {e}')
    
    def _speak_piper(self, text: str):
        """Speak using Piper TTS (high quality neural TTS)."""
        # Piper command: echo "text" | piper --model <model> --output_file - | aplay
        
        if not self.voice_model:
            # Default to a robotic-sounding voice
            self.voice_model = "/home/pi/piper/models/en_US-lessac-medium.onnx"
        
        try:
            # Generate audio with Piper
            piper_process = subprocess.Popen(
                ['piper', '--model', self.voice_model, '--output-raw'],
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
            
            # Send text to Piper
            piper_process.stdin.write(text.encode('utf-8'))
            piper_process.stdin.close()
            
            # Wait for completion
            aplay_process.wait()
            
        except FileNotFoundError:
            self.get_logger().error('Piper not found. Install with: pip install piper-tts')
    
    def _speak_espeak(self, text: str):
        """Speak using espeak (lightweight, robotic voice)."""
        try:
            subprocess.run(
                ['espeak', '-v', 'en', '-s', '160', text],
                check=True,
                capture_output=True
            )
        except FileNotFoundError:
            self.get_logger().error('espeak not found. Install with: sudo apt install espeak')
    
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
            self.get_logger().error('festival not found. Install with: sudo apt install festival')


def main(args=None):
    """Main entry point."""
    rclpy.init(args=args)
    
    # Configuration - change these as needed
    TTS_ENGINE = "espeak"  # Options: "piper", "espeak", "festival"
    VOICE_MODEL = None      # Path to Piper voice model (if using Piper)
    
    # Create and run node
    node = FynxTTSNode(tts_engine=TTS_ENGINE, voice_model=VOICE_MODEL)
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down FYN-X TTS Node')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
