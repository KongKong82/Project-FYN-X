"""
FYN-X Model Rebuild Script
Rebuilds the FYN-X model with bug fixes and GPU optimization.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True, check=True)
        print(f"\n✓ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} - FAILED")
        print(f"Error: {e}")
        return False
    except FileNotFoundError:
        print(f"\n✗ {description} - COMMAND NOT FOUND")
        print(f"Make sure Ollama is installed and in your PATH")
        return False


def check_ollama():
    """Check if Ollama is installed."""
    print("\n" + "="*60)
    print("CHECKING OLLAMA INSTALLATION")
    print("="*60)
    
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✓ Ollama is installed")
        print("\nCurrently installed models:")
        print(result.stdout)
        return True
    except FileNotFoundError:
        print("✗ Ollama not found!")
        print("\nPlease install Ollama from: https://ollama.ai/download")
        return False
    except subprocess.CalledProcessError:
        print("✗ Ollama is installed but not responding")
        print("Try running: ollama serve")
        return False


def check_gpu():
    """Check GPU availability."""
    print("\n" + "="*60)
    print("CHECKING GPU")
    print("="*60)
    
    # Try NVIDIA
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✓ NVIDIA GPU detected:")
        print(result.stdout.strip())
        return "NVIDIA"
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    
    # Check if AMD
    try:
        result = subprocess.run(
            ["rocm-smi"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✓ AMD GPU detected (ROCm)")
        return "AMD"
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    
    # Check if Apple Silicon
    if sys.platform == "darwin":
        print("✓ Running on macOS (Metal GPU support)")
        return "Apple"
    
    print("⚠ No GPU detected - will run on CPU (slower)")
    print("This is okay for testing, but responses will be slower.")
    return "CPU"


def rebuild_model():
    """Rebuild the FYN-X model."""
    modelfile = Path("FYN-X.modelfile")
    
    if not modelfile.exists():
        print(f"\n✗ Modelfile not found: {modelfile}")
        print("Make sure you're running this script from the fynx directory")
        return False
    
    # Step 1: Remove old model (ignore errors if it doesn't exist)
    print("\n" + "="*60)
    print("REMOVING OLD MODEL (if exists)")
    print("="*60)
    subprocess.run(["ollama", "rm", "FYN-X"], capture_output=True)
    print("Old model removed (or didn't exist)")
    
    # Step 2: Create new model
    success = run_command(
        ["ollama", "create", "FYN-X", "-f", "FYN-X.modelfile"],
        "Creating FYN-X model with bug fixes and GPU optimization"
    )
    
    return success


def verify_model():
    """Verify the model was created successfully."""
    print("\n" + "="*60)
    print("VERIFYING MODEL")
    print("="*60)
    
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if "FYN-X" in result.stdout:
            print("✓ FYN-X model found!")
            print("\nModel details:")
            # Extract and print FYN-X line
            for line in result.stdout.split('\n'):
                if 'FYN-X' in line:
                    print(f"  {line}")
            return True
        else:
            print("✗ FYN-X model not found in list")
            return False
            
    except subprocess.CalledProcessError:
        print("✗ Could not verify model")
        return False


def test_model():
    """Quick test of the model."""
    print("\n" + "="*60)
    print("QUICK MODEL TEST")
    print("="*60)
    print("\nSending test prompt to FYN-X...")
    print("This may take a moment on first run (loading model)...\n")
    
    try:
        result = subprocess.run(
            ["ollama", "run", "FYN-X"],
            input="Hello, what is your designation?",
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        
        print("="*60)
        print("FYN-X Response:")
        print("="*60)
        print(result.stdout.strip())
        print("="*60)
        
        # Check for common issues
        if "*" in result.stdout or "(" in result.stdout:
            print("\n⚠ Warning: Response contains emotes or actions")
            print("Model may need further training")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("✗ Model test timed out (took >30s)")
        print("This might indicate GPU is not being used")
        return False
    except subprocess.CalledProcessError:
        print("✗ Model test failed")
        return False


def print_next_steps():
    """Print next steps for user."""
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    
    print("\n1. Test FYN-X interactively:")
    print("   python FYNX_run.py")
    
    print("\n2. Test name recognition:")
    print("   You: Hi, I'm [your name]")
    print("   FYN-X should detect your name automatically")
    
    print("\n3. Test context continuity:")
    print("   Have a conversation and ensure FYN-X remembers context")
    
    print("\n4. Monitor GPU usage:")
    print("   Open Task Manager → Performance → GPU")
    print("   GPU usage should spike when FYN-X responds")
    
    print("\n5. Check performance benchmarks:")
    print("   During conversation, type: benchmark")
    print("   Look for 'ollama_inference' time (should be <5s with GPU)")
    
    print("\n6. Optional: Install local TTS for testing:")
    print("   pip install edge-tts --break-system-packages")
    print("   python src/tts.py")
    
    print("\nFor troubleshooting, see: GPU_OPTIMIZATION.md")
    print("For bug fix details, see: BUG_FIXES.md")
    print()


def main():
    """Main rebuild process."""
    print("\n" + "="*70)
    print(" "*20 + "FYN-X MODEL REBUILD")
    print("="*70)
    print("\nThis script will:")
    print("  1. Check Ollama installation")
    print("  2. Check GPU availability")
    print("  3. Rebuild FYN-X model with bug fixes")
    print("  4. Verify the model was created")
    print("  5. Run a quick test")
    print()
    
    # Check Ollama
    if not check_ollama():
        sys.exit(1)
    
    # Check GPU
    gpu_type = check_gpu()
    
    # Rebuild model
    if not rebuild_model():
        print("\n✗ Model rebuild failed")
        print("Check the error messages above")
        sys.exit(1)
    
    # Verify model
    if not verify_model():
        print("\n✗ Model verification failed")
        sys.exit(1)
    
    # Test model
    print("\nModel created successfully! Running quick test...")
    if not test_model():
        print("\n⚠ Model test had issues (see above)")
        print("You can still try running: python FYNX_run.py")
    
    # Success!
    print("\n" + "="*70)
    print("✓ MODEL REBUILD COMPLETE!")
    print("="*70)
    
    if gpu_type == "NVIDIA":
        print("\n✓ NVIDIA GPU detected - should be fast!")
    elif gpu_type == "AMD":
        print("\n✓ AMD GPU detected - should be fast!")
    elif gpu_type == "Apple":
        print("\n✓ Apple Metal detected - should be fast!")
    else:
        print("\n⚠ Running on CPU - responses will be slower")
        print("  Consider using a smaller model: ollama pull llama3.2")
    
    print_next_steps()


if __name__ == "__main__":
    main()
