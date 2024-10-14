from config import Config
from logger import LogEntry, LogVector, LogReader, LogSegmentation
import rich_click as click
from rich import pretty
from rich.console import Console
from rich.text import Text
from rich.tree import Tree
import os
import tempfile
import logging
import subprocess
from datetime import datetime
import re
import shutil
import json


console = Console()

@click.group()
@click.option('--debug', is_flag=True, help="Enable debug mode.")
@click.pass_context
def cli(ctx, debug):
    """Main entry point for the project management CLI."""
    # Load the configuration at the start
    config = Config("../config.json")

    # Set the config in the context object so all commands can access it
    ctx.ensure_object(dict)
    ctx.obj['config'] = config.config

    # Update debug mode in the context if the --debug flag is set
    ctx.obj['debug'] = debug or config.config.get("debug", False)

    # Set up logging based on the debug flag
    log_level = logging.DEBUG if ctx.obj['debug'] else logging.ERROR
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

@cli.command()
@click.pass_context
def list(ctx: click.Context) -> None:
    """
    Lists all projects in the default directory.
    """
    path = os.path.expanduser(ctx.obj["config"]["path"])
    logging.debug(f"Listing projects in {path}...")

    if os.path.isdir(path):
        tree = Tree(f"[magenta]Projects:")

        def add_to_tree(parent_node, current_path):
            for item in os.listdir(current_path):
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    child_node = parent_node.add(f"{item}")
                    add_to_tree(child_node, item_path)

        add_to_tree(tree, path)
        console.print(tree)
    else:
        click.echo(f"Path {path} does not exist.")

@cli.command()
@click.argument("project_name")
@click.option("--sub", required=False, help="Creates a sub-folder in the project. If project doesn't exists, it creates it.")
@click.pass_context
def create(ctx: click.Context, project_name: str, sub: str = None) -> None:
    """
    Creates a new project in the default directory.
    """
    path = os.path.expanduser(ctx.obj["config"]["path"])
    logging.debug(f"Creating project {project_name} in {path}...")

    if not os.path.isdir(path):
        logging.error(f"Path {path} does not exist.")
        return

    if sub:
        sub_path = os.path.join(path, project_name, sub)
        if os.path.isdir(sub_path):
            logging.error(f"Sub-folder {sub} already exists in project {project_name}.")
            return
        os.makedirs(os.path.join(path, project_name, sub), exist_ok=True)
        logging.debug(f"Created sub-folder {sub} in project {project_name}.")
    else:
        if os.path.isdir(os.path.join(path, project_name)):
            logging.error(f"Project {project_name} already exists.")
            return
        os.mkdir(os.path.join(path, project_name))
        logging.debug(f"Created project {project_name}.")


@cli.command()
@click.argument("project_name")
@click.option("--sub", required=False, help="Edits the config of a sub-project.")
@click.pass_context
def edit_project(ctx: click.Context, project_name: str, sub: str = None) -> None:
    """
    Edits the project configuration.
    """
    path = os.path.expanduser(ctx.obj["config"]["path"])
    logging.debug(f"Editing project {project_name} in {path}...")

    if not os.path.isdir(path):
        logging.error(f"Path {path} does not exist.")
        return

    # Sub-project might have different configurations.
    if sub:
        edit_path = os.path.join(path, project_name, sub)
    else:
        edit_path = os.path.join(path, project_name)

    if not os.path.isdir(edit_path):
        if sub:
            logging.error(f"Sub-folder {sub} does not exist in project {project_name}.")
        else:
            logging.error(f"Project {project_name} does not exist.")
        return

    try:
        editor = ctx.obj["config"]["editor"]
    except:
        editor = "nano"

    config_path = os.path.join(edit_path, "config.json")
    if not os.path.isfile(config_path):
        default_config = {
            "editor": "nano",
            "log_limit": 100,
            "default_template": "default_template"
        }

        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
        
    subprocess.call([editor, config_path])

@cli.command()
@click.argument("project_name")
@click.option("--sub", required=False, help="Deletes a sub-folder in the project.")
@click.pass_context
def edit_project_name(ctx: click.Context, project_name: str, sub: str = None) -> None:
    """
    Edits the project name.
    """    
    if sub:
        edit_path = os.path.join(path, project_name, sub)
    else:
        edit_path = os.path.join(path, project_name)
    new_name = click.prompt("New project name")
    if new_name == project_name:
        logging.debug("New project name is the same as the old one.")
        return
    elif new_name == "":
        logging.error("New project name cannot be empty.")
        return
    if sub:
        os.rename(edit_path, os.path.join(path, project_name, new_name))
    else:
        os.rename(edit_path, os.path.join(path, new_name))
    logging.debug(f"Renamed project {project_name} to {new_name}.")


