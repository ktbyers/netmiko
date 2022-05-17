import functools
from datetime import datetime
import yaml
from scrapli.driver.core import IOSXEDriver
from scrapli.driver.core import NXOSDriver
from scrapli.driver.core import IOSXRDriver
from scrapli.driver.core import EOSDriver
from scrapli.driver.core import JunosDriver


def read_devices():
    f_name = "test_devices.yml"
    with open(f_name) as f:
        return yaml.safe_load(f)

def f_exec_time(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        time_delta = end_time - start_time
        print(f"{str(func)}: Elapsed time: {time_delta}")
        return (time_delta, result)

    return wrapper_decorator


@f_exec_time
def simple_show_cmd(driver, device):
    ScrapliClass = globals()[driver]
    with ScrapliClass(**device) as conn:
        conn.open()
        return conn.send_command("show ip int brief")


if __name__ == "__main__":

    my_devices = read_devices()
    for device_name, device in my_devices.items():
        print("\n")
        driver = device.pop("driver")
        device_type = device.pop("device_type")
        (time_delta, response) = simple_show_cmd(driver, device)

        print()
        print(driver)
        print("-" * 60)
        print(response.result)
        print("-" * 60)
        print()
        print("\n")
