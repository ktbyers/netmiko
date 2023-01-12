from setuptools import setup
from setuptools import find_packages
import os
import re


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
    description="Multi-vendor library to simplify legacy CLI connections to network devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ktbyers/netmiko",
    author="Kirk Byers",
    author_email="ktbyers@twb-tech.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    packages=find_packages(exclude=("test*",)),
    install_requires=[
        "setuptools>=38.4.0",
        "paramiko>=2.7.2",
        "scp>=0.13.3",
        "tenacity",
        "pyyaml>=5.3",
        "textfsm",
        "ntc-templates>=2.0.0",
        "pyserial",
    ],
    entry_points={
        "console_scripts": [
            "netmiko-grep = netmiko.cli_tools.netmiko_grep:main_ep",
            "netmiko-show= netmiko.cli_tools.netmiko_show:main_ep",
            "netmiko-cfg= netmiko.cli_tools.netmiko_cfg:main_ep",
        ]
    },
)
