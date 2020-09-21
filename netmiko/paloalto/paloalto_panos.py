import time
import re
from netmiko.base_connection import BaseConnection


class PaloAltoPanosBase(BaseConnection):
    """
    Implement methods for interacting with PaloAlto devices.

    Disables `enable()` and `check_enable_mode()`
    methods.  Overrides several methods for PaloAlto-specific compatibility.
    """

    def session_preparation(self):
        """
        Prepare the session after the connection has been established.

        Disable paging (the '--more--' prompts).
        Set the base prompt for interaction ('>').
        """
        self._test_channel_read()
        self.set_base_prompt(delay_factor=20)
        self.disable_paging(command="set cli pager off")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on PaloAlto."""
        pass

    def enable(self, *args, **kwargs):
        """No enable mode on PaloAlto."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on PaloAlto."""
        pass

    def check_config_mode(self, check_string="]"):
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(check_string=check_string)

    def config_mode(self, config_command="configure"):
        """Enter configuration mode."""
        return super().config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config="exit", pattern=r">"):
        """Exit configuration mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def commit(
        self,
        comment=None,
        force=False,
        partial=False,
        device_and_network=False,
        policy_and_objects=False,
        vsys="",
        no_vsys=False,
        delay_factor=0.1,
    ):
        """
        Commit the candidate configuration.

        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.

        Automatically enters configuration mode

        default:
            command_string = commit
        (device_and_network or policy_and_objects or vsys or
                no_vsys) and not partial:
            Exception
        """
        delay_factor = self.select_delay_factor(delay_factor)

        if (
            device_and_network or policy_and_objects or vsys or no_vsys
        ) and not partial:
            raise ValueError(
                "'partial' must be True when using "
                "device_and_network or policy_and_objects "
                "or vsys or no_vsys."
            )

        # Select proper command string based on arguments provided
        command_string = "commit"
        commit_marker = "configuration committed successfully"
        if comment:
            command_string += f' description "{comment}"'
        if force:
            command_string += " force"
        if partial:
            command_string += " partial"
            if vsys:
                command_string += f" {vsys}"
            if device_and_network:
                command_string += " device-and-network"
            if policy_and_objects:
                command_string += " device-and-network"
            if no_vsys:
                command_string += " no-vsys"
            command_string += " excluded"

        # Enter config mode (if necessary)
        output = self.config_mode()
        output += self.send_command_expect(
            command_string,
            strip_prompt=False,
            strip_command=False,
            expect_string="100%",
            delay_factor=delay_factor,
        )

        if commit_marker not in output.lower():
            raise ValueError(f"Commit failed with the following errors:\n\n{output}")
        return output

    def strip_command(self, command_string, output):
        """Strip command_string from output string."""
        output_list = output.split(command_string)
        return self.RESPONSE_RETURN.join(output_list)

    def strip_prompt(self, a_string):
        """Strip the trailing router prompt from the output."""
        response_list = a_string.split(self.RESPONSE_RETURN)
        new_response_list = []
        for line in response_list:
            if self.base_prompt not in line:
                new_response_list.append(line)

        output = self.RESPONSE_RETURN.join(new_response_list)
        return self.strip_context_items(output)

    def strip_context_items(self, a_string):
        """Strip PaloAlto-specific output.

        PaloAlto will also put a configuration context:
        [edit]

        This method removes those lines.
        """
        strings_to_strip = [r"\[edit.*\]"]

        response_list = a_string.split(self.RESPONSE_RETURN)
        last_line = response_list[-1]

        for pattern in strings_to_strip:
            if re.search(pattern, last_line):
                return self.RESPONSE_RETURN.join(response_list[:-1])

        return a_string

    def send_command_expect(self, *args, **kwargs):
        """Palo Alto requires an extra delay"""
        return self.send_command(*args, **kwargs)

    def send_command(self, *args, **kwargs):
        """Palo Alto requires an extra delay"""
        kwargs["delay_factor"] = kwargs.get("delay_factor", 2.5)
        return super().send_command(*args, **kwargs)

    def cleanup(self, command="exit"):
        """Gracefully exit the SSH session."""
        try:
            # The pattern="" forces use of send_command_timing
            if self.check_config_mode(pattern=""):
                self.exit_config_mode()
        except Exception:
            pass
        # Always try to send final 'exit' (command)
        self._session_log_fin = True
        self.write_channel(command + self.RETURN)


class PaloAltoPanosSSH(PaloAltoPanosBase):
    pass


class PaloAltoPanosTelnet(PaloAltoPanosBase):
    pass
