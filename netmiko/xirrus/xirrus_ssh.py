from netmiko.base_connection import BaseConnection

class XirrusSSH(BaseConnection):
    """
    Implement methods for interacting with XIRRUS APs.

    Disables 'enable()' and 'check_enable_mode()' methods.
    """

    def session_preparation(self):
        """
        Prepare the session after the connection has been established.

        Enter config mode.
        Disable paging (the '--more--' prompts).
        Exit config mode.
        """

        self.config_mode()
        self.disable_paging(command="no more\n")
        self.exit_config_mode()

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on Xirrus APs."""
        pass

    def enable(self, *args, **kwargs):
        """No enable mode on Xirrus APs."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on Xirrus APs."""
        pass
   
    def config_mode(self, config_command='configure'):
        """Enter configuration mode."""
        return super(XirrusSSH, self).config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config='end'):
        """Exit configuration mode."""
        return super(XirrusSSH, self).exit_config_mode(exit_config=exit_config)


    def commit(self, force=False, partial=False, device_and_network=False,
            policy_and_objects=False, delay_factor=.1):
        """Commit the candidate configuration."""
        delay_factor = self.select_delay_factor(delay_factor)

        if ((device_and_network or policy_and_objects and not partial):
