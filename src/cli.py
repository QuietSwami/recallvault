from config import Config
from logger import LogEntry, LogVector, LogReader, LogSegmentation
import rich_click as click
from click_aliases import ClickAliasedGroup
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
import log
from typing import List, Tuple, Union, Optional


console = Console()

@click.group(cls=ClickAliasedGroup)
@click.option('--debug', is_flag=True, help="Enable debug mode.")
@click.pass_context
def cli(ctx, debug):
    """Main entry point for the project management CLI."""
    # Load the configuration at the start
    config_path = os.path.expanduser("~/.config/recallvault/config.json")
    if not os.path.isfile(config_path):
        default_config = {"path": "~/.config/recallvault", 
                        "log_limit": "145", 
                        "debug": False, 
                        "template_path": "~/.config/recallvault/templates",
                        "editor": "nano"
                        }
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
    
    config = Config(os.path.expanduser("~/.config/recallvault/config.json"))

    path = os.path.expanduser(config.config["path"])
 
    if not os.path.isdir(path):
        os.mkdir(path)
        logging.debug(f"Created project directory at {config.config['path']}.")

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
    
@cli.command(aliases=["list", "ls"])
@click.pass_context
def list(ctx: click.Context) -> None:
    """
    Lists all projects in the default directory.
    """
    all_projects = log.list_all_projects()

    # Create the root of the tree
    tree = Tree("[magenta]Projects:")
    
    # Dictionary to hold nodes for quick access
    node_dict = {None: tree}  # Root projects use `None` as their parent_id

    # Populate the tree with projects
    for project in all_projects:
        # Find the parent node from the dictionary or use the tree root
        parent_node = node_dict.get(project.parent_id, tree)
        
        if project.parent_id is not None:
        # Add the project to its parent node
            current_node = parent_node.add(f"[green]{project.name}[/]")
        else:
            current_node = parent_node.add(f"[blue]{project.name}[/]")
        
        # Store the current node in the dictionary so it can be used as a parent
        node_dict[project.id] = current_node

    # Print the tree to the console
    console.print(tree)
    

@cli.command(aliases=["create", "c"])
@click.argument("name", type=str, required=True)
@click.pass_context
def create(ctx: click.Context, name: str) -> None:
    """
    Create a new project or subproject.
    """
    project, subproject = name.split("/") if "/" in name else (name, None)
    if subproject:
        # First get the parent ID, then pass the name of the subproject and the parent ID. 
        parent_id = log.get_project_id(project)
        if parent_id is None:
            return
        print(f"Creating subproject: {subproject} under {project}")
        log.create_project(subproject, parent_id)
    else:
        print(f"Creating project: {name} ")
        log.create_project(name)

@cli.command(aliases=["delete", "del", "d"])
@click.argument("name", type=str, required=True)
@click.pass_context
def delete(ctx: click.Context, name: str) -> None:
    """
    Delete a project or subproject.
    """
    project, subproject = name.split("/") if "/" in name else (name, None)
    if subproject:
        project_id = log.get_project_id(subproject)
    else:
        project_id = log.get_project_id(project)

    log.delete_project(project_id)


@cli.command(aliases=["archive", "a", "arc"])
@click.argument("name", type=str, required=True)
@click.pass_context
def archive(ctx: click.Context, name: str) -> None:
    """
    Archive a project.
    """
    project_id = log.get_project_id(name)
    log.archive_project(project_id)

@cli.command(aliases=["unarchive", "ua", "unarc"])
@click.argument("name", type=str, required=True)
@click.pass_context
def unarchive(ctx: click.Context, name: str) -> None:
    """
    Unarchive a project.
    """
    project_id = log.get_project_id(name)
    log.unarchive_project(project_id)
    
def writer(editor, content: str = None, template: str = None) -> str:
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        tmp_file_name = f.name
        logging.debug(f"Created temporary file {tmp_file_name}.")

        # If content is provided, write it to the temporary file
        if content:
            f.write(content)
        # If template is provided (and content is not), copy it to the temporary file
        elif template:
            with open(template, 'r') as template_file:
                shutil.copyfileobj(template_file, f)

    # Open the editor with the temporary file
    subprocess.run([editor, tmp_file_name])

    logging.debug(f"Opened editor {editor} for temporary file {tmp_file_name}.")
    with open(tmp_file_name, "r") as f:
        text = f.read().strip()
        logging.debug(f"Read log from temporary file: {text}")

    os.remove(tmp_file_name)
    return text

def string_to_date(text: str) -> Optional[datetime]:
    """
    Converts a date or datetime string to a datetime object.
    Accepts formats like "YYYY-MM-DD", "YYYY-MM-DD HH:MM", and "YYYY-MM-DD HH:MM:SS".
    
    Parameters:
    - text: The input date or datetime string.

    Returns:
    - A datetime object representing the input string, or raises ValueError if the format is invalid.
    """
    date_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d %H:%M:%S"
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    
    # If none of the formats matched, raise an error
    return None

