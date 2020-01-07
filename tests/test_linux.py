#!/usr/bin/env python
from netmiko import ConnectHandler


def main():

    try:
        hostname = raw_input("Enter remote host to test: ")
        username = raw_input("Enter remote username: ")
    except NameError:
        hostname = input("Enter remote host to test: ")
        username = input("Enter remote username: ")

    linux_test = {
        "username": username,
        "use_keys": True,
        "ip": hostname,
        "device_type": "ovs_linux",
        "key_file": "/home/{}/.ssh/test_rsa".format(username),
        "verbose": False,
    }

    net_connect = ConnectHandler(**linux_test)
    print()
    print(net_connect.find_prompt())

    # Test enable mode
    print()
    print("***** Testing enable mode *****")
    net_connect.enable()
    if net_connect.check_enable_mode():
        print("Success: in enable mode")
    else:
        print("Fail...")
    print(net_connect.find_prompt())

    net_connect.exit_enable_mode()
    print("Out of enable mode")
    print(net_connect.find_prompt())

    # Test config mode
    print()
    print("***** Testing config mode *****")
    net_connect.config_mode()
    if net_connect.check_config_mode():
        print("Success: in config mode")
    else:
        print("Fail...")
    print(net_connect.find_prompt())

    net_connect.exit_config_mode()
    print("Out of config mode")
    print(net_connect.find_prompt())

    # Test config mode (when already at root prompt)
    print()
    print("***** Testing config mode when already root *****")
    net_connect.enable()
    if net_connect.check_enable_mode():
        print("Success: in enable mode")
    else:
        print("Fail...")
    print(net_connect.find_prompt())
    print("Test config_mode while already at root prompt")
    net_connect.config_mode()
    if net_connect.check_config_mode():
        print("Success: still at root prompt")
    else:
        print("Fail...")
    net_connect.exit_config_mode()
    # Should do nothing
    net_connect.exit_enable_mode()
    print("Out of config/enable mode")
    print(net_connect.find_prompt())

    # Send config commands
    print()
    print("***** Testing send_config_set *****")
    print(net_connect.find_prompt())
    output = net_connect.send_config_set(["ls -al"])
    print(output)
    print()


if __name__ == "__main__":
    main()