@cli.command()
@click.pass_context
def display_config(ctx: click.Context) -> None:
    """
    Displays the current configuration.
    """
    config = ctx.obj["config"]

    click.echo("Configuration:")
    for key, value in config.items():
        click.echo(f"  - {key}: {value}")

@cli.command()
@click.option("--key", required=True, help="The key to set.")
@click.option("--value", required=True, help="The value to set.")
@click.pass_context
def set_config(ctx: click.Context, key: str, value: str) -> None:
    """
    Sets the configuration.
    """
    config = ctx.obj["config"]
    
    if key not in config:
        logging.error(f"Key {key} not found in config.")
        return

    cfg = Config("../config.json")
    cfg.change(key, value)
    ctx.obj["config"] = cfg.config
    logging.debug(f"Set {key} to {value}.")


def writer(editor, template:str = None) -> str:
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        tmp_file_name = f.name
        logging.debug(f"Created temporary file {tmp_file_name}.")

        if template:
            # Copy content from the template file to the temporary file
            with open(template, 'r') as template:
                shutil.copyfileobj(template, f)

    subprocess.run([editor, tmp_file_name])

    logging.debug(f"Opened editor {editor} for temporary file {tmp_file_name}.")
    with open(tmp_file_name, "r") as f:
        text = f.read().strip()
        logging.debug(f"Read log from temporary file: {text}")

    os.remove(tmp_file_name)
    return text


@cli.command()
@click.argument("project_name")
@click.option("--sub", required=False, help="Edits the config of a sub-project.")
@click.option("--template", required=False, help="Name of the template used to write the log.")
@click.pass_context
def write(ctx: click.Context, project_name: str, sub: str = None, template: str = None) -> None:
    """
    Writes a new entry to the project log.
    """
    path = os.path.expanduser(ctx.obj["config"]["path"])
    logging.debug(f"Writing to project {project_name} in {path}...")

    if not os.path.isdir(path):
        logging.error(f"Path {path} does not exist.")
        return

    if sub:
        write_path = os.path.join(path, project_name, sub)
    else:
        write_path = os.path.join(path, project_name)

    if not os.path.isdir(write_path):
        if sub:
            logging.error(f"Sub-folder {sub} does not exist in project {project_name}.")
        else:
            logging.error(f"Project {project_name} does not exist.")
        return
    
    try:
        editor = ctx.obj["config"]["editor"]
    except:
        editor = "nano"

    template_path = None

    if template:
        template_path = os.path.join(os.path.expanduser(ctx.obj["config"]["template_path"]), template)
        if not os.path.isfile(template_path):
            logging.error(f"Template {template} does not exist.")
            return

    log = writer(editor, template_path)

    if log:
        reader = LogReader(write_path, int(ctx.obj["config"]["log_limit"]))
        prev_logs = reader.read_logs(reader.seg.last_log_file())
        logEntry = LogEntry(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), log)
        prev_logs.append(logEntry)
        logging.debug(f"Appended log to previous logs {prev_logs}.")
        logging.debug(f"Writing logs to project log file: {reader.seg.last_log_file()}")
        reader.write_logs(prev_logs)
        logging.debug(f"Wrote log to project log file.")


def log_printer(project: str, log: LogVector) -> None:
    """
    Prints a log entry in a formatted way.
    Keywords (in:, on:, with:, etc) are highlighted in light green. 
        These keywords are the prefix used to set searchable tags for the log entry.
        See keywords.py for more details. 
    """
    log_text = Text(f"{project}", style="bold green")
    log_text.append(" - ", style="bold white")
    log_text.append(f"[{log.date}]\n", style="magenta")

    keyword_pattern = re.compile(r"\b(\w+):(?=\S)(\S+)")
    last_index = 0
    for match in keyword_pattern.finditer(log.log):
        # Append text before the match
        if match.start() > last_index:
            log_text.append(log.log[last_index:match.start()], style="white")
        # Append the matched keyword and the colon in light green
        log_text.append(match.group(1) + ":" + match.group(2), style="light_green")
        last_index = match.end()

    # Append the rest of the log after the last match
    if last_index < len(log.log):
        log_text.append(log.log[last_index:], style="white")

    console.print(log_text)

def log_viewer(project: str, logs: LogVector) -> None:
    """
    Displays the logs in a paginated format.
    """
    for log in logs:
        log_printer(project, log)

