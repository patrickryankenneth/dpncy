#!/usr/bin/env python3

from setuptools import setup, find_packages
from pathlib import Path

# Load README.md for long_description
README = Path(__file__).parent / "README.md"
long_description = README.read_text(encoding="utf-8")

setup(
    name="dpncy",
    version="1.0.01",
    author="Patrick Ryan",
    author_email="patrickryankenneth@gmail.com",  # Optional: replace or omit
    description="The Intelligent Python Dependency Resolver",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/patrickryankenneth/dpncy",  # Make sure this is correct
    packages=find_packages(exclude=["tests*", "examples*"]),
    include_package_data=True,
    install_requires=[
        "redis",
        "packaging",
        "zstandard",
        "psycopg2-binary",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "dpncy=dpncy.cli:main"
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
    ],
    python_requires=">=3.11",
    license="MIT",
)
