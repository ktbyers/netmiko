import re
from netmiko.coreedge.cenet_base import CenetBase


class CenetOSBSSH(CenetBase):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="more off")

    def enable(
        self,
        cmd="enable",
        pattern="ssword",
        enable_pattern=r"\#",
        re_flags=re.IGNORECASE,
    ):
        return super().enable(
            cmd=cmd,
            pattern=pattern,
            enable_pattern=enable_pattern,
            re_flags=re_flags,
        )

    pass
