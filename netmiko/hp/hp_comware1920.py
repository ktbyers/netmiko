from typing import Optional, Any
from netmiko.hp.hp_comware import HPComwareBase


class HPComware1920Base(HPComwareBase):
    """
    Connection class for OfficeConnect 1920 series switches
    """

    def set_base_prompt(self, pri_prompt_terminator: str = ">", alt_prompt_terminator: str = "]",
                        delay_factor: float = 1.0, pattern: Optional[str] = None) -> str:
        ret =  super().set_base_prompt(pri_prompt_terminator, alt_prompt_terminator, delay_factor, pattern)
        self.enable_cmd_hpe1920()
        return ret

    def enable_cmd_hpe1920(self):
        """
        Enable terminal cmdline for HPE OfficeConnect 1920
        """
        self.send_command('_cmdline-mode on', 'Continue?')
        self.send_command('y', 'password:')
        self.send_command('Jinhua1920unauthorized', 'Warning:')


class HPComware1920SSH(HPComware1920Base):
    pass


class HPComware1920Telnet(HPComware1920Base):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)