@cli.command()
@click.argument("project_name")
@click.option("--sub", required=False, help="Edits the config of a sub-project.")
@click.pass_context
def latest(ctx: click.Context, project_name: str, sub:str = None) -> None:
    """
    Displays the latest log entry.
    """
    path = os.path.expanduser(ctx.obj["config"]["path"])
    logging.debug(f"Reading latest log from project {project_name} in {path}...")

    if not os.path.isdir(path):
        logging.error(f"Path {path} does not exist.")
        return

    if sub:
        latest_path = os.path.join(path, project_name, sub)
    else:
        latest_path = os.path.join(path, project_name)

    if not os.path.isdir(latest_path):
        logging.error(f"Project {project_name} does not exist.")
        return

    reader = LogReader(latest_path, int(ctx.obj["config"]["log_limit"]))
    path = os.path.join(reader.seg.project_path, reader.seg.last_log_file())
    logs = reader.read_logs(path)
    if logs:
        log_printer(f"{project_name}/{sub}", logs.logs[-1])
    else:
        click.echo("No logs found.")

@cli.command()
@click.argument("project_name")
@click.option("--sub", required=False, help="Edits the config of a sub-project.")
@click.pass_context
def edit(ctx: click.Context, project_name:str, sub: str = None) -> None:
    """
    Edits the lastest log file of the chosen project.
    TODO: Should it only be possible to edit the latest entry? Or should it be possible to choose the entry to edit? 
    """
    path = os.path.expanduser(ctx.obj["config"]["path"])
    logging.debug(f"Editing to project {project_name} in {path}...")

    if not os.path.isdir(path):
        logging.error(f"Path {path} does not exist.")
        return
    
    if sub:
        edit_path = os.path.join(path, project_name, sub)
    else:
        edit_path = os.path.join(path, project_name)
    
    if not os.path.isdir(edit_path):
        if sub:
            logging.error(f"Sub-folder {sub} does not exist in project {project_name}.")
        else:
            logging.error(f"Project {project_name} does not exist.")
        return
    
    reader = LogReader(edit_path, int(ctx.obj["config"]["log_limit"]))
    file_to_edit = os.path.join(edit_path, reader.seg.last_log_file())
    subprocess.run(["nano", file_to_edit])


@cli.command()
@click.argument("template_name")
@click.pass_context
def create_template(ctx: click.Context, template_name:str) -> None:
    """
    Creates a new template.
    """
    template_path = os.path.expanduser(ctx.obj["config"]["template_path"])

    if not os.path.isdir(template_path):
        os.mkdir(template_path)
        logging.debug(f"Created template directory at {template_path}.")
    
    template_file = os.path.join(template_path, template_name)
    if os.path.isfile(template_file):
        logging.error(f"Template {template_name} already exists.")
        return
    
    try:
        editor = ctx.obj["config"]["editor"]
    except:
        editor = "nano"

    template = writer(editor)
    with open(template_file, "w") as f:
        f.write(template)
        logging.debug(f"Created template {template_name}.")

@cli.command()
@click.argument("template_name")
@click.pass_context
def edit_template(ctx: click.Context, template_name:str) -> None:
    """
    Creates a new template.
    """
    template_path = os.path.expanduser(ctx.obj["config"]["template_path"])

    if not os.path.isdir(template_path):
        os.mkdir(template_path)
        logging.debug(f"Created template directory at {template_path}.")
    
    template_file = os.path.join(template_path, template_name)
    if not os.path.isfile(template_file):
        logging.error(f"Template {template_name} doesn't exist. Please use the create-template command to create it.")
        return
    
    try:
        editor = ctx.obj["config"]["editor"]
    except:
        editor = "nano"

    subprocess.run([editor, template_file])

@cli.command()
@click.argument("template_name")
@click.pass_context
def delete_template(ctx: click.Context, template_name:str) -> None:
    """
    Deletes a template.
    """
    template_path = os.path.expanduser(ctx.obj["config"]["template_path"])
    template_file = os.path.join(template_path, template_name)

    if not os.path.isfile(template_file):
        logging.error(f"Template {template_name} doesn't exist.")
        return

    # Confirm deletion
    if click.confirm(f"Are you sure you want to delete the template {template_name}?", abort=True):
        os.remove(template_file)

    logging.debug(f"Deleted template {template_name}.")

if __name__ == "__main__":
    config = Config("../config.json")
    
    path = os.path.expanduser(config.config["path"])
 
    if not os.path.isdir(path):
        os.mkdir(path)
        logging.debug(f"Created project directory at {config.config['path']}.")

    cli(obj={})

