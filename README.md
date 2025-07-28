dpncy — Multi-Version Python Package Manager & Dependency Analyzer
dpncy is a lightweight, intelligent Python package version manager designed to enable simultaneous management of multiple versions of the same package in a single environment. It installs, tracks, and isolates versions to avoid conflicts and maximize compatibility, perfect for complex dev setups or legacy compatibility needs.

Features

Isolate multiple versions of Python packages in one environment
Intelligent import hooks to select package versions at runtime
Detailed package metadata indexing stored in Redis
CLI interface for querying package versions, info, and status
Modular design with pluggable package metadata builder
Lightweight and minimal dependencies


Installation
Install dependencies (if not using pipenv/poetry):
pip install redis packaging tqdm

Install from source:
git clone https://github.com/YOUR_USERNAME/dpncy.git
cd dpncy
python setup.py install

To run the demo (highly recommended to see dpncy’s power):
pip install "dpncy[demo]"
dpncy-demo


Configuration
On first run, dpncy will prompt you to configure paths interactively. Alternatively, edit ~/.config/dpncy/config.json with the following template:
{
  "paths_to_index": ["YOUR_PYTHON_BIN_PATH"],
  "site_packages_path": "YOUR_SITE_PACKAGES_PATH",
  "redis_host": "YOUR_REDIS_HOST",
  "redis_port": 6379,
  "redis_key_prefix": "dpncy:pkg:",
  "python_executable": "YOUR_PYTHON_EXECUTABLE",
  "multiversion_base": "YOUR_SITE_PACKAGES_PATH/.dpncy_versions"
}

Example values:

YOUR_PYTHON_BIN_PATH: /usr/bin or ~/.venv/bin
YOUR_SITE_PACKAGES_PATH: ~/.local/lib/python3.11/site-packages
YOUR_REDIS_HOST: localhost
YOUR_PYTHON_EXECUTABLE: /usr/bin/python3.11


Usage
Use the dpncy CLI to check status and package info:
dpncy status
dpncy info flask
dpncy list
dpncy install click

Run the demo to see version switching in action:
dpncy-demo


Development

The core logic is inside the dpncy Python package.
package_meta_builder.py is the metadata extraction tool — it indexes your environment packages.
examples/testflask.py demonstrates integration with Flask.

Run the metadata builder:
python -m dpncy.package_meta_builder --force


Dependencies

redis
packaging
tqdm (optional, for progress bars)
flask, flask-login (for demo)

Minimal and clean to keep your environment light.

License
[MIT]
See LICENSE for reference.
