'''
Delay the Travis CI testing for Python versions so that they don't interfere with each other
'''

from __future__ import print_function

import re
import os
import time
import sys

TRAVIS_DELAY = 0


def main():
    '''
    Delay the Travis CI testing for Python versions so that they don't interfere with each other
    '''
    python_version = "{0}.{1}".format(sys.version_info[0], sys.version_info[1])

    if re.search(r"^3.5", python_version):
        total_delay = 0 * TRAVIS_DELAY
        print("Python 3.5 found")
        print("Sleeping for {0} seconds".format(total_delay))
        time.sleep(total_delay)
    elif re.search(r"^3.4", python_version):
        total_delay = 1 * TRAVIS_DELAY
        print("Python 3.4 found")
        print("Sleeping for {0} seconds".format(total_delay))
        time.sleep(total_delay)
    elif re.search(r"^3.3", python_version):
        total_delay = 2 * TRAVIS_DELAY
        print("Python 3.3 found")
        print("Sleeping for {0} seconds".format(total_delay))
        time.sleep(total_delay)
    elif re.search(r"^2.7", python_version):
        total_delay = 3 * TRAVIS_DELAY
        print("Python 2.7 found")
        print("Sleeping for {0} seconds".format(total_delay))
        time.sleep(total_delay)
    elif re.search(r"^2.6", python_version):
        total_delay = 4 * TRAVIS_DELAY
        print("Python 2.6 found")
        print("Sleeping for {0} seconds".format(total_delay))

    # Execute the unit tests
    return_code = os.system("sh travis_test.sh")
    # return_code comes back as 256 on failure and sys.exit is only 8-bit
    if return_code != 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
