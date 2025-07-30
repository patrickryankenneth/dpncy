[![Security Audit](https://github.com/patrickryankenneth/dpncy/actions/workflows/security_audit.yml/badge.svg)](https://github.com/patrickryankenneth/dpncy/actions/workflows/security_audit.yml)
---
# dpncy - The Intelligent Python Dependency Resolver

### One environment. Unlimited packages/versions/dependencies. No duplicates/downgrades ever again. You can safely delete your pipx, uv, conda, Docker, etc. today.

---
<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://github.com/patrickryankenneth/dpncy/actions/workflows/test.yml"><img src="https://github.com/patrickryankenneth/dpncy/actions/workflows/test.yml/badge.svg" alt="Build Status"></a>
  <a href="https://pypi.org/project/dpncy/"><img src="https://img.shields.io/pypi/v/dpncy" alt="PyPI version"></a>
</p>

---

## 🚀 The 1-Minute Demo: See It to Believe It

Words aren't enough. The best way to understand the power of `dpncy` is to see it in action.

![dpncy demo](dpncy-demo.gif)

Tired of creating a new virtual environment for every small dependency conflict? I was too, until now.

## The Unsolvable Problem, Solved.

> "I was trying to install my packages back into a 'safe' strict Conda-forge environment when I saw it: a single, forced downgrade that I couldn't resolve. At that moment, I decided I was going to solve this, no matter what it cost. In one weekend, `dpncy` was born."

For decades, the Python community has accepted a frustrating reality: if you need two versions of the same package, you need two virtual environments. A legacy project needing `tensorflow==1.15` and a new project needing `tensorflow==2.10` could not coexist. We've been stuck in dependency hell.

**dpncy ends dependency hell.**

It is a revolutionary package manager that allows you to run multiple, conflicting packages and dependencies in a single Python environment. `dpncy` intelligently isolates *only* the conflicting package and its historically-correct dependencies, while your entire environment continues to share all other compatible packages.

The result is one clean environment, infinite versions, and zero waste.

The demo will walk you through a classic disaster scenario:
1.  **The Disaster:** Watch `pip` destroy a perfectly good environment by forcing a downgrade for a legacy package.
2.  **The Rescue:** See `dpncy` heroically fix the environment, restoring the modern package.
3.  **The Right Way:** Witness `dpncy` install the old package again, this time safely isolating it in a "bubble."
4.  **The Magic:** The grand finale shows you switching between the modern version and the bubbled version *in the same script*, proving both are available simultaneously.

---

## 🛠️ Easy Install

Get started in under 1 minute.

```bash
# First, install dpncy (after installing Redis)
pip install dpncy

# Then, run the fully automated, story-driven demo
dpncy demo
```

<table>
<tr>
<td width="50%">

## 🌍 Real-World Example
Imagine maintaining a Flask app that needs:
- `flask-login==0.4.1` (legacy)
- `requests==2.28.0` (new)
- `scikit-learn==0.24` (ML)

**Traditional:**  
3 separate environments  
**dpncy:**  
Single environment  

</td>
<td width="50%">

## 🏢 Enterprise Impact
| Metric               | Before dpncy | After dpncy |
|----------------------|--------------|-------------|
| CI/CD Complexity     | 5 envs       | 1 env       |
| Storage Overhead     | 8.7GB        | 4.3GB       |
| Setup Time           | 22 min       | 60 sec      |

</td>
</tr>
</table>

---

## 🧠 Key Features

*   **Intelligent Downgrade Protection:** Automatically detects and prevents `pip` installs that would break your existing environment.
*   **Surgical Version Bubbles:** Creates lightweight, self-contained bubbles for conflicting packages and their *entire* historical dependency trees.
*   **Dynamic Runtime Switching:** A seamless loader allows your scripts to activate a specific bubbled version on-demand, without changing your environment.
*   **Efficient Deduplication:** Bubbles only contain the necessary files. All compatible dependencies are shared with the main environment, saving gigabytes of disk space.
*   **Rich Metadata Knowledge Base:** Powered by Redis, `dpncy` builds a deep understanding of every package in your environment, including its health and security.

---

## 🎯 Why dpncy Changes Everything

## 🏢 Enterprise Scenario
*"Our data science team needed 3 versions of TensorFlow (1.15, 2.4, 2.9) in the same JupyterHub environment,

dpncy made it work with zero conflicts."*

**Before dpncy:**
- Need Django 3.2 for one project, Django 4.0 for another? → Two virtual environments
- Legacy package needs requests==2.20.0 but your app needs 2.28.0? → Dependency hell
- Want to test your code against multiple package versions? → Complex CI/CD setup

**With dpncy:**
- One environment, infinite package versions
- Zero conflicts, zero waste
- Runtime version switching without pip

---

<details>
<summary>🚀 Click to view the full capabilities and rich metadata </summary>

### Command Line Interface

```bash
# See the complete status of your main environment and all bubbles
dpncy status

# Get deep metadata, including all known versions of a package
dpncy info flask-login

# List all packages in your environment with a health check
dpncy list
📋 Found 223 packages:
  🛡️💚 absl-py v2.3.1 - Abseil Python Common Libraries, see https://github.com/ab...
  🛡️💚 absl_py v2.3.1.dist - Abseil Python Common Libraries, see https://github.com/ab...
  🛡️💚 annotated-types v0.7.0 - Reusable constraint types to use with typing.Annotated
  🛡️💚 annotated_types v0.7.0.dist - Reusable constraint types to use with typing.Annotated
  🛡️💚 anyio v4.9.0 - High level compatibility layer for multiple asynchronous ...
  🛡️💚 argon2-cffi v25.1.0 - Argon2 for Python
  🛡️💚 argon2-cffi-bindings v21.2.0 - Low-level CFFI bindings for Argon2
(continues on..............)
```
### The Knowledge Base

`dpncy` gives you unprecedented insight into your environment by storing rich metadata in Redis.

**Check for all known versions of a package:**
```bash
# redis-cli SMEMBERS "dpncy:pkg:flask-login:installed_versions"
1) "0.6.3"  # Active
2) "0.4.1"  # In a bubble
```

**Get deep metadata for a specific bubbled version:**
```bash
# redis-cli HGETALL "dpncy:pkg:flask-login:0.4.1"
1) "Version"
2) "0.4.1"
3) "dependencies"
4) "[\"Flask>=0.9\", \"Werkzeug>=0.11.15\"]"
...and 50+ other fields
```

**Test these commands in your environment after installing an older version to prove your newer one stayed safe!**

python -c "import flask_login; print(f'\033[1;32mACTIVE VERSION:\033[0m {flask_login.__version__}')"

```bash
ACTIVE VERSION: 0.6.3
```
pip show flask-login | grep Version
```bash
Version: 0.6.3
```

</details>

## 🤝 Contributing

This project was born out of a real-world problem, and it thrives on community collaboration. Contributions, bug reports, and feature requests are incredibly welcome. Please feel free to check the issues page to get started.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