def date_to_string(date: Optional[datetime]) -> Optional[str]:
    """
    Converts a datetime object to a string in the format "YYYY-MM-DD HH:MM:SS".
    
    Parameters:
    - date: The input datetime object.

    Returns:
    - A string representing the input datetime, or None if the input is None.
    """
    return date.strftime("%Y-%m-%d") if date else None

def separator(text: str) -> str:
    """
    Separates log content from the todos in the text.
    
    Parameters:
    - text: The input text containing log content and todos.

    Returns:
    - A string containing only the log content, separated from the todos.
    """
    # Define a pattern to match todos (e.g., lines starting with [ ] or [x])
    todo_pattern = re.compile(r"(^\[( |x)\] .+)", re.MULTILINE)

    if match := todo_pattern.search(text):
        # Return everything before the first todo
        return text[:match.start()].strip()
    else:
        # If no todos are found, return the entire text as log content
        return text.strip()

def clean_description(description: str) -> str:
    """Removes any occurrences of 'due:' or 'on:' and their values from the description."""
    return re.sub(r"\s*(due:\S+|on:\S+)", "", description).strip()

def todo_extractor(text: str, edit: bool = False) -> Union[
    List[Tuple[int, bool, str, Optional[datetime], Optional[str]]],
    List[Tuple[str, str, Optional[datetime], Optional[str]]]
]:
    """
    Extracts todo information from edited text with optional due date and location fields.

    Parameters:
    - text (str): The input text with markdown-style todos.
    - edit (bool): If True, returns a detailed format with todo ID; otherwise, a simpler format.

    Returns:
    - List of tuples with extracted fields:
    - edit=True: (id, completed, description, due_date, location)
    - edit=False: (status, description, due_date, location)
    """
    # Unified regex pattern for todos with optional due date and location
    pattern = r"\[( |x)\] (?:(\d+): )?(.+?)(?=\s+due:|\s+on:|$)(?: due:(\d{4}-\d{2}-\d{2}))?(?: on:(.+?))?$"
    
    matches = re.findall(pattern, text, re.MULTILINE)
    extracted_todos = []
    
    for match in matches:
        status, todo_id, description, due_date, location = match
        completed = status == "x"
        due_date_converted = string_to_date(due_date.strip()) if due_date else None
        location_cleaned = location.strip() if location else None
        
        # Clean the description to remove any "due:" or "on:" remnants
        cleaned_description = clean_description(description)

        # Conditional tuple construction based on `edit` flag
        if edit:
            extracted_todos.append(
                (int(todo_id) if todo_id else None, completed, cleaned_description, due_date_converted, location_cleaned)
            )
        else:
            extracted_todos.append(
                (status, cleaned_description, due_date_converted, location_cleaned)
            )
    
    return extracted_todos
    
@cli.command(aliases=["entry", "e"])
@click.argument("name", type=str, required=True)
@click.option("--template", type=str, help="Use a template for the log entry.")
@click.pass_context
def entry(ctx:click.Context, name: str, template: str) -> None:
    """
    Create a new log entry for a project.
    """
    project, subproject = name.split("/") if "/" in name else (name, None)
    try:
        editor = ctx.obj["config"]["editor"]
    except Exception:
        editor = "nano"

    sel_project = subproject or project

    template_path = None

    if template:
        template_path = os.path.join(os.path.expanduser(ctx.obj["config"]["template_path"]), template)
        if not os.path.isfile(template_path):
            logging.error(f"Template {template} does not exist.")
            return

    log_entry = writer(editor, template_path)

    todos = todo_extractor(log_entry)
    if log:
        project_id = log.get_project_id(sel_project)
        log_id = log.add_log_to_project(project_id, separator(log_entry))
        if todos:
            for todo in todos:
                log.add_todo_to_log(log_id, todo[0] == "x", todo[1], todo[2])
    else:
        print("Please provide a log entry for the project.")


# Todo commands

@cli.command(aliases=["todo-list", "tl"])
@click.argument("name", type=str, required=False)
@click.pass_context
def todo_list(ctx: click.Context, name: str) -> None:
    """
    List all todos for a project or all projects if no project is specified.
    """
    # Split the project name into project and subproject if provided
    project, subproject = (name.split("/") + [None])[:2] if name else (None, None)

    # Get todos for the specified project or all todos if no project is specified
    todos = log.get_all_todos_from_project(log.get_project_id(subproject or project)) if name else log.get_all_todos()

    if todos:
        # Group todos by project
        grouped_todos = {}
        for todo in todos:
            project_name = log.get_project_name_from_log(todo.log_id)  # Assuming each `todo` has an associated `project_name`
            if project_name not in grouped_todos:
                grouped_todos[project_name] = []
            grouped_todos[project_name].append(todo)

        # Print todos by project with delimiters
        for project_name, project_todos in grouped_todos.items():
            click.echo(f"\nProject: {project_name}")
            click.echo("-" * 30)  # Delimiter line
            for todo in project_todos:
                status = "[x]:" if todo.completed else "[ ]:"
                status = status + str(todo.id) if todo.id else status
                status = f"{status} {todo.description}"
                status = (
                    f"{status} due:{date_to_string(todo.due_date)}"
                    if todo.due_date
                    else status
                )
                click.echo(status)
            click.echo("=" * 30)  # End of project delimiter
    else:
        click.echo("No todos found.")


