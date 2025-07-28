import sys
import os
import argparse
import json
from pathlib import Path
from dpncy.core import Dpncy

def create_config_dir():
    """Create config directory and return path"""
    config_dir = Path.home() / ".dpncy"
    config_dir.mkdir(exist_ok=True)
    return config_dir

def is_first_run():
    """Check if this is the first time running dpncy"""
    config_dir = create_config_dir()
    config_file = config_dir / "config.json"
    first_run_marker = config_dir / ".first_run_complete"
    
    return not first_run_marker.exists()

def interactive_setup():
    """Interactive first-time setup wizard"""
    print("🎉 Welcome to dpncy - Multi-version intelligent package installer!")
    print("=" * 65)
    print()
    
    # Check Redis connection
    print("🔍 Checking system requirements...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis connection: OK")
    except Exception as e:
        print("❌ Redis connection: FAILED")
        print("   Please ensure Redis is running on localhost:6379")
        print(f"   Error: {e}")
        return False
    
    print()
    print("🎯 What would you like to do?")
    print()
    print("1. 🚀 Run interactive demo (recommended for first-time users)")
    print("2. 📦 Install a package with version management")
    print("3. 📊 View system status")
    print("4. 📖 Show help and exit")
    print("5. ⚙️  Configure settings")
    print()
    
    while True:
        try:
            choice = input("Enter your choice (1-5): ").strip()
            
            if choice == "1":
                return run_demo_flow()
            elif choice == "2":
                return run_install_flow()
            elif choice == "3":
                return show_status()
            elif choice == "4":
                show_help()
                return True
            elif choice == "5":
                return configure_settings()
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Setup cancelled. Run 'dpncy' again anytime!")
            return False

