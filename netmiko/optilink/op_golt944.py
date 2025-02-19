from netmiko.huawei.huawei import HuaweiTelnet


class OptilinkGOLT944Telnet(HuaweiTelnet):
    """Optilink GOLT 944 telnet driver"""

    def session_preparation(self) -> None:
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"[>\]]")
        self.set_base_prompt()
        self.config_mode()
        self.disable_paging(command="screen-rows per-page 0")
        self.exit_config_mode()
