

class CommandBufferArbiter:
    """
    Acts as a send command rate limiter that maintains the “command buffer” at bucket_size number of commands.
    It would allow sending of bucket_size commands, when it sees X prompts come back, it allows another X command(s).
    If it doesn’t see a prompt come back in some time, it figures “I must have missed it” and sends another command.
    This continues until the config set is depleted.
    """

    def __init__(self, connection, bucket_size=10, timeout=10):
        """
        :param connection: Connection object

        :param bucket_size: The number of commands that can be executed without acknowledging the prompt
        :type bucket_size: int

        :param timeout: The amount of seconds before giving up looking for the prompt and allow another command to be sent
        :type timeout: int
        """
        self.connection = connection
        self.bucket_size = bucket_size
        self.timeout = timeout

        self.unacknowledged_commands = 0
        self.timer = None

        # lines that have already been checked for prompts
        self.completed_lines = []
        # lines that have yet to be checked for prompts
        self.pending_lines = []
        # The current line that has not yet been completed with a terminating EOL
        self.incomplete_line = ''

    def get_token(self, output):
        """
        Get permission from the Arbiter to send one command

        :param output: Connection.read_channel() would be directed here
        :type output: str

        :return: boolean - if a command can be sent
        """
        self.timer = time.time()

        self._process_output(output)

        log.debug(
            "Arbiter completed_lines: %s, pending_lines: %s, incomplete_line: %s, unacknowledged_commands: %s",
            len(self.completed_lines),
            len(self.pending_lines),
            self.incomplete_line,
            self.unacknowledged_commands,
        )

        if self.unacknowledged_commands < self.bucket_size:
            self.unacknowledged_commands += 1
            log.debug("Arbiter granted token")
            return True

        return False

    def is_done(self, output):
        """
        Process a batch of output and return True when the Arbiter appears done

        :param output: Connection.read_channel() would be directed here
        :type output: str

        :return: boolean True when the Arbiter appears done
        """
        self._process_output(output)
        log.debug(
            "Arbiter checking if done - unacknowledged_commands: %s",
            self.unacknowledged_commands,
            self.incomplete_line,
        )
        return not bool(self.unacknowledged_commands)

    def all_output(self):
        """
        Builds a string containing all of the processed output

        :return: str all of the processed output
        """
        completed_and_pending_lines = "\n".join(self.completed_lines + self.pending_lines)
        return "{}\n{}".format(
            completed_and_pending_lines,
            self.incomplete_line
        )

    def _process_output(self, output):
        log.debug("Arbiter ingest output:\n%s", output)
        output_lines = output.splitlines()

        # If the output starts with a new line, close out the incomplete line
        if output.startswith('\n'):
            output_lines.insert(0, self.incomplete_line)
            self.incomplete_line = ''

        if output_lines:
            # Concatenate the incomplete line with the first line in the output
            output_lines[0] = self.incomplete_line + output_lines[0]
            self.incomplete_line = ''

            # Consider the last line incomplete if the output does not end with a new line
            if not output.endswith('\n'):
                self.incomplete_line = output_lines.pop()

        self.pending_lines.extend(output_lines)

        self._count_prompts()
        self._process_timer()

    def _count_prompts(self):
        while self.pending_lines:
            line = self.pending_lines.pop(0)
            # for every prompt we see, reset the timer, subtract from unacknowledged_commands
            if self.connection.line_has_prompt(line):
                self._acknowledge_command()
            self.completed_lines.append(line)

        # If self.incomplete_line contains a prompt
        if self.connection.line_has_prompt(self.incomplete_line):
            log.debug("Arbiter found prompt in incomplete_line")
            self._acknowledge_command()
            self.completed_lines.append(self.incomplete_line)
            self.incomplete_line = ''

    def _process_timer(self):
        # If our timer has expired, acknowledge one command
        if time.time() - self.timer > self.timeout:
            if self.unacknowledged_commands:
                log.warning("Arbiter expiring an unacknowledged_command")
                self._acknowledge_command()
            self.timer = time.time()

    def _acknowledge_command(self):
        self.unacknowledged_commands -= min(1, self.unacknowledged_commands)
        self.timer = time.time()
