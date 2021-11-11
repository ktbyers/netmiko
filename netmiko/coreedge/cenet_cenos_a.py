from netmiko.coreedge.cenet_base import CenetBase


class CenetOSASSH(CenetBase):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="more off")

    pass
