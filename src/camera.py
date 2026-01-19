"""
Camera module for FYN-X with face detection and recognition.
Supports both local computer webcam and edge compute device.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List
import time

# Try to import face_recognition library
FACE_RECOGNITION_AVAILABLE = False
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    pass


class Camera:
    """
    Camera interface for FYN-X.
    Supports local webcam or remote camera on edge device.
    """
    
    def __init__(self, source: str = 'local', camera_id: int = 0, 
                 enable_face_detection: bool = True,
                 enable_face_recognition: bool = True):
        """
        Initialize camera.
        
        Args:
            source: 'local' for computer webcam, 'edge' for edge device
            camera_id: Camera device ID (0 = default webcam)
            enable_face_detection: Enable face detection
            enable_face_recognition: Enable face recognition
        """
        self.source = source
        self.camera_id = camera_id
        self.enable_face_detection = enable_face_detection
        self.enable_face_recognition = enable_face_recognition and FACE_RECOGNITION_AVAILABLE
        
        self.cap = None
        self.known_faces = {}  # name -> face_encoding
        self.faces_dir = Path("data/faces")
        self.faces_dir.mkdir(parents=True, exist_ok=True)
        
        # Load Haar Cascade for face detection (fallback)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Load known faces
        if self.enable_face_recognition:
            self._load_known_faces()
    
    def connect(self) -> bool:
        """
        Connect to camera.
        
        Returns:
            True if successful, False otherwise
        """
        if self.source == 'local':
            return self._connect_local()
        elif self.source == 'edge':
            return self._connect_edge()
        else:
            print(f"[CAMERA ERROR] Unknown source: {self.source}")
            return False
    
    def _connect_local(self) -> bool:
        """Connect to local webcam."""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                print(f"[CAMERA ERROR] Could not open camera {self.camera_id}")
                return False
            
            # Test read
            ret, frame = self.cap.read()
            if not ret:
                print("[CAMERA ERROR] Could not read from camera")
                self.cap.release()
                return False
            
            print(f"[CAMERA] Connected to local camera {self.camera_id}")
            return True
            
        except Exception as e:
            print(f"[CAMERA ERROR] {e}")
            return False
    
    def _connect_edge(self) -> bool:
        """Connect to camera on edge device (via network stream)."""
        # TODO: Implement RTSP/HTTP stream from edge device
        print("[CAMERA] Edge camera not yet implemented")
        print("  Use source='local' for now")
        return False
    
    def disconnect(self):
        """Disconnect from camera."""
        if self.cap:
            self.cap.release()
            print("[CAMERA] Disconnected")
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame.
        
        Returns:
            Frame as numpy array, or None if failed
        """
        if not self.cap or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        return frame
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in frame.
        
        Args:
            frame: Input image
            
        Returns:
            List of face bounding boxes (x, y, w, h)
        """
        if not self.enable_face_detection:
            return []
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return [(x, y, w, h) for (x, y, w, h) in faces]
    
    def recognize_face(self, frame: np.ndarray) -> Optional[str]:
        """
        Recognize face in frame.
        
        Args:
            frame: Input image
            
        Returns:
            Name of recognized person, or None if unknown
        """
        if not self.enable_face_recognition or not FACE_RECOGNITION_AVAILABLE:
            return None
        
        if not self.known_faces:
            return None
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find faces in frame
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if not face_locations:
            return None
        
        # Get face encodings
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        if not face_encodings:
            return None
        
        # Compare with known faces
        for face_encoding in face_encodings:
            for name, known_encoding in self.known_faces.items():
                matches = face_recognition.compare_faces([known_encoding], face_encoding)
                
                if matches[0]:
                    return name
        
        return None
    
    def add_face(self, name: str, frame: Optional[np.ndarray] = None) -> bool:
        """
        Add a new face to the recognition database.
        
        Args:
            name: Person's name
            frame: Frame containing the face (if None, will capture)
            
        Returns:
            True if successful, False otherwise
        """
        if not FACE_RECOGNITION_AVAILABLE:
            print("[CAMERA ERROR] face_recognition library not installed")
            print("  Install with: pip install face-recognition --break-system-packages")
            return False
        
        # Capture frame if not provided
        if frame is None:
            frame = self.capture_frame()
            if frame is None:
                print("[CAMERA ERROR] Could not capture frame")
                return False
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find faces
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if not face_locations:
            print("[CAMERA ERROR] No face detected in frame")
            return False
        
        if len(face_locations) > 1:
            print("[CAMERA WARNING] Multiple faces detected, using first one")
        
        # Get face encoding
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        if not face_encodings:
            print("[CAMERA ERROR] Could not encode face")
            return False
        
        # Save encoding
        face_encoding = face_encodings[0]
        self.known_faces[name] = face_encoding
        
        # Save to file
        face_file = self.faces_dir / f"{name}.npy"
        np.save(face_file, face_encoding)
        
        print(f"[CAMERA] Added face: {name}")
        return True
    
    def _load_known_faces(self):
        """Load known faces from data/faces/."""
        if not FACE_RECOGNITION_AVAILABLE:
            return
        
        face_files = list(self.faces_dir.glob("*.npy"))
        
        for face_file in face_files:
            name = face_file.stem
            try:
                encoding = np.load(face_file)
                self.known_faces[name] = encoding
                print(f"[CAMERA] Loaded face: {name}")
            except Exception as e:
                print(f"[CAMERA ERROR] Could not load {face_file}: {e}")
        
        if self.known_faces:
            print(f"[CAMERA] Loaded {len(self.known_faces)} known faces")
    
    def list_known_faces(self) -> List[str]:
        """Get list of known face names."""
        return list(self.known_faces.keys())
    
    def show_preview(self, duration: int = 5, show_detection: bool = True):
        """
        Show camera preview window.
        
        Args:
            duration: How long to show (seconds), 0 = until 'q' pressed
            show_detection: Draw face detection boxes
        """
        if not self.cap or not self.cap.isOpened():
            print("[CAMERA ERROR] Camera not connected")
            return
        
        print(f"[CAMERA] Showing preview (press 'q' to quit)")
        
        start_time = time.time()
        
        while True:
            frame = self.capture_frame()
            if frame is None:
                break
            
            # Detect and draw faces
            if show_detection and self.enable_face_detection:
                faces = self.detect_faces(frame)
                
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Try recognition
                if self.enable_face_recognition:
                    name = self.recognize_face(frame)
                    if name:
                        cv2.putText(frame, name, (x, y-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            # Show frame
            cv2.imshow('FYN-X Camera', frame)
            
            # Check exit conditions
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            if duration > 0 and (time.time() - start_time) > duration:
                break
        
        cv2.destroyAllWindows()


def setup_instructions():
    """Print setup instructions."""
    print("\n" + "="*60)
    print("FYN-X CAMERA SETUP")
    print("="*60)
    
    print("\nBasic face detection (OpenCV only):")
    print("  pip install opencv-python --break-system-packages")
    
    print("\nAdvanced face recognition (optional):")
    print("  pip install face-recognition --break-system-packages")
    print("  Note: Requires Visual C++ Build Tools on Windows")
    
    print("\n" + "="*60 + "\n")


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    setup_instructions()
    
    # Test camera
    print("Testing camera connection...")
    camera = Camera(
        source='local',
        enable_face_detection=True,
        enable_face_recognition=FACE_RECOGNITION_AVAILABLE
    )
    
    if not camera.connect():
        print("Camera test failed!")
        sys.exit(1)
    
    print("\nCamera connected successfully!")
    
    # Show what's available
    print(f"Face detection: {'✓ Enabled' if camera.enable_face_detection else '✗ Disabled'}")
    print(f"Face recognition: {'✓ Enabled' if camera.enable_face_recognition else '✗ Disabled'}")
    
    if camera.known_faces:
        print(f"Known faces: {', '.join(camera.list_known_faces())}")
    else:
        print("No known faces yet")
    
    # Show preview
    print("\nShowing camera preview for 5 seconds...")
    camera.show_preview(duration=5, show_detection=True)
    
    camera.disconnect()
    print("\nCamera test complete!")
