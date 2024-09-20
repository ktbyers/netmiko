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


#        print()
#        print("-" * 40)
#        print(device_name)
#        print(output)
#        print("-" * 40)


def output_json(results):
    for device_name, output in results.items():
        if output_json:
            # Try to parse the output as JSON
            json_data = json.loads(output)
            print_json(json.dumps({device_name: json_data}))


def output_yaml(results):
    pass


def output_dispatcher(out_format, results):

    output_functions = {"text": output_text, "json": output_json, "yaml": output_yaml}
    func = output_functions.get(out_format, output_text)
    return func(results)
