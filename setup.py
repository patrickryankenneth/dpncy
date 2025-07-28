# /home/minds3t/stealth/dpncy/setup.py
from setuptools import setup, find_packages

# Core requirements (always installed)
CORE_REQUIRES = [
'redis>=4.5.1',
'packaging>=23.1'
]

# Demo requirements (only for first-run experience)
DEMO_REQUIRES = [
'flask>=2.0.0',
'flask-login==0.6.3'  # MUST be exact version
]

setup(
name="dpncy",
version="0.13.0",
packages=find_packages(),
install_requires=CORE_REQUIRES,
extras_require={
    'demo': DEMO_REQUIRES,  # pip install "dpncy[demo]"
},
entry_points={
    'console_scripts': [
        'dpncy = dpncy.cli:main',
        'dpncy-demo = dpncy.demo:run_demo'  # New demo command
    ],
},
python_requires='>=3.11',
)
