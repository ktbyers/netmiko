import re
import subprocess
import sys

import pytest

from netmiko.zpe.zpe_nodegrid import ZpeNodegridSSH


@pytest.mark.parametrize(
    "prompt",
    [
        "[admin@nodegrid /]#",
        "[admin@nodegrid ETH0]#",
        "[+admin@nodegrid ETH0]#",
    ],
)
def test_cli_prompt(prompt: str) -> None:
    """Recognize normal and staged-change CLI prompts after bracketed output.

    Check the matched text and boundaries exclude preceding output and trailing space.
    Verify stripping removes only the prompt line, preserving command output.
    """
    output = f"interface: [ETH0]\n{prompt} "
    match = re.search(pattern=ZpeNodegridSSH.prompt_pattern, string=output)
    assert match is not None
    assert match.group() == prompt
    assert match.start() == len("interface: [ETH0]\n")
    assert match.end() == len(output) - 1

    connection = ZpeNodegridSSH.__new__(ZpeNodegridSSH)
    connection.RESPONSE_RETURN = "\n"
    assert connection.strip_prompt(a_string=output) == "interface: [ETH0]"


@pytest.mark.parametrize(
    "prompt", ["admin@nodegrid:~$", "root@nodegrid:~#", "root@nodegrid:/var/home#"]
)
def test_shell_prompt(prompt: str) -> None:
    """Recognize shell prompts with user/root terminators and home/absolute paths.

    Check matching works after a newline and ends at the terminator, before whitespace.
    This ensures shell-mode command completion can detect the documented prompts.
    """
    output = f"Entering shell\n{prompt} "
    match = re.search(pattern=ZpeNodegridSSH.shell_prompt_pattern, string=output)
    assert match is not None
    assert match.group() == prompt
    assert match.end() == len(output) - 1


@pytest.mark.parametrize(
    "output",
    ["ordinary output", "[admin@nodegrid /]", "[admin@nodegrid\n/]#", ""],
)
def test_non_prompt_output(output: str) -> None:
    """Reject ordinary, empty, incomplete, and newline-split CLI prompt text.

    Verify stripping leaves each non-prompt input unchanged.
    This prevents false prompt detection from discarding command output.
    """
    assert re.search(pattern=ZpeNodegridSSH.prompt_pattern, string=output) is None
    connection = ZpeNodegridSSH.__new__(ZpeNodegridSSH)
    connection.RESPONSE_RETURN = "\n"
    assert connection.strip_prompt(a_string=output) == output


@pytest.mark.parametrize(
    "output",
    ["user@host:path", "user@host:\npath#", "user@\nhost:path$", "plain output$"],
)
def test_non_shell_prompt_output(output: str) -> None:
    """Reject incomplete shell prompts and prompt components split across lines.

    Also reject a dollar-terminated line without the username/hostname structure.
    These checks guard against prematurely treating ordinary output as a shell prompt.
    """
    assert re.search(pattern=ZpeNodegridSSH.shell_prompt_pattern, string=output) is None


def test_nested_brackets_prompt_termination() -> None:
    """Recognize a nested-bracket prompt through its final terminator.

    Allow either opening bracket to start the match, but exclude the preceding line.
    Verify stripping removes the entire prompt line without losing command output.
    """
    output = "command output\n[ some text [ some more text ] ]# "
    match = re.search(pattern=ZpeNodegridSSH.prompt_pattern, string=output)
    assert match is not None
    assert match.end() == len(output) - 1
    # Either outer or inner '[' can start the match; neither may consume the output line.
    assert match.start() >= len("command output\n")
    connection = ZpeNodegridSSH.__new__(ZpeNodegridSSH)
    connection.RESPONSE_RETURN = "\n"
    assert connection.strip_prompt(a_string=output) == "command output"


@pytest.mark.parametrize(
    "pattern, repeated_text, count",
    [
        pytest.param(ZpeNodegridSSH.prompt_pattern, "[", 200_000, id="cli-opening-brackets"),
        pytest.param(ZpeNodegridSSH.prompt_pattern, "[+", 100_000, id="cli-staged-brackets"),
        pytest.param(ZpeNodegridSSH.shell_prompt_pattern, "@:", 2_000, id="shell-delimiters"),
        pytest.param(ZpeNodegridSSH.shell_prompt_pattern, "u@h:", 2_000, id="shell-prefixes"),
    ],
)
def test_nonmatching_output_search_is_bounded(pattern: str, repeated_text: str, count: int) -> None:
    """Require long delimiter-heavy output to be rejected within five seconds.

    Run each driver regex in a subprocess that is killed and reaped on timeout,
    so excessive backtracking cannot hang pytest.
    This catches severe runtime regressions but does not prove linear complexity.
    """
    search_code = (
        "import re, sys\n"
        "match = re.search(pattern=sys.argv[1], string=sys.stdin.read())\n"
        "sys.exit(0 if match is None else 1)\n"
    )
    output = "command output\n" + repeated_text * count + "\nend of output"
    try:
        result = subprocess.run(
            args=[sys.executable, "-c", search_code, pattern],
            input=output,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except subprocess.TimeoutExpired:
        pytest.fail("Prompt search exceeded the 5-second subprocess limit", pytrace=False)
    assert result.returncode == 0, result.stderr or "Non-prompt output matched a prompt"
