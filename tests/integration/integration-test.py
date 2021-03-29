from netmiko import ConnectHandler

linux = {
    "device_type": "linux",
    "ip": "127.0.0.1",
    "username": "root",
    "password": "root",
    "port": 2222,
    "verbose": True,
}

connection = ConnectHandler(**linux)
output = connection.send_command("cat /root/data.txt")
connection.disconnect()

expected = "hello netmiko"
assert output == expected, f'expected "{expected}", but got "{output}"'
