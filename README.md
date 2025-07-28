dpncy - The Intelligent Python Dependency Resolver

![alt text](https://img.shields.io/badge/License-MIT-yellow.svg)

Tired of creating a new virtual environment for every small dependency conflict? dpncy ends Python dependency hell by introducing "selective version bubbles."

It's a revolutionary package manager that allows you to run multiple versions of a library in a single environment. It intelligently isolates only the conflicting packages, while sharing all compatible dependencies. The result is one clean environment, infinite versions, and zero waste.

See It In Action

This is the output of the live interactive demo. Notice how we seamlessly switch from flask-login==0.6.3 to 0.4.1 at runtime, without ever changing the environment.

<details>
  
<summary>🚀 Click to view the full interactive demo output</summary>

Generated code

python /path/to/file/dpncy/examples/testflask.py

=== DPNCY VERSION SWITCHING DEMO ===

🔍 Current environment:
Current flask-login: 0.6.3

📦 Available isolated versions:
🔄 Multi-Version Package System Status

📁 Base directory: /opt/conda/envs/evocoder_env/lib/python3.11/site-packages/.dpncy_versions
🪝 Import hook installed: ✅

📦 Isolated Package Versions (1):
📁 flask-login-0.4.1 (4.7 MB)
🔍 Finding loader class...
Found class with activate_snapshot: DPNCYLoader
✅ Using DPNCYLoader

=== Testing Flask-Login 0.6.3 ===

🌀 dpncy loader: Activating flask-login==0.6.3...
✅ Using system-installed flask-login==0.6.3 (no bubble required)
Active Flask: 3.1.1
Active Flask-Login: 0.6.3
✅ Works!

=== Testing Flask-Login 0.4.1 ===

🌀 dpncy loader: Activating flask-login==0.4.1...
✅ Activated bubble: /opt/conda/envs/evocoder_env/lib/python3.11/site-packages/.dpncy_versions/flask-login-0.4.1
🔗 Processing 2 dependencies...
ℹ️  Using system version for flask (no bubble)
ℹ️  Using system version for werkzeug (no bubble)
Active Flask: 3.1.1
Active Flask-Login: 0.4.1
✅ Works!

💡 Notice how we switched versions without pip!
🎉 This is the power of dpncy - dependency hell solved!

</details>

🧠 Key Features

    Intelligent Conflict Resolution: Automatically detects and isolates only incompatible package versions. No more bloated environments.

    Surgical Version Bubbles: Creates lightweight, isolated environments for conflicting packages while sharing all other compatible libraries from the system.

    Dynamic Import Hook: Seamlessly switches between the system version and an isolated bubble version at runtime.

    User-Friendly CLI: Includes an interactive mode, a guided demo, and straightforward commands for managing your packages.

    Redis-Powered Indexing: Uses Redis for a fast and persistent index of all your package metadata.

🚀 Getting Started: The 1 Minute Demo

The best way to see the power of dpncy is to run the interactive demo.

Prerequisites:

    Python 3.8+

    Git

    A running Redis server (redis-server)

      
# 1. Clone the repository
git clone https://github.com/patrickryankenneth/dpncy.git
cd dpncy

# 2. Install dpncy with its demo dependencies
# The '.' installs the code in the current directory
pip install ".[demo]"

# 3. Run the interactive demo!
# This will guide you through installing conflicting versions and show the magic.
dpncy demo

🛠️ Installation

For general use after you've tried the demo:
Generated bash

      
# Clone the repo
git clone https://github.com/patrickryankenneth/dpncy.git
cd dpncy

# Install using pip
pip install .


On the first run of any dpncy command, it will guide you through an interactive configuration to set up your paths and Redis connection.
⚙️ Usage

dpncy provides a simple command-line interface for managing your multi-version environment.
Generated bash

      
# Show the status of the versioning system and isolated packages
dpncy status

# Get detailed information about a specific package
dpncy info flask

# List all packages known to dpncy
dpncy list

# Use dpncy to install a package with version management
dpncy install "requests==2.20.0"


How It Works

dpncy operates on a simple but powerful principle.

    Snapshot & Analyze: When you dpncy install <package>, it first analyzes your environment.

    Standard Install: It performs a standard pip install.

    Isolate Conflicts: It then analyzes the changes. If a package was downgraded or changed in a conflicting way, dpncy moves the newly installed version into an isolated "bubble" directory and restores the original environment.

    Activate at Runtime: When you import a package, a lightweight import hook checks if a specific version is required. If so, it dynamically adds the package's "bubble" to the Python path, making that version available instantly.

🔧 Configuration

dpncy is designed to be configured interactively on its first run, so you don't need to manually create a configuration file.

For advanced users or automated setups, the configuration is stored in ~/.config/dpncy/config.json.
<details>
<summary>Click to view example config.json</summary>
Generated json

      
{
    "paths_to_index": ["/home/user/.venv/bin"],
    "site_packages_path": "/home/user/.venv/lib/python3.11/site-packages",
    "redis_host": "localhost",
    "redis_port": 6379,
    "redis_key_prefix": "dpncy:pkg:",
    "python_executable": "/home/user/.venv/bin/python",
    "multiversion_base": "/home/user/.venv/lib/python3.11/site-packages/.dpncy_versions"
}

</details>

🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

📄 License

This project is licensed under the MIT License. See the LICENSE file for details.
