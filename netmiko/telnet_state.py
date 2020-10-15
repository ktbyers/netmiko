import re
from typing import TYPE_CHECKING
from transitions import Machine, State

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
            State(name="LoginPending", on_enter=["read_channel"]),
            State(name="SendUsername", on_enter=["send_username"]),
            #        'SendUsername',
            #        'SendPassword',
            #        "LoggedIn",
            #        "SpecialCase",
        ]

        return states

    def define_transitions(self):
        transitions = [
            {"trigger": "start", "source": "Start", "dest": "LoginPending"},
            {
                "trigger": "username_prompt_detected",
                "source": "LoginPending",
                "dest": "SendUsername",
            },
        ]
        return transitions

    def read_channel(self) -> str:
        data = self.channel.read_channel()
        self.output += data
        self.parse_output(data)
        import ipdb

        ipdb.set_trace()
        print(data)
        return data

    def send_username(self):
        print("Made it here")

    def parse_output(self, data: str):

        patterns = [
            {"name": "username", "pattern": self.username_pattern},
            {"name": "password", "pattern": self.password_pattern},
            {"name": "prompt", "pattern": self.prompt_regex},
        ]

        for case in patterns:
            pattern = case["pattern"]
            name = case["name"]

            # HERE!!!!
            ipdb.set_trace()

            if re.search(pattern, data, flags=re.I):
                # Execute the transitions
                if name == "username":
                    self.username_prompt_detected()
                break


if __name__ == "__main__":
    login = TelnetLogin()

    import ipdb

    ipdb.set_trace()
    login.state
    login.start()
