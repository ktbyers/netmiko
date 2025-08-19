from typing import Optional, Any
from netmiko.hp.hp_comware import HPComwareBase


class HPComware1950Base(HPComwareBase):
    """
    Connection class for OfficeConnect 1950 series switches
    """

    def set_base_prompt(self, pri_prompt_terminator: str = ">", alt_prompt_terminator: str = "]",
                        delay_factor: float = 1.0, pattern: Optional[str] = None) -> str:
        ret =  super().set_base_prompt(pri_prompt_terminator, alt_prompt_terminator, delay_factor, pattern)
        self.enable_cmd_hpe1950()
        return ret

    def enable_cmd_hpe1950(self):
        """
        Enable terminal cmdline for HPE OfficeConnect 1950
        """
        self.send_command('xtd-cli-mode', 'Switch to extended CLI mode?')
        self.send_command('y', 'Password:')
        self.send_command('foes-bent-pile-atom-ship', 'Warning:')


class HPComware1950SSH(HPComware1950Base):
    pass


class HPComware1950Telnet(HPComware1950Base):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
