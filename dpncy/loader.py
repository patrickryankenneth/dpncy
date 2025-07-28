import sys
import os
import json
import redis
from pathlib import Path
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from importlib.metadata import version as get_installed_version, PackageNotFoundError
from dpncy.core import ConfigManager

class DPNCYLoader:
    def __init__(self):
        # Load configuration using ConfigManager
        config_manager = ConfigManager()
        self.config = config_manager.config
        
    def system_version_matches(self, pkg_name, requested_version):
        try:
            return get_installed_version(pkg_name) == requested_version
        except PackageNotFoundError:
            return False

    def activate_snapshot(self, package_spec: str, verbose: bool = True):
        """Smart bubble activator that handles version ranges and physical bubbles"""
        try:
            if verbose:
                print(f"\n🌀 dpncy loader: Activating {package_spec}...")

            if '==' not in package_spec:
                raise ValueError(f"Requires 'name==version' format, got: {package_spec}")
            
            pkg_name, version = package_spec.split('==', 1)
            pkg_name = pkg_name.lower().replace('_', '-')

            if self.system_version_matches(pkg_name, version):
                if verbose:
                    print(f"    ✅ Using system-installed {pkg_name}=={version} (no bubble required)")
                return True

            r = redis.Redis(
                host=self.config['redis_host'],
                port=self.config['redis_port'],
                decode_responses=True
            )
            
            version_keys = r.keys(f"dpncy:pkg:{pkg_name}:*")
            available_versions = [k.split(':')[-1] for k in version_keys 
                               if not k.endswith(('installed_versions', '.dist'))]
            
            if not available_versions:
                if verbose:
                    print(f"    ❌ No versions found for {pkg_name} in Redis")
                return False

            selected_version = version if version in available_versions else None
            
            if not selected_version:
                try:
                    req = Requirement(f"{pkg_name}=={version}")
                    for v in sorted(available_versions, key=Version, reverse=True):
                        if req.specifier.contains(v):
                            selected_version = v
                            break
                except Exception as e:
                    if verbose:
                        print(f"    ⚠️  Version parsing error: {e}")

            if not selected_version:
                if verbose:
                    print(f"    ❌ No compatible version found for {pkg_name}=={version}")
                    print(f"    Available: {available_versions}")
                return False

            bubble_path = Path(self.config['multiversion_base']) / f"{pkg_name}-{selected_version}"
            if not bubble_path.exists():
                if verbose:
                    print(f"    ❌ Bubble directory missing: {bubble_path}")
                return False

            if str(bubble_path) not in sys.path:
                sys.path.insert(0, str(bubble_path))
                if verbose:
                    print(f"    ✅ Activated bubble: {bubble_path}")

            pkg_data = r.hgetall(f"dpncy:pkg:{pkg_name}:{selected_version}")
            deps_json = pkg_data.get('dependencies', '[]')
            
            try:
                dependencies = json.loads(deps_json)
            except json.JSONDecodeError:
                dependencies = []

            if dependencies and verbose:
                print(f"    🔗 Processing {len(dependencies)} dependencies...")

            for dep_spec in dependencies:
                try:
                    req = Requirement(dep_spec)
                    dep_pkg = req.name.lower().replace('_', '-')
                    
                    dep_version_keys = r.keys(f"dpncy:pkg:{dep_pkg}:*")
                    dep_versions = [v.split(':')[-1] for v in dep_version_keys 
                                  if not v.endswith(('installed_versions', '.dist'))]
                    
                    best_version = None
                    for v in sorted(dep_versions, key=Version, reverse=True):
                        if req.specifier.contains(v):
                            best_version = v
                            break
                    
                    if best_version:
                        dep_bubble_path = Path(self.config['multiversion_base']) / f"{dep_pkg}-{best_version}"
                        if dep_bubble_path.exists():
                            self.activate_snapshot(f"{dep_pkg}=={best_version}", verbose)
                        elif verbose:
                            print(f"    ℹ️  Using system version for {dep_pkg} (no bubble)")
                    elif verbose:
                        print(f"    ⚠️  No compatible version for {dep_spec}")
                        
                except Exception as e:
                    if verbose:
                        print(f"    ⚠️  Failed to process {dep_spec}: {str(e)}")

            return True

        except Exception as e:
            if verbose:
                print(f"    ❌ Activation failed: {str(e)}")
            return False