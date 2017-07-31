#!/bin/sh

cd /home/gituser/netmiko/
echo

VERSION=`cat netmiko/__init__.py | grep version | sed "s/^__version__ = '//"`
VERSION=`echo $VERSION | sed "s/'$//"`
PACKAGE=`echo 'netmiko-'$VERSION'.tar.gz'`
DIR_PACKAGE=`echo './dist/'$PACKAGE`
echo -n "New Version is: "
echo $PACKAGE
while true; do
    read -p "Is this correct? " response
    case $response in
        [Yy]* ) break;;
        [Nn]* ) exit 1;;
    esac
done

pylama
if [ $? -eq 0 ]; then
    echo
    echo "pylama ... [OK]"
    echo
else
    echo
    echo "pylama ... [FAIL]"
    exit 1
fi

echo
python setup.py sdist > /dev/null
if [ $? -eq 0 ]; then
    echo "creating distribution ... [OK]"
    ls -ltr $DIR_PACKAGE
else
    echo "creating distribution ... [FAIL]"
    exit 1
fi

# Check distribution exists
if [ -f $DIR_PACKAGE ]; then
    echo "Distribution exists"
else
    exit 1
fi
sleep 1

echo
echo "Testing in new virtual environment"
if [ -d "/home/gituser/VENV" ]; then
    cd /home/gituser/VENV
    if [ -d "netmiko_packaging" ]; then
        rm -r netmiko_packaging
    fi
fi
if [ -d "netmiko_packaging" ]; then
    echo "Directory exists"
    exit 1
else
    echo "Create virtualenv"
    /usr/local/bin/virtualenv -p /usr/bin/python2.7 --no-site-packages netmiko_packaging
    echo "Source virtualenv"
    source /home/gituser/VENV/netmiko_packaging/bin/activate
    which python
    cd /home/gituser/netmiko
    pip install dist/$PACKAGE
    echo
    echo
    echo "Netmiko Installed Version"
    python -c "import netmiko; print netmiko.__version__"
    TEST_VERSION=`python -c "import netmiko; print netmiko.__version__"`
    echo
fi

if [ "$TEST_VERSION" == "$VERSION" ]; then
    echo "Install distribution package in virtualenv ... [OK]"
else
    echo "Install distribution package in virtualenv ... [FAIL]"
fi

echo
echo
echo "Upload to testpypi.python.org"
while true; do
    read -p "Continue? " response
    case $response in
        [Yy]* ) break;;
        [Nn]* ) exit 1;;
    esac
done
deactivate
source /home/gituser/VENV/py27_netmiko/bin/activate
echo `which python`
cd /home/gituser/netmiko
### FIX: Uncomment
#twine upload -r pypitest $DIR_PACKAGE

echo
echo
echo "Verify uploaded at https://testpypi.python.org"
while true; do
    read -p "Continue? " response
    case $response in
        [Yy]* ) break;;
        [Nn]* ) exit 1;;
    esac
done

echo

### FIX: NEED TO ADD
# twine upload $DIR_PACKAGE


sleep 1
echo
echo "Test clean install from pypi"
if [ -d "/home/gituser/VENV" ]; then
    cd /home/gituser/VENV
    if [ -d "netmiko_packaging" ]; then
        rm -r netmiko_packaging
    fi
fi
sleep 1

if [ -d "netmiko_packaging" ]; then
    echo "Directory exists"
    exit 1
else
    echo "Create virtualenv"
    /usr/local/bin/virtualenv -p /usr/bin/python2.7 --no-site-packages netmiko_packaging
    echo "Source virtualenv"
    deactivate
    source /home/gituser/VENV/netmiko_packaging/bin/activate
    which python
    cd /home/gituser
    pip install netmiko
    echo
    echo
    echo "Netmiko Installed Version (from pypi)"
    python -c "import netmiko; print netmiko.__version__"
    TEST_VERSION=`python -c "import netmiko; print netmiko.__version__"`
    echo
fi
