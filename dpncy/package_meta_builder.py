#!/usr/bin/env python3
"""
dpncy_metadata_builder.py - v11 - The "Multi-Version Complete" Edition
A fully integrated, self-aware metadata gatherer with complete multi-version
support for robust, side-by-side package management.
"""
import os
import re
import json
import subprocess
import redis
import hashlib
import importlib.metadata
import zlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dpncy.core import ConfigManager

# Configuration and imports
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError: 
    HAS_TQDM = False

def get_python_version():
    """Get current Python version in X.Y format"""
    return f"{sys.version_info.major}.{sys.version_info.minor}"

def get_site_packages_path():
    """Dynamically find the site-packages path"""
    import site
    # Get the first user or system site-packages directory
    site_packages_dirs = site.getsitepackages()
    if hasattr(site, 'getusersitepackages'):
        site_packages_dirs.append(site.getusersitepackages())
    
    # Prefer virtual environment site-packages if available
    if hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix:
        # We're in a virtual environment
        venv_site_packages = Path(sys.prefix) / "lib" / f"python{get_python_version()}" / "site-packages"
        if venv_site_packages.exists():
            return str(venv_site_packages)
    
    # Fall back to first available site-packages
    for sp in site_packages_dirs:
        if Path(sp).exists():
            return sp
    
    # Last resort fallback
    return str(Path(sys.executable).parent.parent / "lib" / f"python{get_python_version()}" / "site-packages")

def get_bin_paths():
    """Get binary paths to index"""
    paths = []
    
    # Add current Python's bin directory
    python_bin_dir = str(Path(sys.executable).parent)
    paths.append(python_bin_dir)
    
    # Add virtual environment bin if available
    if hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix:
        venv_bin = str(Path(sys.prefix) / 'bin')
        if venv_bin not in paths and Path(venv_bin).exists():
            paths.append(venv_bin)
    
    return paths

# Load configuration using ConfigManager
config_manager = ConfigManager()
config = config_manager.config

