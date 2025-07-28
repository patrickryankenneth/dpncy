import subprocess
import sys
from pathlib import Path

def run_demo():
    """Interactive demo that shows DPNCY's power"""
    print("""
    🚀 DPNCY Interactive Demo 🚀
    --------------------------
    This will:
    1. Install Flask-Login 0.6.3 normally
    2. Use DPNCY to install 0.4.1
    3. Show version switching in action
    """)
    
    # 1. Force install Flask-Login 0.6.3
    print("\n🔧 STEP 1: Normal pip install (Flask-Login 0.6.3)")
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "--force-reinstall", "flask-login==0.6.3"
    ], check=True)
    
    # 2. Use DPNCY to install 0.4.1
    print("\n✨ STEP 2: DPNCY install (Flask-Login 0.4.1)")
    from dpncy.core import smart_install
    smart_install("flask-login==0.4.1")
    
    # 3. Run test script
    test_script = Path(__file__).parent / "examples" / "testflask.py"
    print(f"\n🔥 DEMO READY! Run:\n  python {test_script}")