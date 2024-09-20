import json
from rich import print_json
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

CUSTOM_THEME = Theme(
    {
        "device_name": "bold magenta",
        "border": "cyan",
        "output": "green",
    }
)


def output_text(results):
    # Create a custom theme for consistent coloring

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


def output_json(results):
    for device_name, output in results.items():
        if output_json:
            try:
                json_data = json.loads(output)
                print_json(json.dumps({device_name: json_data}))
            except json.decoder.JSONDecodeError as e:
                msg = f"""

Error processing output for device: {device_name}

In order to use display the output in JSON (--json arg), you must provide the output in JSON
format (i.e. device supports '| json' or parse with TextFSM)

"""
                new_exception = json.decoder.JSONDecodeError(
                    msg,
                    e.doc,
                    e.pos
                )
                # Raise the new exception, chaining it to the original one
                raise new_exception from e


def output_yaml(results):
    pass


def output_dispatcher(out_format, results):

    output_functions = {"text": output_text, "json": output_json, "yaml": output_yaml}
    func = output_functions.get(out_format, output_text)
    return func(results)
