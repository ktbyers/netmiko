import time
from netmiko.vyos.vyos_ssh import VyOSSSH


class UbiquitiEdgeRouterSSH(VyOSSSH):
    """Implement methods for interacting with EdgeOS EdgeRouter network devices."""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.set_terminal_width(command="terminal width 512")
        self.disable_paging(command="terminal length 0")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(self, cmd="save", confirm=False, confirm_response=""):
        """Saves Config."""
        if confirm is True:
            raise ValueError("EdgeRouter does not support save_config confirmation.")
        output = self.send_command(command_string=cmd)
        if "Done" not in output:
            raise ValueError(f"Save failed with following errors:\n\n{output}")
        return output
