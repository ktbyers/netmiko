import re
import time
from typing import List, Dict, Callable, Optional
from typing import TYPE_CHECKING
from transitions import Machine, State

from netmiko import log
from netmiko.ssh_exception import NetmikoAuthenticationException

import logging

# Make Transitions log less as it is way too noisy
logging.getLogger("transitions").setLevel(logging.CRITICAL)


if TYPE_CHECKING:
    from netmiko.channel import TelnetChannel


class TelnetLogin:
    if TYPE_CHECKING:
        state: str
        done_sleeping: Callable[..., bool]
        username_sent: Callable[..., bool]
        password_sent: Callable[..., bool]
        username_prompt_detected: Callable[..., bool]
        password_prompt_detected: Callable[..., bool]
        logged_in: Callable[..., bool]
        no_match: Callable[..., bool]
        enter_sent: Callable[..., bool]
        finish_config_dialog: Callable[..., bool]

    def __init__(
        self,
        channel: "TelnetChannel",
        username: str,
        password: str,
        username_pattern: str,
        password_pattern: str,
        pri_prompt_terminator: str,
        alt_prompt_terminator: str,
        login_timeout: int,
        addl_patterns: Optional[List[Dict[str, str]]] = None,
    ) -> None:

        self.channel = channel
        self.login_timeout = login_timeout

        self.username = username
        self.password = password

        self.username_pattern = username_pattern
        self.password_pattern = password_pattern

        prompt_regex = rf"({pri_prompt_terminator}|{alt_prompt_terminator})"
        self.prompt_regex = prompt_regex

        # Record the entire interaction
        self.capture = ""

        # Define the state machine
        self.states = self.define_states()
        self.transitions = self.define_transitions()

        # Create the state machine
        self.fsm = self.create_machine()

        self.patterns = [
            {
                "name": "username",
                "pattern": self.username_pattern,
                "tr_method": "username_prompt_detected",
            },
            {
                "name": "password",
                "pattern": self.password_pattern,
                "tr_method": "password_prompt_detected",
            },
            {"name": "prompt", "pattern": self.prompt_regex, "tr_method": "logged_in"},
        ]

        if addl_patterns is not None:
            self.patterns += addl_patterns

    def create_machine(self) -> Machine:
        machine = Machine(
            self, states=self.states, transitions=self.transitions, initial="Start"
        )
        return machine

    def define_states(self) -> List[State]:
        states = [
            State(name="Start", on_exit=["start_timer"]),
            State(name="LoginPending", on_enter=["random_sleep", "read_channel"]),
            State(name="SleepLonger", on_enter=["sleep_longer"]),
            State(name="SendUsername", on_enter=["send_username"]),
            State(name="SendPassword", on_enter=["send_password"]),
            State(name="LoggedIn"),
            State(name="CiscoConfigDialog", on_enter=["handle_config_dialog"]),
            State(name="HitEnter", on_enter=["hit_enter"]),
        ]

        return states

    def define_transitions(self) -> List[Dict[str, str]]:
        transitions = [
            {"trigger": "start", "source": "Start", "dest": "LoginPending"},
            {"trigger": "no_match", "source": "LoginPending", "dest": "SleepLonger"},
            {
                "trigger": "done_sleeping",
                "source": "SleepLonger",
                "dest": "LoginPending",
            },
            {
                "trigger": "username_prompt_detected",
                "source": "LoginPending",
                "dest": "SendUsername",
            },
            {
                "trigger": "cisco_config_dialog",
                "source": "LoginPending",
                "dest": "CiscoConfigDialog",
            },
            {
                "trigger": "press_enter_to_continue",
                "source": "LoginPending",
                "dest": "HitEnter",
            },
            {
                "trigger": "password_prompt_detected",
                "source": "LoginPending",
                "dest": "SendPassword",
            },
            {"trigger": "logged_in", "source": "LoginPending", "dest": "LoggedIn"},
            {
                "trigger": "username_sent",
                "source": "SendUsername",
                "dest": "LoginPending",
            },
            {
                "trigger": "password_sent",
                "source": "SendPassword",
                "dest": "LoginPending",
            },
            {"trigger": "enter_sent", "source": "HitEnter", "dest": "LoginPending"},
            {
                "trigger": "finish_config_dialog",
                "source": "CiscoConfigDialog",
                "dest": "LoginPending",
            },
        ]
        return transitions

    def start_timer(self) -> None:
        self.start_time = time.time()
        self.reset_time = time.time()

    def read_channel(self) -> str:
        log.debug(f"State: {self.state} read_channel() method")
        data = self.channel.read_channel()
        log.debug(f"Data on read_channel:\n\n{data}")
        self.capture += data
        self.parse_output(data)
        return data

    @staticmethod
    def random_sleep() -> None:
        # FIX: do something different here
        time.sleep(0.1)

    def sleep_longer(self) -> None:
        log.debug(f"State: {self.state} sleep_longer() method")
        time.sleep(0.5)
        self.done_sleeping()

    def send_username(self) -> None:
        log.debug(f"State: {self.state} send_username() method")
        # Sometimes username must be terminated with "\r" and not "\r\n"
        self.channel.write_channel(self.username + "\r")
        self.random_sleep()
        self.username_sent()

    def send_password(self) -> None:
        log.debug(f"State: {self.state} send_password() method")
        # Sometimes username must be terminated with "\r" and not "\r\n"
        self.channel.write_channel(self.password + "\r")
        self.random_sleep()
        self.password_sent()

    def hit_enter(self) -> None:
        # FIX: use telnet enter
        self.channel.write_channel("\r\n")
        self.enter_sent()

    def handle_config_dialog(self) -> None:
        """
        Cisco devices via a terminal server might prompt with:

        Would you like to enter the initial configuration dialog? [yes/no]:

        Send "no"
        """
        log.debug(f"State: {self.state} handle_config_dialog() method")
        # Sometimes username must be terminated with "\r" and not "\r\n"
        # FIX: use self.TELNET_RETURN
        self.channel.write_channel("no" + "\r\n")
        self.finish_config_dialog()

    def parse_output(self, data: str) -> None:
        log.debug(f"State: {self.state} parse_output() method")

        # import ipdb; ipdb.set_trace()
        for case in self.patterns:
            pattern = case["pattern"]
            name = case["name"]
            tr_method = case["tr_method"]

            if re.search(pattern, data, flags=re.I):
                if name == "prompt":
                    msg = f"""
Successfully logged in. Entire output capture:

{self.capture}

"""
                    log.debug(msg)

                # Execute the transitions
                method = getattr(self, tr_method)
                method()
                break

        if time.time() > self.start_time + self.login_timeout:
            msg = f"""

Telnet login timed-out to {self.channel.host}:

Please ensure your username and password are correct.

"""
            raise NetmikoAuthenticationException(msg)

        if self.state == "LoggedIn":
            return
        else:
            # Certain situations can require hitting an enter to activate
            # the channel (for example, a device connected via a terminal server)
            # import ipdb; ipdb.set_trace()
            if data == "" and time.time() - self.reset_time > 1:
                self.channel.write_channel("\r\n")
                time.sleep(0.5)
                self.reset_time = time.time()
            self.no_match()
