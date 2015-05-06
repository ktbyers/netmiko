'''
Delay the Travis CI testing for Python versions so that they don't interfere with each other
'''

from __future__ import print_function

import subprocess
import re
import os
import time

TRAVIS_DELAY = 180


def main():
    '''
    Delay the Travis CI testing for Python versions so that they don't interfere with each other
    '''
    proc = subprocess.Popen(['python', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (std_out, _) = proc.communicate()

    std_out = std_out.decode('utf-8')
    std_out = std_out.strip()

    (_, python_version) = std_out.split()

    if re.search(r"^3.4", python_version):
        print("Python 3.4 found")
        print("Sleeping for {0} seconds".format(TRAVIS_DELAY))
        time.sleep(TRAVIS_DELAY)
        os.system("sh travis_test.sh")
    elif re.search(r"^3.3", python_version):
        print("Python 3.3 found")
    elif re.search(r"^2.7", python_version):
        print("Python 2.7 found")
        print("Sleeping for {0} seconds".format(TRAVIS_DELAY * 0))
        os.system("sh travis_test.sh")
    elif re.search(r"^2.6", python_version):
        print("Python 2.6 found")


if __name__ == "__main__":
    main()
