import json
import rich
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.theme import Theme
from rich.syntax import Syntax
from rich.text import Text

NAVY_BLUE = "#000080"
BLUE = "#1E90FF"
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


def output_text(results):
    console = Console(theme=CUSTOM_THEME)
    for device_name, output in results.items():
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
                # "xcode" alternate theme
                syntax = Syntax(formatted_json, "json", theme=theme)
                panel = Panel(
                    syntax,
                    border_style=Style(color=NAVY_BLUE),
                    expand=False,
                    padding=(1, 1)
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


def output_dispatcher(out_format, results):

    # Sort the results dictionary by device_name
    results = dict(sorted(results.items()))

    output_functions = {
        "text": output_text,
        "json": output_json,
        "yaml": output_yaml,
        "raw": output_raw,
        "json_raw": output_json,
    }
    kwargs = {}
    if out_format == "json_raw":
        func = output_functions.get(out_format, output_text)
        kwargs["raw"] = True
    else:
        func = output_functions.get(out_format, output_text)
    return func(results, **kwargs)


def output_failed_devices(failed_devices):
    if failed_devices:
        console = Console(theme=CUSTOM_THEME)

        # Sort the failed devices list
        failed_devices.sort()

        # Create the content for the panel
        content = Text()
        for device_name in failed_devices:
            content.append(f"  {device_name}\n", style="failed_device")

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
        console.print(panel, style="failed_title")
        console.print()
