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
    
    try:
        # 1. Force install Flask-Login 0.6.3
        print("\n🔧 STEP 1: Normal pip install (Flask-Login 0.6.3)")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "--force-reinstall", "flask-login==0.6.3"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Step 1 failed: {result.stderr}")
            return
        else:
            print("✅ Flask-Login 0.6.3 installed!")
        
        # 2. Use DPNCY to install 0.4.1 
        print("\n✨ STEP 2: DPNCY install (Flask-Login 0.4.1)")
        
        # Import the correct class and method
        from dpncy.core import Dpncy
        
        dpncy = Dpncy()
        result = dpncy.smart_install(["flask-login==0.4.1"])
        
        if result == 0:
            print("✅ DPNCY install successful!")
        else:
            print("❌ DPNCY install failed!")
            return
            
        # 3. Show current status
        print("\n📊 STEP 3: Multi-version status")
        dpncy.show_multiversion_status()
        
        # 4. Run test script if it exists
        test_script = Path(__file__).parent.parent / "examples" / "testflask.py"
        if test_script.exists():
            print(f"\n🔥 DEMO READY! Run:\n   python {test_script}")
        else:
            print(f"\n🔥 DEMO COMPLETE!")
            print("You can now test version switching:")
            print("  1. Import flask_login in Python")
            print("  2. Check flask_login.__version__")
            print("  3. Use dpncy to switch versions")
            
        # 5. Show how to test manually
        print("\n🧪 Manual Test:")
        print("python -c \"import flask_login; print(f'Version: {flask_login.__version__}')\"")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure dpncy is properly installed!")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_demo()