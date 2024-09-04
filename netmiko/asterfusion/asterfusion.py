"""
AsterNOS platforms running Enterprise SONiC Distribution by AsterFusion Co.
"""

from netmiko import log
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.no_enable import NoEnable

import threading
import time


class AsterfusionBase(NoEnable, CiscoSSHConnection):
    def __init__(self, cli_mode: str = "klish", **kwargs) -> None:
        self.cli_mode = cli_mode
        super().__init__(**kwargs)
        self.close_thread_alive_check = False
        self.thread_alive()

    def thread_alive(self):
        check_alive_time = 120  # 120s send is_alive chr

        def send_alive():
            time.sleep(check_alive_time)  # wait connection is initialised
            while True:
                if self.close_thread_alive_check:
                    log.info(f"{self} session is close ,exit --  ")
                    break
                alive = self.is_alive()
                log.debug(f"[]check alive {self} {alive}")
                if (not alive) and (self.close_thread_alive_check):  # check 3 times
                    log.info(
                        f"{self} is not alive and close thread alive check , exit --"
                    )
                    break
                time.sleep(check_alive_time)  # alive check time
            return

        th = threading.Thread(target=send_alive, daemon=True)
        th.start()

    def close_alive_thread(self):
        self.close_thread_alive_check = True

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>$#]")
        self.set_base_prompt(alt_prompt_terminator="$")
        if self.cli_mode == "klish":
            self._enter_shell()
            self.disable_paging()
        elif self.cli_mode == "bash":
            self._enter_bash_cli()
        else:
            pass

    def config_mode(
        self,
        config_command: str = "configure terminal",
        pattern: str = r"\#",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def _enter_shell(self) -> str:
        log.debug(f"Host {self.host} {self.cli_mode} Enter sonic-cli shell")
        return self._send_command_str("sonic-cli", expect_string=r"\#")

    def _enter_bash_cli(self) -> str:
        log.debug(f"Host {self.host} {self.cli_mode} Enter bash shell")
        return self._send_command_str("system bash", expect_string=r"\$")

    def _enter_vtysh(self) -> str:
        log.debug(f"Host {self.host} {self.cli_mode} Enter vtysh shell")
        return self._send_command_str("vtysh", expect_string=r"\#")

    def disable_paging(self) -> str:
        return super().disable_paging(command="terminal raw-output")

    def write_config(self) -> str:
        return super().save_config(cmd="write", confirm=True, confirm_response="y")


class AsterfusionSSH(NoEnable, AsterfusionBase):

    def send_command(
        self,
        command_string: str,
        root_pwd: str = None,
        **kwargs,
    ):
        log.debug(
            "Host [{}], run cmd [{}] , find prompt: {} ".format(
                self.host, command_string, self.find_prompt()
            )
        )
        expect_strings = kwargs.pop("expect_string", None)
        try:
            output = super().send_command(
                command_string,
                expect_string=(
                    expect_strings if expect_strings else r"\$|#|password|sudoers"
                ),
                **kwargs,
            )
            if "sudoers" in output:
                raise ValueError("Need to add user to sudo group")
            if "password" in output:
                if root_pwd is None:
                    raise ValueError("Need a root password to execute sudo commands")
                else:
                    output_after_sending_pwd = super().send_command_timing(root_pwd)
                    if "sudoers file" in output_after_sending_pwd:
                        raise ValueError("Need to add user to sudo group")
                    output = super().send_command(
                        command_string,
                        expect_string=expect_strings if expect_strings else r"\$|#",
                    )

            return output
        except Exception as e:
            log.debug(
                f"send_sonic_command got Exception, host:{self.host} , self: {self}"
            )
            return e

    def send_config_set(self, config_commands, **kwargs):
        log.debug(
            "Host [{}], run cmd [{}] , find prompt: {} ".format(
                self.host, config_commands, self.find_prompt()
            )
        )
        output = super().send_config_set(config_commands, **kwargs)
        return output

    def send_config_from_file(self, config_file, raise_errors: bool = True, **kwargs):
        """
        Send configuration commands down the SSH channel from a file.

        The file is processed line-by-line and each command is sent down the
        SSH channel.

        **kwargs are passed to send_config_set method.

        :param config_file: Path to configuration file to be sent to the device

        :param kwargs: params to be sent to send_config_set method
        """
        log.debug(
            "Host [{}] run cmd from file [{}] , find prompt: {} ".format(
                self.host, config_file, self.find_prompt()
            )
        )
        output = super().send_config_from_file(config_file, **kwargs)
        return output
