#!/usr/bin/env python3
"""
dpncy CLI - v2.0 - The "Smart Setup" Edition
This CLI now features a robust, auto-detecting interactive setup
to ensure a perfect configuration from the first run.
"""
import sys
import os
import argparse
import json
import site
from pathlib import Path
from dpncy.core import Dpncy

# --- STEP 1: THE NEW "BRAIN" ---
def _get_sane_defaults() -> dict:
    """
    Programmatically discovers critical paths to create a complete and
    correct default configuration. This is the new "brain" of the setup.
    """
    try:
        # Find the primary site-packages directory
        sp_path_str = [p for p in site.getsitepackages() if 'site-packages' in p][0]
    except IndexError:
        # Create a failsafe path if discovery fails
        sp_path_str = str(Path.home() / ".local/lib/python{}.{}/site-packages".format(*sys.version_info))
        print(f"⚠️ Could not auto-detect site-packages, defaulting to: {sp_path_str}")

    python_executable = sys.executable
    site_packages_path = Path(sp_path_str)
    
    # This dictionary is now COMPLETE and matches what the builder needs.
    defaults = {
        "site_packages_path": str(site_packages_path),
        "redis_host": "localhost",
        "redis_port": 6379,
        "redis_key_prefix": "dpncy:pkg:",
        "python_executable": python_executable,
        "multiversion_base": str(site_packages_path / ".dpncy_versions"),
        "paths_to_index": [str(Path(python_executable).parent)],
        "builder_script_path": str(site_packages_path / "dpncy" / "package_meta_builder.py")
    }
    return defaults

def create_config_dir() -> Path:
    """Create config directory and return path."""
    config_dir = Path.home() / ".config" / "dpncy"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def is_first_run() -> bool:
    """Check if this is the first time running dpncy."""
    config_dir = create_config_dir()
    config_file = config_dir / "config.json"
    return not config_file.exists()

def mark_first_run_complete(config: dict):
    """Save the configuration to mark the first run as complete."""
    config_dir = create_config_dir()
    config_file = config_dir / "config.json"
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"\n✅ Configuration saved to {config_file}")
    except Exception as e:
        print(f"\n❌ Failed to save configuration: {e}")

# --- STEP 2: THE NEW "WIZARD" ---
def interactive_setup():
    """
    A new, intelligent interactive setup that auto-detects paths
    and allows the user to confirm or edit them.
    """
    print("👋 Welcome to dpncy! Let's get you configured.")
    print("   Auto-detecting paths for your environment. Press Enter to accept defaults.")
    
    final_config = _get_sane_defaults()
    user_overrides = {}

    for key, value in final_config.items():
        # Don't ask about list-based keys for now to keep it simple
        if isinstance(value, list):
            user_overrides[key] = value
            continue

        prompt = f"{key.replace('_', ' ').title()} [{value}]: "
        user_input = input(prompt).strip()
        if user_input:
            user_overrides[key] = user_input
        else:
            user_overrides[key] = value
    
    # Ensure port is an integer
    try:
        user_overrides['redis_port'] = int(user_overrides['redis_port'])
    except ValueError:
        print(f"⚠️ Invalid port '{user_overrides['redis_port']}'. Using default 6379.")
        user_overrides['redis_port'] = 6379

    mark_first_run_complete(user_overrides)
    print("\n🚀 dpncy is now configured and ready to use!")
    return True

# --- The rest of your CLI can stay largely the same ---
# (I've cleaned it up slightly for clarity)

def create_parser():
    parser = argparse.ArgumentParser(
        prog='dpncy', 
        description='Multi-version intelligent package installer',
        epilog='Run `dpncy` with no arguments to see status or for first-time setup.'
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
    
    demo_parser = subparsers.add_parser('demo', help='Run the interactive demo')

    reset_parser = subparsers.add_parser('reset', help='Reset the dpncy knowledge base in Redis')
    reset_parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')

    rebuild_parser = subparsers.add_parser('rebuild-kb', help='Full reset and rebuild of the knowledge base')

    return parser

def main():
    # If `dpncy` is run with no arguments, handle it here
    if len(sys.argv) == 1:
        if is_first_run():
            return 0 if interactive_setup() else 1
        else:
            print("👋 Welcome back to dpncy! Run 'dpncy status' or 'dpncy --help'.")
            return 0

    parser = create_parser()
    args = parser.parse_args()
    
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
            # This requires the demo module to be available
            from dpncy.demo import run_demo
            return run_demo()
        elif args.command == 'reset':
            return dpncy.reset_knowledge_base(force=args.yes)
        elif args.command == 'rebuild-kb':
            return dpncy.rebuild_knowledge_base()
        else:
            parser.print_help()
            return 1
            
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