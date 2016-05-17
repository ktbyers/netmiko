from setuptools import setup
import os
import re


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
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              base_module_data, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name='netmiko',
    version=find_version('netmiko', '__init__.py'),
    description='Multi-vendor library to simplify Paramiko SSH connections to network devices',
    url='https://github.com/ktbyers/netmiko',
    author='Kirk Byers',
    author_email='ktbyers@twb-tech.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    packages=['netmiko',
              'netmiko/cisco',
              'netmiko/arista',
              'netmiko/hp',
              'netmiko/f5',
              'netmiko/juniper',
              'netmiko/brocade',
              'netmiko/huawei',
              'netmiko/fortinet',
              'netmiko/a10',
              'netmiko/ovs',
              'netmiko/linux',
              'netmiko/enterasys',
              'netmiko/extreme',
              'netmiko/alcatel',
              'netmiko/dell',
              'netmiko/avaya',
              'netmiko/paloalto',
              'netmiko/quanta'],
    install_requires=['paramiko>=1.13.0', 'scp>=0.10.0', 'pyyaml'],
    extras_require={
        'test': ['pytest>=2.6.0',]
    },
)