@cli.command(aliases=["todo-edit", "te"])
@click.argument("name", type=str, required=False)
@click.pass_context
def todo_edit(ctx: click.Context, name: str) -> None:
    # Split name into project and subproject
    project, subproject = (name.split("/") + [None])[:2] if name else (None, None)
    
    # Get all todos for the specified project or all if no project specified
    todos = log.get_all_todos_from_project(log.get_project_id(subproject or project)) if name else log.get_all_todos()
    if todos:
        edit_content = ""
        
        # Format each todo with its id and status
        for todo in todos:
            status = "[x]" if todo.completed else "[ ]"
            edit_content += f"{status} {todo.id}: {todo.description}"
            edit_content += f" due:{date_to_string(todo.due_date)}" if todo.due_date else ""
            edit_content += "\n"
        
        # Open the temporary editor and capture the edited content
        editor = ctx.obj["config"]["editor"]
        edited_content = writer(editor, edit_content)
        
        print(edited_content)
        
        # Parse the edited content to extract ids, statuses, and descriptions
        edited_todos = todo_extractor(edited_content, edit=True)
        print(edited_todos)
        # Update each todo in the database based on parsed content
        for edited_todo in edited_todos:
            todo_id, completed, description, due_date, location = edited_todo
            log.update_todo_status(todo_id, completed, description, due_date)
    else:
        click.echo("No todos found for the project.")

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
    log_text.append("\n")

    keyword_pattern = re.compile(r"\b(\w+):(?=\S)(\S+)")
    last_index = 0
    for match in keyword_pattern.finditer(log.log):
        # Append text before the match
        if match.start() > last_index:
            log_text.append(log.log[last_index:match.start()], style="white")
        # Append the matched keyword and the colon in light green
        log_text.append(f"{match.group(1)}:{match.group(2)}", style="light_green")
        last_index = match.end()

    # Append the rest of the log after the last match
    if last_index < len(log.log):
        log_text.append(log.log[last_index:], style="white")
    console.print(log_text)

@cli.command(aliases=["entry-print", "p"])
@click.argument("name", type=str, required=True)
@click.option("--depth", type=int, default=1, help="The number of log to print.")
@click.pass_context
def entry_print(ctx: click.Context, name: str, depth: int) -> None:
    """
    Print the log entries for a project.
    """
    project, subproject = name.split("/") if "/" in name else (name, None)
    project_name = subproject or project
    project_id = log.get_project_id(subproject or project)
    logs = log.get_logs_from_project(project_id, depth)
    reversed_logs = logs[::-1] # Reverse the logs to print the most recent first
    for log_entry in reversed_logs:
        log_printer(project_name, log_entry)
        click.echo("-" * 30)

# Template commands

@cli.command(aliases=["template-list", "tls"])
@click.pass_context
def template_list(ctx: click.Context) -> None:
    """
    List all available templates.
    """
    template_path = os.path.expanduser(ctx.obj["config"]["template_path"])
    if not os.path.isdir(template_path):
        logging.error(f"Template directory {template_path} does not exist.")
        return

    templates = os.listdir(template_path)
    for template in templates:
        click.echo(template)
        
@cli.command(aliases=["new-template", "nt"])
@click.argument("name", type=str, required=True)
@click.pass_context
def new_template(ctx: click.Context, name: str) -> None:
    """
    Create a new template.
    """
    editor = ctx.obj["config"]["editor"]
    template_path = os.path.expanduser(ctx.obj["config"]["template_path"])
    if not os.path.isdir(template_path):
        os.mkdir(template_path)
        logging.debug(f"Created template directory at {template_path}.")

    template_file = os.path.join(template_path, name)
    if os.path.isfile(template_file):
        logging.error(f"Template {name} already exists.")
        return

    log_entry = writer(editor)
    with open(template_file, "w") as f:
        f.write(log_entry)
        
@cli.command(aliases=["edit-template", "et"])
@click.argument("name", type=str, required=True)
@click.pass_context
def edit_template(ctx: click.Context, name: str) -> None:
    """
    Edit an existing template.
    """
    editor = ctx.obj["config"]["editor"]
    template_path = os.path.expanduser(ctx.obj["config"]["template_path"])
    template_file = os.path.join(template_path, name)
    if not os.path.isfile(template_file):
        logging.error(f"Template {name} does not exist.")
        return

    log_entry = writer(editor, template_file)
    with open(template_file, "w") as f:
        f.write(log_entry)
        
@cli.command(aliases=["delete-template", "dt"])
@click.argument("name", type=str, required=True)
@click.pass_context
def delete_template(ctx: click.Context, name: str) -> None:
    """
    Delete a template.
    """
    template_path = os.path.expanduser(ctx.obj["config"]["template_path"])
    template_file = os.path.join(template_path, name)
    if not os.path.isfile(template_file):
        logging.error(f"Template {name} does not exist.")
        return

    os.remove(template_file)
    logging.debug(f"Deleted template {name}.")


if __name__ == "__main__":
    cli()