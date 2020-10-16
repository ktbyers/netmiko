import re
from typing import TYPE_CHECKING
from transitions import Machine, State
import time

if TYPE_CHECKING:
    from netmiko.channel import TelnetChannel


class TelnetLogin:
    def __init__(
        self,
        channel: "TelnetChannel",
        username: str,
        password: str,
        username_pattern: str,
        password_pattern: str,
        pri_prompt_terminator: str,
        alt_prompt_terminator: str,
    ) -> None:

        self.channel = channel

        self.username = username
        self.password = password

        self.username_pattern = username_pattern
        self.password_pattern = password_pattern

        prompt_regex = r"(pri_prompt_terminator|alt_prompt_terminator)"
        self.prompt_regex = prompt_regex

        # Record the entire interaction
        self.output = ""

        # Define the state machine
        self.states = self.define_states()
        self.transitions = self.define_transitions()

        # Create the state machine
        self.fsm = self.create_machine()

    def create_machine(self):
        machine = Machine(
            self, states=self.states, transitions=self.transitions, initial="Start"
        )
        return machine

    def define_states(self):
        states = [
            State(name="Start"),
            State(name="LoginPending", on_enter=["random_sleep", "read_channel"]),
            State(name="SleepLonger", on_enter=["sleep_longer"]),
            State(name="SendUsername", on_enter=["send_username"]),
            State(name="SendPassword", on_enter=["send_password"]),
            State(name="LoggedIn"),
            # "SpecialCase",
        ]

        return states

    def define_transitions(self):
        transitions = [
            {"trigger": "start", "source": "Start", "dest": "LoginPending"},
            {
                "trigger": "no_match",
                "source": "LoginPending",
                "dest": "SleepLonger",
            },
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
        ]
        return transitions

    def read_channel(self) -> str:
        print(f"State: {self.state} read_channel() method")
        data = self.channel.read_channel()
        print(data)
        self.output += data
        self.parse_output(data)
        return data

    @staticmethod
    def random_sleep():
        # FIX: do something different here
        time.sleep(0.5)

    def sleep_longer(self):
        print(f"State: {self.state} sleep_longer() method")
        self.random_sleep()
        self.done_sleeping()

    def send_username(self) -> None:
        print(f"State: {self.state} send_username() method")
        # Sometimes username must be terminated with "\r" and not "\r\n"
        self.channel.write_channel(self.username + "\r")
        self.random_sleep()
        self.username_sent()

    def send_password(self) -> None:
        print(f"State: {self.state} send_password() method")
        # Sometimes username must be terminated with "\r" and not "\r\n"
        self.channel.write_channel(self.password + "\r")
        self.random_sleep()
        self.password_sent()

    def parse_output(self, data: str):
        print(f"State: {self.state} parse_output() method")

        patterns = [
            {"name": "username", "pattern": self.username_pattern},
            {"name": "password", "pattern": self.password_pattern},
            {"name": "prompt", "pattern": self.prompt_regex},
        ]

        for case in patterns:
            pattern = case["pattern"]
            name = case["name"]

            if re.search(pattern, data, flags=re.I):
                # Execute the transitions
                if name == "username":
                    self.username_prompt_detected()
                elif name == "password":
                    self.password_prompt_detected()
                elif name == "prompt":
                    self.logged_in()
                    print(self.output)
                break

        self.no_match()
