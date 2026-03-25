from netmiko.ssh_dispatcher import CLASS_MAPPER_BASE;
device_types = set(CLASS_MAPPER_BASE.keys());
print('Is \"dptech\" registered?', 'dptech' in device_types);
assert 'dptech' in device_types, ' dptech NOT found in CLASS_MAPPER_BASE';
print('Test PASSED: dptech is registered!')