class DpncyMetadataGatherer:
    def __init__(self, force_refresh: bool = False):
        self.redis_client = None
        self.force_refresh = force_refresh
        self.security_report = {}
        if self.force_refresh: 
            print("🟢 --force flag detected. Caching will be ignored.")
        if not HAS_TQDM: 
            print("⚠️ Install 'tqdm' for a better progress bar.")

    def connect_redis(self) -> bool:
        try:
            self.redis_client = redis.Redis(
                host=config["redis_host"], 
                port=config["redis_port"], 
                decode_responses=True
            )
            self.redis_client.ping()
            print("✅ Connected to Redis successfully.")
            return True
        except Exception as e:
            print(f"❌ Could not connect to Redis: {e}")
            return False

    def discover_all_packages(self) -> List[Tuple[str, str]]:
        packages = {}  # {pkg_name_lower: version_str} for active environment
        isolated_packages_versions = {}  # {pkg_name_lower: set(versions)} for isolated versions
        active_packages = {}  # Track which version is actually active

        # 1. Discover packages from the main site-packages (active environment)
        try:
            for dist in importlib.metadata.distributions():
                pkg_name = dist.metadata['Name'].lower()
                version = dist.metadata['Version']
                packages[pkg_name] = version
                active_packages[pkg_name] = version  # This is the actually active version
        except Exception as e:
            print(f"⚠️ Error discovering packages from importlib.metadata: {e}")

        # 2. Scan .dist-info/egg-info directly in main site-packages
        site_packages = Path(config["site_packages_path"])
        if site_packages.is_dir():
            for item in site_packages.iterdir():
                if item.is_dir() and (item.name.endswith('.dist-info') or item.name.endswith('.egg-info')):
                    parts = item.name.split('-')
                    if len(parts) >= 2:
                        pkg_name = parts[0].lower()
                        pkg_version = parts[1].rstrip('.dist-info').rstrip('.egg-info')
                        if pkg_name not in packages:
                            packages[pkg_name] = pkg_version
                            active_packages[pkg_name] = pkg_version

        # 3. Discover packages from the .dpncy_versions isolation area
        multiversion_base_path = Path(config["multiversion_base"])
        if multiversion_base_path.is_dir():
            for isolated_pkg_dir in multiversion_base_path.iterdir():
                if isolated_pkg_dir.is_dir() and '-' in isolated_pkg_dir.name:
                    parts = isolated_pkg_dir.name.rsplit('-', 1)
                    if len(parts) == 2:
                        pkg_name = parts[0].lower()
                        pkg_version = parts[1]
                        if pkg_name not in isolated_packages_versions:
                            isolated_packages_versions[pkg_name] = set()
                        isolated_packages_versions[pkg_name].add(pkg_version)

        # Store active versions in Redis for later reference
        self._store_active_versions(active_packages)

        # Combine active and isolated versions
        all_unique_package_versions = {}
        for pkg_name, version in packages.items():
            if pkg_name not in all_unique_package_versions:
                all_unique_package_versions[pkg_name] = set()
            all_unique_package_versions[pkg_name].add(version)

        for pkg_name, versions_set in isolated_packages_versions.items():
            if pkg_name not in all_unique_package_versions:
                all_unique_package_versions[pkg_name] = set()
            all_unique_package_versions[pkg_name].update(versions_set)

        # Convert to list of (pkg_name, version) tuples
        result_list = []
        for pkg_name, versions_set in all_unique_package_versions.items():
            for version_str in versions_set:
                result_list.append((pkg_name, version_str))

        print(f"🔍 Discovered {len(all_unique_package_versions)} unique packages with {len(result_list)} total versions.")
        return sorted(result_list, key=lambda x: x[0])

    def _store_active_versions(self, active_packages: Dict[str, str]):
        """Store the active versions in Redis to fix the active version detection issue"""
        if not self.redis_client:
            return
            
        for pkg_name, version in active_packages.items():
            main_key = f"{config['redis_key_prefix']}{pkg_name}"
            try:
                self.redis_client.hset(main_key, "active_version", version)
            except Exception as e:
                print(f"⚠️ Failed to store active version for {pkg_name}: {e}")

    def run(self):
        print("🚀 Starting dpncy Metadata Builder v11 (Multi-Version Complete Edition)...")
        if not self.connect_redis(): 
            return

        packages_to_process = self.discover_all_packages()

        # Perform security scan only on active packages
        print("🛡️ Performing bulk security scan for active packages...")
        active_packages = {}
        try:
            for dist in importlib.metadata.distributions():
                active_packages[dist.metadata['Name'].lower()] = dist.metadata['Version']
        except Exception as e:
            print(f"⚠️ Error preparing packages for security scan: {e}")
        self._run_bulk_security_check(active_packages)
        print(f"✅ Bulk security scan complete. Found {len(self.security_report)} potential issues.")

        package_iterator = tqdm(packages_to_process, desc="Processing packages", unit="pkg") if HAS_TQDM else packages_to_process
        processed_count = 0

        for package_name, version_str in package_iterator:
            if HAS_TQDM: 
                package_iterator.set_postfix_str(f"Current: {package_name} v{version_str}", refresh=True)
            try:
                version_key = f"{config['redis_key_prefix']}{package_name.lower()}:{version_str}"
                previous_data = self.redis_client.hgetall(version_key)
                
                metadata = self._build_comprehensive_metadata(package_name, previous_data, version_str)
                
                current_checksum = self._generate_checksum(metadata)
                if not self.force_refresh and previous_data and previous_data.get('checksum') == current_checksum:
                    continue
                
                metadata['checksum'] = current_checksum
                self._store_in_redis(package_name, version_str, metadata)
                processed_count += 1
                
            except Exception as e:
                if HAS_TQDM: 
                    package_iterator.write(f"    ❌ ERROR processing {package_name} v{version_str}: {e}")

        print(f"\n🎉 Metadata building complete! Updated {processed_count} package(s).")

    def _build_comprehensive_metadata(self, package_name: str, previous_data: Dict, specific_version: str) -> Dict:
        metadata = {
            'name': package_name,
            'Version': specific_version,
            'last_indexed': datetime.now().isoformat()
        }

        # Try to get metadata from active environment first
        dist = self._get_distribution(package_name)
        package_files = self._find_package_files(dist, package_name)

        # If dist is not found or version doesn't match, check .dpncy_versions
        if not dist or (dist and dist.metadata.get('Version') != specific_version):
            version_path = Path(config["multiversion_base"]) / f"{package_name}-{specific_version}"
            if version_path.is_dir():
                dist_info = next((p for p in version_path.glob('*.dist-info') if p.is_dir()), None)
                if dist_info:
                    try:
                        metadata_file = dist_info / 'METADATA'
                        if metadata_file.exists():
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata.update(self._parse_metadata_file(f.read()))
                    except Exception as e:
                        print(f"⚠️ Error parsing metadata from {version_path}: {e}")

        if dist:
            for k, v in dist.metadata.items():
                metadata[k] = v
            metadata['dependencies'] = [str(req) for req in dist.requires] if dist.requires else []

        metadata.update(self._enrich_from_site_packages(package_name, specific_version))

        if self.force_refresh or 'help_text' not in previous_data:
            if package_files.get('binaries'):
                metadata.update(self._get_help_output(package_files['binaries'][0]))
            else:
                metadata['help_text'] = "No executable binary found."
        else:
            metadata['help_text'] = previous_data.get('help_text', "No help text available.")

        metadata['cli_analysis'] = self._analyze_cli(metadata.get('help_text', ''))
        metadata['security'] = self._get_security_info(package_name)
        metadata['health'] = self._perform_health_checks(package_name, package_files)
        
        return metadata

    def _parse_metadata_file(self, metadata_content: str) -> Dict:
        metadata = {}
        current_key = None
        current_value = []
        for line in metadata_content.splitlines():
            if ': ' in line and not line.startswith(' '):
                if current_key:
                    metadata[current_key] = '\n'.join(current_value).strip() if current_value else ''
                current_key, value = line.split(': ', 1)
                current_value = [value]
            elif line.startswith(' ') and current_key:
                current_value.append(line.strip())
        if current_key:
            metadata[current_key] = '\n'.join(current_value).strip() if current_value else ''
        return metadata

    def _store_in_redis(self, package_name: str, version_str: str, metadata: Dict):
        pkg_name_lower = package_name.lower()
        version_key = f"{config['redis_key_prefix']}{pkg_name_lower}:{version_str}"
        data_to_store = metadata.copy()

        for field in ['help_text', 'readme_snippet', 'license_text', 'Description']:
            if field in data_to_store and isinstance(data_to_store[field], str) and len(data_to_store[field]) > 500:
                compressed = zlib.compress(data_to_store[field].encode('utf-8'))
                data_to_store[field] = compressed.hex()
                data_to_store[f"{field}_compressed"] = 'true'

        flattened_data = self._flatten_dict(data_to_store)
        main_key = f"{config['redis_key_prefix']}{pkg_name_lower}"

        with self.redis_client.pipeline() as pipe:
            pipe.delete(version_key)
            pipe.hset(version_key, mapping=flattened_data)
            pipe.hset(main_key, "name", package_name)
            pipe.sadd(f"{main_key}:installed_versions", version_str)
            pipe.sadd(f"{config['redis_key_prefix']}index", pkg_name_lower)
            pipe.execute()

    def _perform_health_checks(self, package_name: str, package_files: Dict) -> Dict:
        health_data = {
            'import_check': self._verify_installation(package_name),
            'binary_checks': {
                Path(bin_path).name: self._check_binary_integrity(bin_path)
                for bin_path in package_files.get('binaries', [])
            }
        }
        oversized = [name for name, check in health_data['binary_checks'].items() if check.get('size', 0) > 10_000_000]
        if oversized:
            health_data['size_warnings'] = oversized
        return health_data

    def _verify_installation(self, package_name: str) -> Dict:
        script = f"import importlib.metadata; print(importlib.metadata.version('{package_name.replace('-', '_')}'))"
        try:
            result = subprocess.run(
                [config["python_executable"], "-c", script], 
                capture_output=True, text=True, check=True, timeout=5
            )
            return {'importable': True, 'version': result.stdout.strip()}
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            return {
                'importable': False, 
                'error': e.stderr.strip() if hasattr(e, 'stderr') else str(e)
            }

    def _check_binary_integrity(self, bin_path: str) -> Dict:
        if not os.path.exists(bin_path):
            return {'exists': False}
        integrity_report = {
            'exists': True,
            'size': os.path.getsize(bin_path),
            'is_elf': False,
            'valid_shebang': self._has_valid_shebang(bin_path)
        }
        try:
            with open(bin_path, 'rb') as f:
                if f.read(4) == b'\x7fELF':
                    integrity_report['is_elf'] = True
        except Exception:
            pass
        return integrity_report

    def _has_valid_shebang(self, path: str) -> bool:
        try:
            with open(path, 'r', errors='ignore') as f:
                return f.readline().startswith('#!')
        except Exception:
            return False

    def _find_package_files(self, dist, package_name: str) -> Dict:
        files = {'binaries': []}
        if dist and dist.files:
            for file_path in dist.files:
                full_path = Path(config["site_packages_path"]).parent / file_path
                if "bin/" in str(file_path) and full_path.exists():
                    files['binaries'].append(str(full_path))
        if not files['binaries']:
            for bin_dir in config["paths_to_index"]:
                potential_binary = Path(bin_dir) / package_name.lower()
                if potential_binary.exists() and os.access(potential_binary, os.X_OK):
                    files['binaries'].append(str(potential_binary))
                    break
        return files

    def _run_bulk_security_check(self, packages: Dict[str, str]):
        reqs_file_path = '/tmp/bulk_safety_reqs.txt'
        try:
            with open(reqs_file_path, 'w') as f:
                for name, version in packages.items():
                    f.write(f"{name}=={version}\n")
            result = subprocess.run([
                config["python_executable"], "-m", "safety", "check",
                "-r", reqs_file_path, "--json"
            ], capture_output=True, text=True, timeout=120)
            if result.stdout:
                self.security_report = json.loads(result.stdout)
        except Exception as e:
            print(f"    ⚠️ Bulk security scan failed: {e}")
        finally:
            if os.path.exists(reqs_file_path):
                os.remove(reqs_file_path)

    def _get_security_info(self, package_name: str) -> Dict:
        vulnerabilities = self.security_report.get(package_name.lower(), [])
        return {
            'audit_status': 'checked_in_bulk',
            'issues_found': len(vulnerabilities),
            'report': vulnerabilities
        }

    def _generate_checksum(self, metadata: Dict) -> str:
        core_data = {
            'Version': metadata.get('Version'),
            'dependencies': metadata.get('dependencies'),
            'help_text': metadata.get('help_text')
        }
        data_string = json.dumps(core_data, sort_keys=True)
        return hashlib.sha256(data_string.encode('utf-8')).hexdigest()

    def _get_help_output(self, executable_path: str) -> Dict:
        if not os.path.exists(executable_path):
            return {"help_text": "Executable not found."}
        for flag in ["--help", "-h"]:
            try:
                result = subprocess.run(
                    [executable_path, flag],
                    capture_output=True, text=True, timeout=3, errors='ignore'
                )
                output = (result.stdout or result.stderr).strip()
                if output and "usage:" in output.lower():
                    return {"help_text": output[:5000]}
            except Exception:
                continue
        return {"help_text": "No valid help output captured."}

    def _analyze_cli(self, help_text: str) -> Dict:
        if not help_text or "No valid help" in help_text:
            return {}
        analysis = {"common_flags": [], "subcommands": []}
        lines = help_text.split('\n')
        command_regex = re.compile(r'^\s*([a-zA-Z0-9_-]+)\s{2,}(.*)')
        in_command_section = False
        for line in lines:
            if re.search(r'^(commands|available commands):', line, re.IGNORECASE):
                in_command_section = True
                continue
            if in_command_section and not line.strip():
                in_command_section = False
                continue
            if in_command_section:
                match = command_regex.match(line)
                if match:
                    command_name = match.group(1).strip()
                    if not command_name.startswith('-'):
                        analysis["subcommands"].append({
                            "name": command_name,
                            "description": match.group(2).strip()
                        })
        if not analysis["subcommands"]:
            analysis["subcommands"] = [
                {"name": cmd, "description": "N/A"}
                for cmd in self._fallback_analyze_cli(lines)
            ]
        analysis["common_flags"] = list(set(re.findall(r'--[a-zA-Z0-9][a-zA-Z0-9-]+', help_text)))
        return analysis

    def _fallback_analyze_cli(self, lines: list) -> list:
        subcommands = []
        in_command_section = False
        for line in lines:
            if re.search(r'commands:', line, re.IGNORECASE):
                in_command_section = True
                continue
            if in_command_section and line.strip():
                match = re.match(r'^\s*([a-zA-Z0-9_-]+)', line)
                if match:
                    subcommands.append(match.group(1))
            elif in_command_section and not line.strip():
                in_command_section = False
        return list(set(subcommands))

    def _get_distribution(self, package_name: str):
        try:
            return importlib.metadata.distribution(package_name)
        except importlib.metadata.PackageNotFoundError:
            return None

    def _enrich_from_site_packages(self, name: str, version: str = None) -> Dict:
        enriched_data = {}
        guesses = set([name, name.lower().replace('-', '_')])
        base_path = Path(config["site_packages_path"])
        
        if version:
            base_path = Path(config["multiversion_base"]) / f"{name}-{version}"
        
        for g in guesses:
            pkg_path = base_path / g
            if pkg_path.is_dir():
                readme_path = next((p for p in pkg_path.glob('[Rr][Ee][Aa][Dd][Mm][Ee].*') if p.is_file()), None)
                if readme_path:
                    enriched_data['readme_snippet'] = readme_path.read_text(encoding='utf-8', errors='ignore')[:500]
                license_path = next((p for p in pkg_path.glob('[Ll][Ii][Cc][Ee][Nn][Ss]*') if p.is_file()), None)
                if license_path:
                    enriched_data['license_text'] = license_path.read_text(encoding='utf-8', errors='ignore')[:500]
                return enriched_data
        return {}

    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, str(v)))
        return dict(items)

if __name__ == "__main__":
    force = '--force' in sys.argv or '-f' in sys.argv
    gatherer = DpncyMetadataGatherer(force_refresh=force)
    gatherer.run()