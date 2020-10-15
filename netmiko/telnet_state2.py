from transitions import Machine, State
from netmiko.channel import TelnetChannel


class TelnetLogin:
    def __init__(
        self,
        channel: TelnetChannel,
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
            State(name="LoginPending", on_enter=["send_enter"])
            #        'SendUsername',
            #        'SendPassword',
            #        "LoggedIn",
            #        "SpecialCase",
        ]

        return states

    def define_transitions(self):
        transitions = [{"trigger": "start", "source": "Start", "dest": "LoginPending"}]
        return transitions

    def send_enter(self):
        print("Hello world")


if __name__ == "__main__":
    login = TelnetLogin()

    import ipdb

    ipdb.set_trace()
    login.state
    login.start()
