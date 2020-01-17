import re

from netmiko.base_connection import BaseConnection

class EricssonIposSSH(BaseConnection):

    def check_enable_mode(self, check_string="#"):
        """
        Check if in enable mode. Return boolean.
        """
        return super().check_enable_mode(
            check_string=check_string
        )

    def enable(self, cmd="", pattern="ssword", re_flags=re.IGNORECASE):
        """
        Enter enable mode.
        """
        return super().enable(
            cmd=cmd,
            pattern=pattern,
            re_flags=re_flags
        )

    def exit_enable_mode(self, exit_command="disable"):
        """
        Exits enable (privileged exec) mode.
        """
        return super().exit_enable_mode(
            exit_command=exit_command
        )

    
    def check_config_mode(self, check_string=")#", pattern=""):
        """
        Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(
            check_string=check_string,
            pattern=pattern
        )

    def config_mode(self, config_command="configure", pattern=""):
        """
        Enter into configuration mode on remote device.
        """
        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
        return super().config_mode(
            config_command=config_command,
            pattern=pattern
        )

    def exit_config_mode(self, exit_config="end", pattern="#"):
        """
        Exit from configuration mode.
        Ercisson output :
            end                   Commit configuration changes and return to exec mode
        """
        return super().exit_config_mode(
            exit_config=exit_config,
            pattern=pattern
        )


    def commit(
        self,
        confirm=False,
        confirm_delay=None,
        comment="",
        delay_factor=1,
    ):
        """
        Commit the candidate configuration.

        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.

        Automatically enters configuration mode

        """

        delay_factor = self.select_delay_factor(delay_factor)


        if confirm_delay and not confirm:
            raise ValueError(
                "Invalid arguments supplied to commit method both confirm and check"
            )

        command_string = "commit"
        commit_marker = "Transaction committed"
        if confirm:
            if confirm_delay:
                command_string = f"commit confirmed {confirm_delay}"
            else:
                command_string = "commit confirmed"
            commit_marker = "Commit confirmed ,it will be rolled back within"
        
        if comment:
            if '"' in comment:
                raise ValueError("Invalid comment contains double quote")
            comment = f'"{comment}"'
            command_string += f" comment {comment}"
       
        output = self.config_mode()

        output += self.send_command_expect(
            command_string,
            strip_prompt=False,
            strip_command=False,
            delay_factor=delay_factor,
        )
        
        if commit_marker not in output:
            raise ValueError(
                f"Commit failed with the following errors:\n\n{output}"
            )

        return output
