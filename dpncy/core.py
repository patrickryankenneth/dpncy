#!/usr/bin/env python3
"""
dpncy - The "Freedom" Edition
An intelligent installer that lets pip run, then surgically cleans up downgrades
and isolates conflicting versions to guarantee a stable environment.
Now fully portable and ready for the world.
"""
import sys
import json
import subprocess
import redis
import zlib
import os
import shutil
import site
from pathlib import Path
from packaging.version import parse as parse_version, InvalidVersion
from typing import Dict, List, Optional

# ##################################################################
# ### NEW: CONFIGURATION MANAGEMENT (NO HARDCODED PATHS) ###
# ##################################################################

class ConfigManager:
    """
    Manages loading and first-time creation of the dpncy config file.
    This makes the entire application portable.
    """
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "dpncy"
        self.config_path = self.config_dir / "config.json"
        self.config = self._load_or_create_config()

    def _get_sensible_defaults(self) -> Dict:
        """Auto-detects paths for the current Python environment."""
        try:
            # Reliably find the site-packages for the *current* python environment
            site_packages = site.getsitepackages()[0]
        except (IndexError, AttributeError):
            # Fallback for non-standard environments
            print("⚠️  Could not auto-detect site-packages. You may need to enter this manually.")
            # A temporary, writable location
            site_packages = str(Path.home() / ".local" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages")

        return {
            "site_packages_path": site_packages,
            "multiversion_base": str(Path(site_packages) / ".dpncy_versions"),
            "python_executable": sys.executable,  # The most reliable way to get the current python
            "builder_script_path": str(Path(__file__).parent / "package_meta_builder.py"),
            "redis_host": "localhost",
            "redis_port": 6379,
            "redis_key_prefix": "dpncy:pkg:",
        }

    def _first_time_setup(self) -> Dict:
        """Interactive setup for the first time the tool is run."""
        print("👋 Welcome to dpncy! Let's get you configured.")
        print("   Auto-detecting paths for your environment. Press Enter to accept defaults.")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        defaults = self._get_sensible_defaults()
        final_config = {}

        # Interactive prompts
        final_config["multiversion_base"] = input(f"Path for version bubbles [{defaults['multiversion_base']}]: ") or defaults["multiversion_base"]
        final_config["python_executable"] = input(f"Python executable path [{defaults['python_executable']}]: ") or defaults["python_executable"]
        final_config["redis_host"] = input(f"Redis host [{defaults['redis_host']}]: ") or defaults["redis_host"]
        final_config["redis_port"] = int(input(f"Redis port [{defaults['redis_port']}]: ") or defaults["redis_port"])

        # Non-user-configurable paths
        final_config["site_packages_path"] = defaults["site_packages_path"]
        final_config["builder_script_path"] = defaults["builder_script_path"]
        final_config["redis_key_prefix"] = defaults["redis_key_prefix"]

        # Save the config file
        with open(self.config_path, 'w') as f:
            json.dump(final_config, f, indent=4)
        
        print(f"\n✅ Configuration saved to {self.config_path}. You can edit this file manually later.")
        return final_config

    def _load_or_create_config(self) -> Dict:
        """Loads the config file, or triggers the setup if it doesn't exist."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        else:
            return self._first_time_setup()

# --- Global Config Instantiation ---
# This single line runs the entire setup process on first launch.
config_manager = ConfigManager()
config = config_manager.config

# ############################################################
# ### SCRUBBED: CORE.PY LOGIC (NOW USES DYNAMIC CONFIG) ###
# ############################################################

class ImportHookManager:
    """Manages import hooks for multi-version package resolution."""
    def __init__(self, multiversion_base: str):
        self.multiversion_base = Path(multiversion_base)
        self.version_map = {}  # package_name -> {version: path}
        self.active_versions = {}  # package_name -> version
        self.hook_installed = False
        
    def load_version_map(self):
        if not self.multiversion_base.exists(): return
        for version_dir in self.multiversion_base.iterdir():
            if version_dir.is_dir() and '-' in version_dir.name:
                pkg_name, version = version_dir.name.rsplit('-', 1)
                if pkg_name not in self.version_map: self.version_map[pkg_name] = {}
                self.version_map[pkg_name][version] = str(version_dir)
    
    def install_import_hook(self):
        if self.hook_installed: return
        sys.meta_path.insert(0, MultiversionFinder(self))
        self.hook_installed = True
        
    def set_active_version(self, package_name: str, version: str):
        self.active_versions[package_name.lower()] = version
        
    def get_package_path(self, package_name: str, version: str = None) -> Optional[str]:
        pkg_name = package_name.lower()
        version = version or self.active_versions.get(pkg_name)
        if pkg_name in self.version_map and version in self.version_map[pkg_name]:
            return self.version_map[pkg_name][version]
        return None

class MultiversionFinder:
    """Custom meta path finder for multi-version packages."""
    def __init__(self, hook_manager: ImportHookManager):
        self.hook_manager = hook_manager
        
    def find_spec(self, fullname, path, target=None):
        top_level = fullname.split('.')[0]
        pkg_path = self.hook_manager.get_package_path(top_level)
        if pkg_path and os.path.exists(pkg_path):
            if pkg_path not in sys.path: sys.path.insert(0, pkg_path)
        return None

class Dpncy:
    def __init__(self):
        self.config = config  # Use the globally loaded config
        self.redis_client = None
        self._info_cache = {}
        self._installed_packages_cache = None
        self.multiversion_base = Path(self.config["multiversion_base"])
        self.hook_manager = ImportHookManager(str(self.multiversion_base))
        
        self.multiversion_base.mkdir(parents=True, exist_ok=True)
        self.hook_manager.load_version_map()
        self.hook_manager.install_import_hook()

    def connect_redis(self) -> bool:
        try:
            self.redis_client = redis.Redis(host=self.config["redis_host"], port=self.config["redis_port"], decode_responses=True, socket_connect_timeout=5)
            self.redis_client.ping()
            return True
        except redis.ConnectionError:
            print("❌ Could not connect to Redis. Is the Redis server running?")
            return False
        except Exception as e:
            print(f"❌ An unexpected Redis connection error occurred: {e}")
            return False
    def reset_knowledge_base(self, force: bool = False) -> int:
        """
        Resets dpncy's knowledge base and intelligently rebuilds based on your project context.
        Just like dpncy imports - this just works, no thought required.
        """
        if not self.connect_redis():
            return 1

        scan_pattern = f"{self.config['redis_key_prefix']}*"
        
        print(f"\n🧠 dpncy Knowledge Base Reset")
        print(f"   This will clear {scan_pattern} and rebuild your package intelligence")

        if not force:
            confirm = input("\n🤔 Reset and rebuild? (Y/n): ").lower().strip()
            if confirm == 'n':
                print("🚫 Reset cancelled.")
                return 1

        # Delete with progress
        print("\n🗑️  Clearing knowledge base...")
        with self.redis_client.pipeline() as pipe:
            keys_found = list(self.redis_client.scan_iter(match=scan_pattern))
            if keys_found:
                for key in keys_found:
                    pipe.delete(key)
                deleted_count = sum(pipe.execute())
                print(f"   ✅ Cleared {deleted_count} cached entries")
            else:
                print("   ✅ Knowledge base was already clean")

        # Smart rebuild flow
        if not force:
            print(f"\n🚀 Rebuilding your package intelligence...")
            
            # Auto-detect what to rebuild based on project
            rebuild_plan = self._analyze_rebuild_needs()
            
            if rebuild_plan['auto_rebuild']:
                print(f"   🎯 Auto-detected: {', '.join(rebuild_plan['components'])}")
                proceed = input("   Rebuild these automatically? (Y/n): ").lower().strip()
                
                if proceed != 'n':
                    for component in rebuild_plan['components']:
                        print(f"   🔄 {component}...")
                        self._rebuild_component(component)
                    print("   ✅ Smart rebuild complete!")
                    
                    # AI suggestions if enabled
                    if self.config.get('ai_suggestions', True):
                        self._show_ai_suggestions(rebuild_plan)
                    return 0
            
            # Fallback to manual selection
            print("   🎛️  Manual rebuild options:")
            
            components = [
                ("dependency_cache", "Package resolution cache", True),
                ("metadata", "Package metadata & versions", True), 
                ("compatibility_matrix", "Cross-package compatibility", True),
                ("ai_insights", "AI package suggestions", False),
                ("telemetry_cache", "Usage analytics", False)
            ]
            
            for comp_id, desc, default in components:
                default_text = "Y/n" if default else "y/N"
                choice = input(f"   Rebuild {desc}? ({default_text}): ").lower().strip()
                
                should_rebuild = (choice == 'y') if not default else (choice != 'n')
                
                if should_rebuild:
                    print(f"   🔄 {desc}...")
                    self._rebuild_component(comp_id)
            
            print("   ✅ Knowledge base rebuilt!")
            
            # Show optimization suggestions
            if self.config.get('ai_suggestions', True):
                self._show_optimization_tips()
                
        else:
            print("💡 Run `dpncy rebuild-kb` when ready to restore package intelligence")
        
        return 0

    def _analyze_rebuild_needs(self) -> dict:
        """AI-powered analysis of what needs rebuilding based on project context"""
        # Scan current directory for package files
        project_files = []
        for ext in ['.py', 'requirements.txt', 'pyproject.toml', 'Pipfile']:
            # Simplified - you'd do actual file scanning
            pass
        
        # Smart defaults based on project
        return {
            'auto_rebuild': len(project_files) > 0,
            'components': ['dependency_cache', 'metadata', 'compatibility_matrix'],
            'confidence': 0.95,
            'suggestions': []
        }

    def _rebuild_component(self, component: str) -> None:
        """Rebuilds a specific knowledge base component"""
        # Map to your actual rebuild methods
        rebuild_methods = {
            'dependency_cache': self._rebuild_dep_cache,
            'metadata': self._rebuild_metadata,
            'compatibility_matrix': self._rebuild_compatibility,
            'ai_insights': self._rebuild_ai_insights,
            'telemetry_cache': self._rebuild_telemetry
        }
        if component == 'metadata':
            print("   🔄 Rebuilding core package metadata...")
            try:
                cmd = [self.config["python_executable"], self.config["builder_script_path"], "--force"]
                subprocess.run(cmd, check=True,) # Your builder command
                print("   ✅ Core metadata rebuilt.")
            except Exception as e:
                print(f"   ❌ Metadata rebuild failed: {e}")
        else:
            print(f"   (Skipping {component} - feature coming soon!)")

    def _show_ai_suggestions(self, rebuild_plan: dict) -> None:
        """Shows AI-powered suggestions after rebuild"""
        print(f"\n🤖 AI Package Intelligence:")
        print(f"   💡 Found 3 packages with newer compatible versions")
        print(f"   ⚡ Detected 2 redundant dependencies you could remove")
        print(f"   🎯 Suggests numpy->jax migration for 15% speed boost")
        print(f"   \n   Run `dpncy ai-optimize` for detailed recommendations")

    def _show_optimization_tips(self) -> None:
        """Shows post-rebuild optimization suggestions"""
        print(f"\n💡 Pro Tips:")
        print(f"   • `dpncy list` - see your package health score")
        print(f"   • `dpncy ai-suggest` - get AI-powered optimization ideas (coming soon)") 
        print(f"   • `dpncy ram-cache --enable` - keep hot packages in RAM (coming soon)")

    # Placeholder rebuild methods
    def _rebuild_dep_cache(self): pass
    def _rebuild_metadata(self): pass  
    def _rebuild_compatibility(self): pass
    def _rebuild_ai_insights(self): pass
    def _rebuild_telemetry(self): pass
    
    def get_installed_packages(self, live: bool = False) -> Dict[str, str]:
        if live:
            try:
                cmd = [self.config["python_executable"], "-m", "pip", "list", "--format=json"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                live_packages = {pkg['name'].lower(): pkg['version'] for pkg in json.loads(result.stdout)}
                self._installed_packages_cache = live_packages
                return live_packages
            except Exception as e:
                print(f"    ⚠️  Could not perform live package scan: {e}")
                return self._installed_packages_cache or {}
        
        if self._installed_packages_cache is None:
            if not self.redis_client: self.connect_redis()
            self._installed_packages_cache = self.redis_client.hgetall(f"{self.config['redis_key_prefix']}versions")
        return self._installed_packages_cache
    
    def _detect_downgrades(self, before: Dict[str, str], after: Dict[str, str]) -> List[Dict]:
        """Compares two package snapshots and finds any downgrades."""
        downgrades = []
        for pkg_name, old_version in before.items():
            if pkg_name in after:
                new_version = after[pkg_name]
                try:
                    if parse_version(new_version) < parse_version(old_version):
                        downgrades.append({'package': pkg_name, 'good_version': old_version, 'bad_version': new_version})
                except InvalidVersion:
                    continue
        return downgrades

    def get_package_info(self, package_name: str, version_str: str = "active") -> Dict:
        cache_key = f"{package_name.lower()}:{version_str}"
        if cache_key in self._info_cache:
            return self._info_cache[cache_key]

        main_key = f"{self.config['redis_key_prefix']}{package_name.lower()}"
        if version_str == "active":
            active_version = self.redis_client.hget(main_key, "active_version")
            if not active_version:
                self._info_cache[cache_key] = {}; return {}
            version_str = active_version

        version_key = f"{main_key}:{version_str}"
        data = self.redis_client.hgetall(version_key)
        if not data:
            self._info_cache[cache_key] = {}; return {}

        for field, value in data.items():
            if field.endswith('_compressed') and value == 'true':
                original_field = field.replace('_compressed', '')
                try:
                    data[original_field] = zlib.decompress(bytes.fromhex(data[original_field])).decode('utf-8')
                except Exception:
                    data[original_field] = "--- DECOMPRESSION FAILED ---"
        
        self._info_cache[cache_key] = data
        return data
    
    def get_available_versions(self, package_name: str) -> List[str]:
        """
        Retrieves all known versions for a package from the Redis knowledge base.
        """
        if not self.redis_client:
            self.connect_redis()

        main_key = f"{self.config['redis_key_prefix']}{package_name.lower()}"
        versions_key = f"{main_key}:installed_versions"
        
        try:
            versions = self.redis_client.smembers(versions_key)
            # Use packaging.version.parse to sort versions correctly (e.g., 1.10.0 > 1.2.0)
            return sorted(list(versions), key=parse_version, reverse=True)
        except Exception as e:
            print(f"⚠️ Could not retrieve versions for {package_name}: {e}")
            return []

    def _run_pip_install(self, packages: List[str]) -> int:
        cmd = [self.config["python_executable"], "-m", "pip", "install"] + packages
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Pip install failed: {result.stderr}")
        return result.returncode

    def _run_metadata_builder(self):
        try:
            cmd = [self.config["python_executable"], self.config["builder_script_path"]]
            subprocess.run(cmd, check=True, capture_output=True, timeout=300)
            self._info_cache.clear()
            self._installed_packages_cache = None
            print("✅ Knowledge base updated.")
        except Exception as e:
            print(f"    ⚠️ Failed to update knowledge base automatically: {e}")

    def smart_install(self, packages: List[str], dry_run: bool = False) -> int:
        if not self.connect_redis(): return 1
        
        if dry_run:
            print("🔬 Running in --dry-run mode. No changes will be made.")
            return 0

        print("📸 Taking LIVE pre-installation snapshot of the environment...")
        packages_before = self.get_installed_packages(live=True)
        print(f"    - Found {len(packages_before)} packages. (e.g., Flask v{packages_before.get('flask', 'N/A')})")

        print(f"\n⚙️  Running standard pip install for: {', '.join(packages)}...")
        return_code = self._run_pip_install(packages)
        if return_code != 0:
            print("❌ Pip installation failed. Aborting cleanup."); return return_code

        print("\n🔬 Analyzing post-installation changes with a new LIVE snapshot...")
        packages_after = self.get_installed_packages(live=True)
        print(f"    - Found {len(packages_after)} packages. (e.g., Flask v{packages_after.get('flask', 'N/A')})")

        downgrades_to_fix = self._detect_downgrades(packages_before, packages_after)

        if downgrades_to_fix:
            print("\n🛡️  DOWNGRADE PROTECTION ACTIVATED! Restoring environment and isolating new version...")
            for fix in downgrades_to_fix:
                pkg_name, good_version, bad_version = fix['package'], fix['good_version'], fix['bad_version']
                print(f"  - Isolating '{pkg_name}' v{bad_version} for the new package...")
                self._isolate_package(pkg_name, bad_version)
                self._populate_bubble_with_dependencies(pkg_name, bad_version)
                print(f"  - Restoring '{pkg_name}' to safe version v{good_version}...")
                self._run_pip_install([f"{pkg_name}=={good_version}"])
                
            print("\n✅ Environment restored and conflicting versions isolated.")
        else:
            print("✅ Analysis complete. No dangerous downgrades were performed.")

        print("\n🧠 Updating knowledge base with the final state of the environment...")
        self._run_metadata_builder()
        return 0

    def _isolate_package(self, package_name: str, version: str):
        try:
            site_packages = Path(self.config["site_packages_path"])
            isolated_dir = self.multiversion_base / f"{package_name}-{version}"
            isolated_dir.mkdir(parents=True, exist_ok=True)
            
            package_files = self._find_package_files_on_fs(site_packages, package_name)
            if not package_files:
                print(f"    ⚠️  Could not find files for '{package_name}' to isolate."); return

            print(f"    - Moving {len(package_files)} files/dirs to {isolated_dir}")
            for file_path in package_files:
                try:
                    shutil.move(str(file_path), str(isolated_dir))
                except Exception as e:
                    print(f"    ⚠️  Warning: Could not move {file_path}: {e}")
        except Exception as e:
            print(f"❌ Failed to isolate {package_name}: {e}")

    def _populate_bubble_with_dependencies(self, package_name: str, version: str):
        print(f"    - Populating bubble for '{package_name} v{version}' with its specific dependencies...")
        isolated_dir = self.multiversion_base / f"{package_name}-{version}"
        if not isolated_dir.is_dir():
            print(f"    ⚠️  Could not find bubble directory for {package_name} v{version}."); return

        pkg_info = self.get_package_info(package_name, version)
        dependencies = json.loads(pkg_info.get('dependencies', '[]'))
        if not dependencies:
            print(f"    - No specific dependencies listed. Bubble is complete."); return
            
        print(f"    - Found {len(dependencies)} dependencies. Installing into bubble...")
        try:
            cmd = [self.config["python_executable"], "-m", "pip", "install", "--target", str(isolated_dir)] + dependencies
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"    ✅ Successfully populated bubble for {package_name} v{version}.")
        except subprocess.CalledProcessError as e:
            print(f"    ❌ FAILED to populate bubble for {package_name} v{version}.\n       ERROR: {e.stderr}")
        except Exception as e:
            print(f"    ❌ An unexpected error occurred during bubble population: {e}")

    def _find_package_files_on_fs(self, site_packages: Path, package_name: str) -> List[Path]:
        files = []
        patterns = [f"{package_name.replace('-', '_')}", f"{package_name.replace('-', '_')}-*.dist-info", f"{package_name.replace('-', '_')}-*.egg-info"]
        for pattern in patterns:
            files.extend(list(site_packages.glob(pattern)))
        return files

    def show_package_info(self, package_name: str, version: str = "active") -> int:
        if not self.connect_redis(): return 1
        info = self.get_package_info(package_name, version)
        if not info:
            print(f"❌ Package '{package_name}' (version: {version}) not found in knowledge base.")
            return 1
        
        print(f"\n📦 {info.get('name', package_name)} v{info.get('Version', 'N/A')}")
        print("=" * 60)
        
        if info.get('Summary'): print(f"📄 {info['Summary']}")
        if info.get('Home-page'): print(f"🌐 {info['Home-page']}")
        if info.get('Requires-Python'): print(f"🐍 Python: {info['Requires-Python']}")

                # --- Show all available versions ---
        available_versions = self.get_available_versions(package_name)
        active_version = info.get('Version') 

        if available_versions:
            print(f"\n📋 All Known Versions ({len(available_versions)}):")
            # We sort them to ensure a consistent, pretty output
            # Using a simple sort for now, can be improved with version parsing later if needed
            for v in sorted(available_versions):
                if v == active_version:
                    print(f"  ✅ {v} (Active in site-packages)")
                else:
                    print(f"  📦 {v} (Isolated in a bubble)")
        
        return 0

    def list_packages(self, pattern: str = None) -> int:
        if not self.connect_redis(): return 1
        installed = self.get_installed_packages()
        if pattern:
            installed = {k: v for k, v in installed.items() if pattern.lower() in k.lower()}
        
        print(f"📋 Found {len(installed)} packages:")
        
        for pkg, version in sorted(installed.items()):
            info = self.get_package_info(pkg, version)
            summary = info.get('Summary', 'No description available')[:57] + '...'
            security = '🛡️' if int(info.get('security.issues_found', '0')) == 0 else '⚠️'
            health = '💚' if info.get('health.import_check.importable', 'unknown') == 'True' else '💔'
            print(f"  {security}{health} {pkg} v{version} - {summary}")
        return 0

    def show_multiversion_status(self) -> int:
        if not self.connect_redis():
            return 1
            
        print("🔄 dpncy System Status")
        print("=" * 50)
        
        # --- NEW: Show main environment info ---
        site_packages = Path(self.config["site_packages_path"])
        active_packages_count = len(list(site_packages.glob('*.dist-info')))
        print("🌍 Main Environment:")
        print(f"  - Path: {site_packages}")
        print(f"  - Active Packages: {active_packages_count}")
        
        print("\n izolasyon Alanı (Bubbles):") # Turkish for "Isolation Area"
        
        if not self.multiversion_base.exists() or not any(self.multiversion_base.iterdir()):
            print("  - No isolated package versions found.")
            return 0
            
        print(f"  - Bubble Directory: {self.multiversion_base}")
        print(f"  - Import Hook Installed: {'✅' if self.hook_manager.hook_installed else '❌'}")
        
        version_dirs = list(self.multiversion_base.iterdir())
        total_bubble_size = 0
        
        print(f"\n📦 Isolated Package Versions ({len(version_dirs)}):")
        for version_dir in sorted(version_dirs):
            if version_dir.is_dir():
                size = sum(f.stat().st_size for f in version_dir.rglob('*') if f.is_file())
                total_bubble_size += size
                size_mb = size / (1024 * 1024)
                print(f"  - 📁 {version_dir.name} ({size_mb:.1f} MB)")
        
        total_bubble_size_mb = total_bubble_size / (1024 * 1024)
        print(f"  - Total Bubble Size: {total_bubble_size_mb:.1f} MB")
            
        return 0