"""
Network publisher for sending FYN-X responses to edge devices.
Supports both raw socket communication and ROS2 publishing.
"""

import socket
import json
from typing import Optional, Dict, Any


class NetworkPublisher:
    """
    Publishes text chunks over network to edge devices.
    Supports simple TCP socket protocol.
    """
    
    def __init__(self, host: str = "localhost", port: int = 5555):
        """
        Initialize network publisher.
        
        Args:
            host: Target host (IP address or hostname)
            port: Target port
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        
    def connect(self) -> bool:
        """
        Connect to the edge device.
        
        Returns:
            True if connection successful
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"✓ Connected to edge device at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to {self.host}:{self.port}: {e}")
            self.connected = False
            return False
    
    def publish_chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Publish a text chunk to the edge device.
        
        Args:
            text: Text chunk to send
            metadata: Optional metadata (speaker, timestamp, etc.)
        """
        if not self.connected:
            return
        
        try:
            # Create message with metadata
            message = {
                'type': 'text_chunk',
                'text': text,
                'metadata': metadata or {}
            }
            
            # Serialize and send
            data = json.dumps(message).encode('utf-8')
            length = len(data)
            
            # Send length prefix (4 bytes) then data
            self.socket.sendall(length.to_bytes(4, byteorder='big'))
            self.socket.sendall(data)
            
        except Exception as e:
            print(f"[ERROR] Failed to publish chunk: {e}")
            self.connected = False
    
    def publish_complete(self):
        """Signal that the response is complete."""
        if not self.connected:
            return
        
        try:
            message = {
                'type': 'response_complete',
                'text': '',
                'metadata': {}
            }
            data = json.dumps(message).encode('utf-8')
            length = len(data)
            
            self.socket.sendall(length.to_bytes(4, byteorder='big'))
            self.socket.sendall(data)
            
        except Exception as e:
            print(f"[ERROR] Failed to send completion signal: {e}")
    
    def disconnect(self):
        """Disconnect from the edge device."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            self.connected = False
            print("✓ Disconnected from edge device")


class ROS2Publisher:
    """
    Publishes text chunks via ROS2.
    Requires rclpy to be installed.
    """
    
    def __init__(self, topic_name: str = "/fynx/tts_input"):
        """
        Initialize ROS2 publisher.
        
        Args:
            topic_name: ROS2 topic name
        """
        self.topic_name = topic_name
        self.node = None
        self.publisher = None
        self.initialized = False
        
        try:
            import rclpy
            from std_msgs.msg import String
            
            self.rclpy = rclpy
            self.String = String
            
        except ImportError:
            print("[WARNING] rclpy not installed. ROS2 publishing disabled.")
            print("Install with: pip install rclpy std_msgs")
            return
    
    def initialize(self) -> bool:
        """
        Initialize ROS2 node and publisher.
        
        Returns:
            True if initialization successful
        """
        if not hasattr(self, 'rclpy'):
            return False
        
        try:
            self.rclpy.init()
            self.node = self.rclpy.create_node('fynx_publisher')
            self.publisher = self.node.create_publisher(
                self.String, 
                self.topic_name, 
                10
            )
            self.initialized = True
            print(f"✓ ROS2 publisher initialized on topic: {self.topic_name}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to initialize ROS2: {e}")
            return False
    
    def publish_chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Publish a text chunk via ROS2.
        
        Args:
            text: Text chunk to send
            metadata: Optional metadata (currently not used in std_msgs/String)
        """
        if not self.initialized:
            return
        
        try:
            msg = self.String()
            msg.data = text
            self.publisher.publish(msg)
            
            # Spin once to process callbacks
            self.rclpy.spin_once(self.node, timeout_sec=0.01)
            
        except Exception as e:
            print(f"[ERROR] Failed to publish to ROS2: {e}")
    
    def publish_complete(self):
        """Signal that the response is complete."""
        # Could publish a special marker or use a different topic
        if self.initialized:
            msg = self.String()
            msg.data = "<RESPONSE_COMPLETE>"
            self.publisher.publish(msg)
    
    def shutdown(self):
        """Shutdown ROS2 node."""
        if self.node:
            self.node.destroy_node()
        if hasattr(self, 'rclpy') and self.rclpy.ok():
            self.rclpy.shutdown()
        self.initialized = False
        print("✓ ROS2 publisher shutdown")


def create_network_callback(publisher: NetworkPublisher) -> callable:
    """
    Create a callback function that publishes to network.
    
    Args:
        publisher: NetworkPublisher instance
        
    Returns:
        Callback function for streaming chunks
    """
    def callback(text: str):
        publisher.publish_chunk(text)
    
    return callback


def create_ros2_callback(publisher: ROS2Publisher) -> callable:
    """
    Create a callback function that publishes to ROS2.
    
    Args:
        publisher: ROS2Publisher instance
        
    Returns:
        Callback function for streaming chunks
    """
    def callback(text: str):
        publisher.publish_chunk(text)
    
    return callback


# Example usage
if __name__ == "__main__":
    import time
    
    # Test network publisher
    print("Testing NetworkPublisher:")
    net_pub = NetworkPublisher(host="localhost", port=5555)
    
    if net_pub.connect():
        test_chunks = ["Hello ", "from ", "FYN-X! ", "How ", "are ", "you?"]
        
        for chunk in test_chunks:
            net_pub.publish_chunk(chunk)
            time.sleep(0.2)
        
        net_pub.publish_complete()
        net_pub.disconnect()
    
    print("\n" + "="*50 + "\n")
    
    # Test ROS2 publisher
    print("Testing ROS2Publisher:")
    ros2_pub = ROS2Publisher(topic_name="/fynx/tts_input")
    
    if ros2_pub.initialize():
        test_chunks = ["ROS2 ", "test ", "message."]
        
        for chunk in test_chunks:
            ros2_pub.publish_chunk(chunk)
            time.sleep(0.2)
        
        ros2_pub.publish_complete()
        ros2_pub.shutdown()
