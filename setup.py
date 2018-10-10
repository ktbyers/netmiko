from setuptools import setup
from setuptools import find_packages
import os
import re
import sys


requirements = ["paramiko>=2.4.1", "scp>=0.10.0", "pyyaml", "pyserial", "textfsm"]

# Cryptography library makes this necessary as older versions of PIP (PIP7 and less)
# will not auto_install enum34 from extras_require.
if sys.version_info < (3,):
    requirements.append("enum34")
    requirements.append("ipaddress")

with open("README.md", "r") as fs:
    long_description = fs.read()


def find_version(*file_paths):
    """
    This pattern was modeled on a method from the Python Packaging User Guide:
        https://packaging.python.org/en/latest/single_source_version.html

    We read instead of importing so we don't get import errors if our code
    imports from dependencies listed in install_requires.
    """
    base_module_file = os.path.join(*file_paths)
    with open(base_module_file) as f:
        base_module_data = f.read()
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", base_module_data, re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="netmiko",
    version=find_version("netmiko", "__init__.py"),
    description="Multi-vendor library to simplify Paramiko SSH connections to network devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ktbyers/netmiko",
    author="Kirk Byers",
    author_email="ktbyers@twb-tech.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    packages=find_packages(exclude=("test*",)),
    install_requires=requirements,
    extras_require={"test": ["pytest>=3.2.5"]},
)
