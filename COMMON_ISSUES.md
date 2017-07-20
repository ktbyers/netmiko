### Show commands that prompt for more information

In these cases, I generally use the send_command_timing() method (which doesn't look for prompts)


For example, a CLI interaction that looks like this:

```
pynet-rtr1#copy running-config flash:test1.txt
Destination filename [test1.txt]? 
5587 bytes copied in 1.316 secs (4245 bytes/sec)

pynet-rtr1#
```

```python
cmd1 = "copy running-config flash:test1.txt
output = net_connect.send_command_timing(cmd1)
if 'Destination filename' in output:
    output += net_connect.send_command_timing("\n")
print(output)
```
