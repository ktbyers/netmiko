#!/bin/sh

# Execute the unit tests in Travis CI
RETURN_CODE=0
cd tests 
./test_suite.sh
if [ $? -ne 0 ]; then
    RETURN_CODE=1
fi

exit $RETURN_CODE
