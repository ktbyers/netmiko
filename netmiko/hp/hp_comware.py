import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class HPComwareBase(CiscoSSHConnection):
    def __init__(self, **kwargs):
        # Comware doesn't have a way to set terminal width which breaks cmd_verify
        global_cmd_verify = kwargs.get("global_cmd_verify")
        if global_cmd_verify is None:
            kwargs["global_cmd_verify"] = False
        return super().__init__(**kwargs)

    def session_preparation(self):
        """
        Prepare the session after the connection has been established.
        Extra time to read HP banners.
        """
        delay_factor = self.select_delay_factor(delay_factor=0)
        i = 1
        while i <= 4:
            # Comware can have a banner that prompts you to continue
            # 'Press Y or ENTER to continue, N to exit.'
            time.sleep(0.5 * delay_factor)
            self.write_channel("\n")
            i += 1

        time.sleep(0.3 * delay_factor)
        self.clear_buffer()
        self._test_channel_read(pattern=r"[>\]]")
        self.set_base_prompt()
        command = self.RETURN + "screen-length disable"
        self.disable_paging(command=command)
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def config_mode(self, config_command="system-view"):
        """Enter configuration mode."""
        return super().config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config="return", pattern=r">"):
        """Exit config mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def check_config_mode(self, check_string="]"):
        """Check whether device is in configuration mode. Return a boolean."""
        return super().check_config_mode(check_string=check_string)

    def set_base_prompt(
        self, pri_prompt_terminator=">", alt_prompt_terminator="]", delay_factor=1
    ):
        """
        Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple contexts. For Comware
        this will be the router prompt with < > or [ ] stripped off.

        This will be set on logging in, but not when entering system-view
        """
        prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
        )

        # Strip off leading character
        prompt = prompt[1:]
        prompt = prompt.strip()
        self.base_prompt = prompt
        return self.base_prompt

    def enable(self, cmd="system-view"):
        """enable mode on Comware is system-view."""
        return self.config_mode(config_command=cmd)

    def exit_enable_mode(self, exit_command="return"):
        """enable mode on Comware is system-view."""
        return self.exit_config_mode(exit_config=exit_command)

    def check_enable_mode(self, check_string="]"):
        """enable mode on Comware is system-view."""
        return self.check_config_mode(check_string=check_string)

    def save_config(self, cmd="save force", confirm=False, confirm_response=""):
        """Save Config."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class HPComwareSSH(HPComwareBase):
    def send_config_set(
            self,
            config_commands=None,
            exit_config_mode=True,
            delay_factor=1,
            max_loops=150,
            strip_prompt=False,
            strip_command=False,
            config_mode_command=None,
            cmd_verify=True,
            enter_config_mode=True,
    ):
        delay_factor = self.select_delay_factor(delay_factor)
        if config_commands is None:
            return ""
        elif isinstance(config_commands, str):
            config_commands = (config_commands,)

        if not hasattr(config_commands, "__iter__"):
            raise ValueError("Invalid argument passed into send_config_set")

        # Send config commands
        output = ""
        if enter_config_mode:
            cfg_mode_args = (config_mode_command,) if config_mode_command else tuple()
            output += self.config_mode(*cfg_mode_args)

        if self.fast_cli and self._legacy_mode:
            for cmd in config_commands:
                self.write_channel(self.normalize_cmd(cmd))
            # Gather output
            output += self._read_channel_timing(
                delay_factor=delay_factor, max_loops=max_loops
            )
        elif not cmd_verify:
            for cmd in config_commands:
                self.write_channel(self.normalize_cmd(cmd))
                time.sleep(delay_factor * 0.05)
            # Gather output
            output += self._read_channel_timing(
                delay_factor=delay_factor, max_loops=max_loops
            )
        else:
            for cmd in config_commands:
                self.write_channel(self.normalize_cmd(cmd))

                # Make sure command is echoed
                new_output = self.read_until_pattern(pattern=re.escape(cmd.strip()))
                output += new_output

                # We might capture next prompt in the original read
                pattern = f"(?:{re.escape(self.base_prompt)}|\])"
                if not re.search(pattern, new_output):
                    # Make sure trailing prompt comes back (after command)
                    # NX-OS has fast-buffering problem where it immediately echoes command
                    # Even though the device hasn't caught up with processing command.
                    new_output = self.read_until_pattern(pattern=pattern)
                    output += new_output

        if exit_config_mode:
            output += self.exit_config_mode()
        output = self._sanitize_output(output)
        log.debug(f"{output}")
        return output


class HPComwareTelnet(HPComwareBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
