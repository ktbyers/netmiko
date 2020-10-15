#
#"""
#269             STATES:
#270             NoLogin:
#271                 Events:
#272                 * Transition to LoginPending State
#273                 
#270             NoLogin:
#274             SendUsername:
#275                 Events:
#276                 * Sends the username -> Transition to LoginPending
#277                 
#270             NoLogin:
#274             SendUsername:
#278             LoginPending
#279                 Events:
#280                 * Detect username_pattern -> Transition to SendUsername
#281                 * Detect password_pattern -> Transition to SendPassword
#282                 * Detect prompt pattern -> Transition to LoggedIn
#283                 * Special Events
#284                     a. Receive initial configuration dialog message
#285                     b. Receive password not set message
#286                     
#287              
#270             NoLogin:
#274             SendUsername:
#278             LoginPending
#288             SendPassword:
#289                 Events: 
#290                 * Sends the password -> Transition to LoginPending
#
#228         pri_prompt_terminator=r"#\s*$",
#229         alt_prompt_terminator=r">\s*$",
#230         username_pattern=r"(?:user:|username|login|user name)",
#231         pwd_pattern=r"assword",
#"""
#from netmiko.channel import TelnetChannel
#
#Class TelnetLogin:
#
#    def __init__(
#        self,
#        channel: TelnetChannel,
#        username: str, 
#        password: str, 
#        username_pattern: str, 
#        pwd_pattern: str,
#        prompt_pattern: str,
#        state: Optional[str] = None,
#    ) -> None:
#
#        self.state = state
#
#    def state_transition(self):
#        if self.state is not None:
#            self.state()
#
#    def login(self):
#        if self.state is None:
#            self.state = login_pending
#
#        self.state_transition()
#
#    def login_pending(self):
#        self.send_enter()


#270             NoLogin:
#274             SendUsername:
#278             LoginPending
#288             SendPassword:

# The states
states = ['Start', 'LoginPending', 'SendUsername', 'SendPassword', "LoggedIn", "SpecialCase"]

# And some transitions between states. We're lazy, so we'll leave out
# the inverse phase transitions (freezing, condensation, etc.).
transitions = [
    { 'trigger': 'melt', 'source': 'solid', 'dest': 'liquid' },
    { 'trigger': 'evaporate', 'source': 'liquid', 'dest': 'gas' },
    { 'trigger': 'sublimate', 'source': 'solid', 'dest': 'gas' },
    { 'trigger': 'ionize', 'source': 'gas', 'dest': 'plasma' }
]

# Initialize
machine = Machine(lump, states=states, transitions=transitions, initial='liquid')

# Now lump maintains state...
lump.state
>>> 'liquid'

# And that state can change...
lump.evaporate()
lump.state
>>> 'gas'
lump.trigger('ionize')
lump.state
>>> 'plasma'
