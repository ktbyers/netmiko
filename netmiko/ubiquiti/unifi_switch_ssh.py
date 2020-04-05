import time
from netmiko.ubiquiti.edge_ssh import UbiquitiEdgeSSH


class UnifiSwitchSSH(UbiquitiEdgeSSH):
    def session_preparation(self):
        """Prepare the session after the connection has been established.
        When SSHing to a UniFi switch, the session initially starts at a Linux
        shell. Nothing interesting can be done in this environment, however,
        running `telnet localhost` drops the session to a more familiar
        environment."""

        self._test_channel_read()
        self.set_base_prompt()
        self.send_command(
            command_string="telnet localhost", expect_string=r"\(UBNT\) >"
        )
        self.set_base_prompt()
        self.enable()
        self.disable_paging()

        # Clear read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(self, command="terminal length 0"):
        super(UbiquitiEdgeSSH, self).disable_paging(command=command)
