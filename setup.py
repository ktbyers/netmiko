from distutils.core import setup
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
    url='https://github.com/ktbyers/netmiko',
    download_url='https://github.com/ktbyers/netmiko/archive/v' + find_version('netmiko', '__init__.py') + '.tar.gz',
    license='MIT',
    author='Kirk Byers',
    author_email='ktbyers@twb-tech.com',
    install_requires=['paramiko>=1.13.0', 'scp>=0.10.0'],
    description='Multi-vendor library to simplify Paramiko SSH connections to network devices',
    packages=['netmiko',
              'netmiko/cisco',
              'netmiko/arista',
              'netmiko/hp',
              'netmiko/f5',
              'netmiko/juniper',
              'netmiko/brocade',
              'netmiko/huawei',
              'netmiko/a10',
              'netmiko/avaya'],
    )
