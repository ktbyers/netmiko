from typing import Optional, Any
from netmiko.hp.hp_comware import HPComwareBase


class HPComware1910Base(HPComwareBase):
    """
    Connection class for OfficeConnect 1920 series switches
    """

    def set_base_prompt(self, pri_prompt_terminator: str = ">", alt_prompt_terminator: str = "]",
                        delay_factor: float = 1.0, pattern: Optional[str] = None) -> str:
        ret =  super().set_base_prompt(pri_prompt_terminator, alt_prompt_terminator, delay_factor, pattern)
        self.enable_cmd_hpe1910()
        return ret

    def enable_cmd_hpe1910(self):
        """
        Enable terminal cmdline for HPE OfficeConnect 1920
        """
        self.send_command('_cmdline-mode on', 'Continue?')
        self.send_command('y', 'password:')
        self.send_command('512900', 'Warning:')


class HPComware1910SSH(HPComware1910Base):
    pass


class HPComware1910Telnet(HPComware1910Base):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)