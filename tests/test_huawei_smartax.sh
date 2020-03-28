echo "Huawei SmartAX SSH" \
&& date \
&& py.test -v test_netmiko_show.py --test_device huawei_smartax \
&& date \
|| RETURN_CODE=1

exit $RETURN_CODE
