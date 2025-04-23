from netmiko.linux.linux_ssh import LinuxSSH


class CumulusLinuxSSH(LinuxSSH):

    def save_config(
        self,
        cmd: str = "nv config apply",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        # self.enable()
        return self._send_command_str(
            command_string=cmd,
            strip_prompt=False,
            strip_command=False,
            read_timeout=100.0,
        )
