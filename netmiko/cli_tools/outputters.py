import json
import re
import rich
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.theme import Theme
from rich.syntax import Syntax
from rich.text import Text

NAVY_BLUE = "#000080"
BLUE = "#1E90FF"
LINEN_WHITE = "#FAF0E6"

# "xcode"/"trac" alternate light themes
LIGHT_THEME = "trac"
LIGHT_BOX = NAVY_BLUE
# "rrt"/"vim" alternate dark themes
DARK_THEME = "rrt"
DARK_BOX = LINEN_WHITE

DARK_MODE = False
if DARK_MODE:
    DEFAULT_THEME = DARK_THEME
    DEFAULT_BOX = DARK_BOX
else:
    DEFAULT_THEME = LIGHT_THEME
    DEFAULT_BOX = LIGHT_BOX

CUSTOM_THEME = Theme(
    {
        "device_name": "bold magenta",
        "border": BLUE,
        "output": "green",
        "failed_title": "bold #800000",
        "failed_device": "black",
        "failed_border": "#800000",
    }
)


def output_raw(results):
    border_color = CUSTOM_THEME.styles.get("border").color.name

    if len(results) == 1:
        for device_name, output in results.items():
            print(output)
    else:
        for device_name, output in results.items():
            banner = "-" * len(device_name)
            rich.print(f"[bold {border_color}]{device_name}[/]")
            rich.print(f"[{border_color}]{banner}[/]")
            print(output)
            print()


def output_text(results, pattern=None):
    console = Console(theme=CUSTOM_THEME)

    for device_name, output in results.items():
        if pattern:
            # output = highlight_regex(output, pattern)
            output = highlight_regex_with_context(output, pattern)
        else:
            output = Text(output)

        panel = Panel(
            output,
            title=device_name,
            expand=False,
            border_style="border",
            title_align="left",
            padding=(1, 1),
        )
        console.print()
        console.print(panel)
        console.print()


def output_json(results, raw=False):
    console = Console(theme=CUSTOM_THEME)

    for device_name, output in results.items():
        try:
            json_data = json.loads(output)
            formatted_json = json.dumps(json_data, indent=2)
            banner = "-" * len(device_name)
            if raw:
                print()
                print(device_name)
                print(banner)
                print(formatted_json)
                print()
            else:
                theme = DEFAULT_THEME
                syntax = Syntax(formatted_json, "json", theme=theme)
                panel = Panel(
                    syntax,
                    border_style=Style(color=DEFAULT_BOX),
                    expand=False,
                    padding=(1, 1),
                )

                console.print()
                print(device_name)
                console.print(panel)
                console.print()

        except json.decoder.JSONDecodeError as e:
            msg = f"""

Error processing output for device: {device_name}

In order to use display the output in JSON (--json arg), you must provide the output in JSON
format (i.e. device supports '| json' or parse with TextFSM)

"""
            new_exception = json.decoder.JSONDecodeError(msg, e.doc, e.pos)
            # Raise the new exception, chaining it to the original one
            raise new_exception from e


def output_yaml(results):
    pass


def output_failed_devices(failed_devices):
    if failed_devices:
        console = Console(theme=CUSTOM_THEME)

        # Sort the failed devices list
        failed_devices.sort()

        # Create the content for the panel
        content = "\n"
        for device_name in failed_devices:
            content += f"  {device_name}\n"

        # Create and print the panel
        panel = Panel(
            content,
            title="Failed devices",
            expand=False,
            border_style="failed_border",
            title_align="left",
            padding=(1, 1),
        )

        console.print()
        console.print(panel)
        console.print()


def highlight_regex(text, pattern, highlight_color="red"):
    """
    Highlight text matching a regex pattern using Rich.
    """
    text_obj = Text(text)
    for match in re.finditer(pattern, text):
        start, end = match.span()
        text_obj.stylize(highlight_color, start, end)

    return text_obj


def highlight_regex_with_context(text, pattern, highlight_color="red", context_lines=2):
    """
    Highlight text matching a regex pattern using Rich, showing only the matching lines
    with a specified number of context lines before and after.
    """
    lines = text.split("\n")
    text_obj = Text()
    pattern = re.compile(pattern)

    for i, line in enumerate(lines):
        if pattern.search(line):
            # Add context lines before
            start = max(0, i - context_lines)
            for j in range(start, i):
                text_obj.append(lines[j] + "\n")

            # Add the matching line with highlighting
            line_obj = Text(line + "\n")
            for match in pattern.finditer(line):
                line_obj.stylize(highlight_color, match.start(), match.end())
            text_obj.append(line_obj)

            # Add context lines after
            end = min(len(lines), i + context_lines + 1)
            for j in range(i + 1, end):
                text_obj.append(lines[j] + "\n")

            # Add a separator if this isn't the last match
            if i + context_lines + 1 < len(lines):
                text_obj.append("...\n\n")

    return text_obj


def output_dispatcher(out_format, results, pattern=None):

    # Sort the results dictionary by device_name
    results = dict(sorted(results.items()))

    output_functions = {
        "text": output_text,
        "text_highlighted": output_text,
        "json": output_json,
        "yaml": output_yaml,
        "raw": output_raw,
        "json_raw": output_json,
    }
    kwargs = {}
    func = output_functions.get(out_format, output_text)
    if out_format == "text_highlighted":
        if pattern is None:
            raise ValueError("Regex search pattern must be set for!")
        kwargs["pattern"] = pattern
    elif out_format == "json_raw":
        kwargs["raw"] = True

    return func(results, **kwargs)