def run_demo_flow():
    """Handle demo flow"""
    print("\n🎬 Starting interactive demo...")
    print("This will install demo dependencies and show version switching in action.")
    print()
    
    confirm = input("Continue with demo? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        return interactive_setup()
    
    try:
        # Install demo dependencies
        import subprocess
        print("📥 Installing demo dependencies...")
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.[demo]'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Demo dependencies installed!")
            from dpncy.demo import run_demo
            run_demo()
            mark_first_run_complete()
            return True
        else:
            print(f"❌ Failed to install demo dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Demo setup failed: {e}")
        return False

def run_install_flow():
    """Handle package installation flow"""
    print("\n📦 Package Installation Wizard")
    print("Examples: flask==2.0.0, requests>=2.25.0, numpy")
    print()
    
    while True:
        package = input("Enter package name (or 'back' to return): ").strip()
        
        if package.lower() == 'back':
            return interactive_setup()
        
        if not package:
            print("❌ Please enter a package name.")
            continue
            
        try:
            print(f"\n🔄 Installing {package}...")
            dpncy = Dpncy()
            result = dpncy.smart_install([package])
            
            if result == 0:
                print(f"✅ Successfully installed {package}!")
                mark_first_run_complete()
                
                # Ask if they want to install more
                more = input("\nInstall another package? (y/N): ").strip().lower()
                if more in ['y', 'yes']:
                    continue
                else:
                    return True
            else:
                print(f"❌ Installation failed for {package}")
                retry = input("Try again? (y/N): ").strip().lower()
                if retry not in ['y', 'yes']:
                    return interactive_setup()
                    
        except Exception as e:
            print(f"❌ Error installing {package}: {e}")
            return interactive_setup()

def show_status():
    """Show system status"""
    print("\n📊 System Status")
    print("-" * 20)
    
    try:
        dpncy = Dpncy()
        dpncy.show_multiversion_status()
        mark_first_run_complete()
        
        input("\nPress Enter to continue...")
        return interactive_setup()
        
    except Exception as e:
        print(f"❌ Error showing status: {e}")
        return False

def configure_settings():
    """Configure dpncy settings"""
    print("\n⚙️  Configuration")
    print("-" * 15)
    
    config_dir = create_config_dir()
    config_file = config_dir / "config.json"
    
    # Default config
    config = {
        "redis_host": "localhost",
        "redis_port": 6379,
        "auto_backup": True,
        "verbose": False
    }
    
    # Load existing config if it exists
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config.update(json.load(f))
        except:
            pass
    
    print(f"Current Redis host: {config['redis_host']}")
    new_host = input("Enter new Redis host (press Enter to keep current): ").strip()
    if new_host:
        config['redis_host'] = new_host
    
    print(f"Current Redis port: {config['redis_port']}")
    new_port = input("Enter new Redis port (press Enter to keep current): ").strip()
    if new_port:
        try:
            config['redis_port'] = int(new_port)
        except ValueError:
            print("❌ Invalid port number, keeping current.")
    
    # Save config
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print("✅ Configuration saved!")
        mark_first_run_complete()
        
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
    
    input("\nPress Enter to continue...")
    return interactive_setup()

def show_help():
    """Show help information"""
    print("\n📖 dpncy Help")
    print("=" * 15)
    print()
    print("Available commands:")
    print("  dpncy install <package>  - Install package with version management")
    print("  dpncy info <package>     - Show package information")
    print("  dpncy list [filter]      - List installed packages")
    print("  dpncy status            - Show multi-version system status")
    print("  dpncy demo              - Run interactive demo")
    print()
    print("Examples:")
    print("  dpncy install flask==2.0.0")
    print("  dpncy install 'requests>=2.25.0'")
    print("  dpncy info numpy")
    print("  dpncy list flask")
    print()
    print("For more information, visit: https://github.com/YOURREPO/docs")
    print()

def mark_first_run_complete():
    """Mark first run as complete"""
    config_dir = create_config_dir()
    marker_file = config_dir / ".first_run_complete"
    marker_file.touch()

def create_parser():
    parser = argparse.ArgumentParser(prog='dpncy', description='Multi-version intelligent package installer')
    subparsers = parser.add_subparsers(dest='command', required=False, help='Available commands')
    
    install_parser = subparsers.add_parser('install', help='Install packages (with downgrade protection)')
    install_parser.add_argument('packages', nargs='+', help='Packages to install (e.g., "requests==2.25.1")')
    
    info_parser = subparsers.add_parser('info', help='Show detailed package information from the knowledge base')
    info_parser.add_argument('package', help='Package name to inspect')
    
    list_parser = subparsers.add_parser('list', help='List installed packages with multi-version info')
    list_parser.add_argument('filter', nargs='?', help='Optional filter pattern for package names')
    
    status_parser = subparsers.add_parser('status', help='Show multi-version system status')
    
    demo_parser = subparsers.add_parser('demo', help='Run the interactive demo to showcase version switching')
    
    # Add interactive mode
    interactive_parser = subparsers.add_parser('interactive', help='Run interactive mode')
    
    return parser

def main():
    # Check for first run
    if is_first_run() and len(sys.argv) == 1:
        # No command provided and first run - start interactive setup
        success = interactive_setup()
        return 0 if success else 1
    
    # Check if no command provided (but not first run)
    if len(sys.argv) == 1:
        print("👋 Welcome back to dpncy!")
        print()
        print("Quick commands:")
        print("  dpncy install <package>  - Install a package")
        print("  dpncy demo              - Run interactive demo")
        print("  dpncy status            - Show system status")
        print("  dpncy interactive       - Enter interactive mode")
        print("  dpncy --help            - Show all commands")
        print()
        return 0
    
    # Handle direct demo command
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        try:
            from dpncy.demo import run_demo
            run_demo()
            return 0
        except ImportError:
            print("❌ Demo not available. Install demo dependencies with:")
            print("   pip install -e .[demo]")
            return 1
    
    # Handle interactive command
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        success = interactive_setup()
        return 0 if success else 1
    
    # Handle direct install command (legacy support)
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        if len(sys.argv) < 3:
            print("❌ Error: Please specify a package")
            print("   Example: dpncy install flask==2.0.0")
            return 1
        
        try:
            dpncy = Dpncy()
            return dpncy.smart_install(sys.argv[2:])
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            return 1
    
    # Parse arguments normally
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        # This shouldn't happen with required=False, but just in case
        parser.print_help()
        return 0
    
    dpncy = Dpncy()
    
    try:
        if args.command == 'install':
            return dpncy.smart_install(args.packages)
        elif args.command == 'info':
            return dpncy.show_package_info(args.package)
        elif args.command == 'list':
            return dpncy.list_packages(getattr(args, 'filter', None))
        elif args.command == 'status':
            return dpncy.show_multiversion_status()
        elif args.command == 'demo':
            from dpncy.demo import run_demo
            run_demo()
            return 0
        elif args.command == 'interactive':
            success = interactive_setup()
            return 0 if success else 1
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
        return 1
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())