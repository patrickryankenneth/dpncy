# dpncy - The Intelligent Python Dependency Resolver

### One environment - Infinite packages and versions. Zero duplicates, downgrades, or 'could not resolve's.
*The only environment you'll ever need.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Tired of creating a new virtual environment for every small dependency conflict? `dpncy` ends Python dependency hell by introducing **"selective version bubbles."**

It's a revolutionary package manager that allows you to run multiple versions of a library in a single environment. It intelligently isolates *only* the conflicting packages while sharing all compatible dependencies. The result is one clean environment, infinite versions, and zero waste.

---

## See It In Action

This is the output of the live interactive demo. Notice how we seamlessly switch from `flask-login==0.6.3` to `0.4.1` at runtime, without ever changing the environment.

<details>
<summary>🚀 Click to view the full interactive demo output </summary>

## dpncy Demo: Seamless Version Switching

Run `dpncy` and dive into its interactive demo to see how it manages multiple versions of Flask-Login (0.6.3 and 0.4.1) in one environment—without pip reinstalls!

🎉 Welcome to dpncy - Multi-version intelligent package installer!
=================================================================
🔍 Checking system requirements...
✅ Redis connection: OK

🎯 What would you like to do?
1. 🚀 Run interactive demo
2. 📦 Install a package
3. 📊 View system status
4. 📖 Show help
5. ⚙️ Configure settings

Enter your choice (1-5): 1

🎬 Starting interactive demo...
Continue with demo? (y/N): y
📥 Installing demo dependencies...
✅ Demo dependencies installed!

🚀 DPNCY Interactive Demo 🚀
--------------------------
1. Install Flask-Login 0.6.3 normally
2. Use dpncy to install 0.4.1
3. Show version switching in action

🔧 STEP 1: Normal pip install
✅ Flask-Login 0.6.3 installed!

✨ STEP 2: dpncy install
📸 Snapshotting environment...
⚙️ Installing flask-login==0.4.1...
🛡️ Downgrade protection activated!
  - Isolated flask-login v0.4.1 to bubble
  - Restored flask-login v0.6.3 in main environment
✅ Environment restored and conflicts isolated!
🧠 Updating knowledge base...
✅ Knowledge base updated.

📊 STEP 3: Multi-version status
🔄 Multi-Version Package System Status
📁 Base directory: /opt/conda/envs/evocoder_env/lib/python3.11/site-packages/.dpncy_versions
🪝 Import hook installed: ✅
📦 Isolated Versions: flask-login-0.4.1 (4.7 MB)

🔥 DEMO READY! Switching versions...

=== Testing Flask-Login 0.6.3 ===
🌀 Activating flask-login==0.6.3...
Active Flask-Login: 0.6.3
✅ Works!

=== Testing Flask-Login 0.4.1 ===
🌀 Activating flask-login==0.4.1...
✅ Activated bubble: /opt/conda/envs/evocoder_env/lib/python3.11/site-packages/.dpncy_versions/flask-login-0.4.1
Active Flask-Login: 0.4.1
✅ Works!

🎉 dpncy switched versions seamlessly—no pip needed!

</details>

---

## 🎯 Why dpncy Changes Everything

**Before dpncy:**
- Need Django 3.2 for one project, Django 4.0 for another? → Two virtual environments
- Legacy package needs requests==2.20.0 but your app needs 2.28.0? → Dependency hell
- Want to test your code against multiple package versions? → Complex CI/CD setup

**With dpncy:**
- One environment, infinite package versions
- Zero conflicts, zero waste
- Runtime version switching without pip

---

## 🧠 Key Features

- **Intelligent Conflict Resolution:** Automatically detects and isolates only incompatible package versions. No more bloated environments.
- **Surgical Version Bubbles:** Creates lightweight, isolated "bubbles" for conflicting packages while sharing all other compatible libraries.
- **Dynamic Import Hook:** Seamlessly switches between the system version and an isolated bubble version at runtime.
- **User-Friendly CLI:** Includes an interactive mode, a guided demo, and straightforward commands for managing packages.
- **Redis-Powered Indexing:** Uses Redis for a fast and persistent index of all your package metadata.

---

## 🚀 Getting Started: The 1-Minute Demo

The best way to see the power of `dpncy` is to run the interactive demo.

# Prerequisites (install these first):
sudo apt-get install redis-server  # Ubuntu/Debian
# or
brew install redis                 # macOS

# Start Redis
redis-server

# Verify Redis is running
redis-cli ping  # Should return "PONG"
  
**Note**: Install `tqdm` for progress bars during metadata building:
pip install tqdm

```bash
# 1. Clone the repository
git clone https://github.com/patrickryankenneth/dpncy.git
cd dpncy

# 2. Install dpncy with its demo dependencies
# The '.' installs the code in the current directory
pip install ".[demo]"

# 3. Run the interactive demo!
# This will guide you through installing conflicting versions and show the magic.
dpncy demo
```

---


## 🛠️ Installation

For general use after you've tried the demo:

```bash
# Clone the repo
git clone https://github.com/patrickryankenneth/dpncy.git
cd dpncy

# Install using pip
pip install .
```

On the first run, dpncy will guide you through an interactive configuration to set up your paths and Redis connection.

---

## ⚙️ Usage

```bash
# Show the status of the versioning system and isolated packages
dpncy status

# Get detailed information about a specific package
dpncy info flask

# List all packages known to dpncy
dpncy list

# Use dpncy to install a package with version management
dpncy install "requests==2.20.0"
```
--- 
## 🌍 Real-World Example

Imagine you're maintaining a Flask app that needs:
- `flask-login==0.4.1` (legacy authentication system)
- `requests==2.28.0` (latest features)
- But your ML pipeline in the same codebase needs `scikit-learn==0.24` which conflicts with newer requests

**Traditional solution:** 3 different environments, complex deployment
**dpncy solution:** One environment, surgical isolation of only the conflicting versions

---

## How It Works

dpncy operates on a simple but powerful principle:

1. **Snapshot & Analyze:** When you run `dpncy install <package>`, it analyzes your environment.

2. **Standard Install:** Performs a standard pip install.

3. **Isolate Conflicts:** Analyzes changes, isolates conflicting versions into "bubbles," and restores the original environment.

4. **Activate at Runtime:** A lightweight import hook dynamically adds the correct bubble version to your Python path on import.

---

## 🔧 Configuration

dpncy is designed to be configured interactively on its first run, so you don't need to manually create a configuration file.

For advanced users or automated setups, the configuration is stored at:

```text
~/.config/dpncy/config.json
```

<details>
<summary>Example config.json</summary>

```json
{
    "paths_to_index": ["/home/user/.venv/bin"],
    "site_packages_path": "/home/user/.venv/lib/python3.11/site-packages",
    "redis_host": "localhost",
    "redis_port": 6379,
    "redis_key_prefix": "dpncy:pkg:",
    "python_executable": "/home/user/.venv/bin/python",
    "multiversion_base": "/home/user/.venv/lib/python3.11/site-packages/.dpncy_versions"
}
```

</details>

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

---

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

---

```

---
