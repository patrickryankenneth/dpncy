#!/usr/-bin/env python3
"""
dpncy CLI
"""
import sys  # <--- THE MISSING LINE
import argparse
from .core import Dpncy, ConfigManager

def create_parser():
    """Creates and configures the argument parser."""
    parser = argparse.ArgumentParser(
        prog='dpncy', 
        description='Multi-version intelligent package installer',
        epilog='Run `dpncy` with no arguments for first-time setup or status.'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    install_parser = subparsers.add_parser('install', help='Install packages (with downgrade protection)')
    install_parser.add_argument('packages', nargs='+', help='Packages to install (e.g., "requests==2.25.1")')
    
    info_parser = subparsers.add_parser('info', help='Show detailed package information')
    info_parser.add_argument('package', help='Package name to inspect')
    info_parser.add_argument('--version', default='active', help='Specific version to inspect')

    list_parser = subparsers.add_parser('list', help='List installed packages')
    list_parser.add_argument('filter', nargs='?', help='Optional filter pattern for package names')
    
    status_parser = subparsers.add_parser('status', help='Show multi-version system status')
    
    demo_parser = subparsers.add_parser('demo', help='Run the interactive, automated demo')

    reset_parser = subparsers.add_parser('reset', help='Reset the dpncy knowledge base in Redis')
    reset_parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')

    return parser

def main():
    """The main entry point for the CLI."""
    
    # Handle the case where 'dpncy' is run with no arguments
    if len(sys.argv) == 1:
        cm = ConfigManager()
        if not cm.config_path.exists():
            # This is the first time the user has ever run the tool
            cm._first_time_setup() # This runs the interactive config
            print("\n" + "="*50)
            print("🚀 Welcome to dpncy! Your setup is complete.")
            print("To see the magic in action, we highly recommend running the demo:")
            print("\n    dpncy demo\n")
            print("="*50)
        else:
            # This is a returning user
            print("👋 Welcome back to dpncy!")
            print("   Run `dpncy status` to see your environment.")
            print("   Run `dpncy demo` for a showcase of features.")
            print("   Run `dpncy --help` for all commands.")
        return 0

    parser = create_parser()
    args = parser.parse_args()
    
    # Create the main Dpncy object only when a command is actually run
    dpncy = Dpncy()
    
    try:
        if args.command == 'install':
            return dpncy.smart_install(args.packages)
        elif args.command == 'info':
            return dpncy.show_package_info(args.package, args.version)
        elif args.command == 'list':
            return dpncy.list_packages(args.filter)
        elif args.command == 'status':
            return dpncy.show_multiversion_status()
        elif args.command == 'demo':
            from dpncy.demo import run_demo
            return run_demo()
        elif args.command == 'reset':
            return dpncy.reset_knowledge_base(force=args.yes)
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n❌ An unexpected top-level error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())