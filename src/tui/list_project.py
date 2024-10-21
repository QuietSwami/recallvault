import npyscreen
from src import log
import logging

# Configure the logger from app.py


class ListProjectsForm(npyscreen.FormBaseNew):
    def create(self):
        self.name = 'List Projects'
        self.all_project = log.list_all_projects()

        # Add the project list (first column)
        self.projects = self.add(npyscreen.MultiLineAction, name="Projects", max_height=20, relx=2, rely=2)
        self.projects.values = [x.name for x in self.all_project]
        self.projects.actionHighlighted = self.on_project_selected

        # Add a second column for the actions (menu)
        self.actions_menu = self.add(npyscreen.MultiLineAction, name="Actions", max_height=20, relx=40, rely=2)
        self.actions_menu.values = ["Select a project to see actions"]
        self.actions_menu.actionHighlighted = self.on_action_selected  # Ensure this is set

    def on_project_selected(self, project_name, keypress):
        logging.debug(f"Project selected: {project_name}")
        if selected_project := next(
            (p for p in self.all_project if p.name == project_name), None
        ):
            self.update_action_menu(selected_project)
            logging.info(f"Displaying action menu for {selected_project.name}")
        else:
            npyscreen.notify_confirm("Project not found", title="Error")
            logging.error(f"Project not found: {project_name}")

    def update_action_menu(self, project):
        """
        Updates the action menu (second column) with actions for the selected project.
        """
        logging.debug(f"Updating action menu for project: {project.name}")
        self.selected_project = project
        self.actions_menu.values = [
            "Add Entry",
            "Edit Project",
            "Delete Project"
        ]
        self.actions_menu.display()  # Refresh the display

    def on_action_selected(self, action, keypress):
        """
        Handles the action when a menu item is selected from the second column.
        """
        logging.debug(f"Action selected: {action}")
        if action == "Add Entry":
            self.add_entry(self.selected_project)
        elif action == "Edit Project":
            self.edit_project(self.selected_project)
        elif action == "Delete Project":
            self.delete_project(self.selected_project)

    def add_entry(self, project):
        self._switch_to_page(
            'Adding entry to project: ', project, 'ADD_ENTRY'
        )

    def edit_project(self, project):
        self._switch_to_page(
            'Editing project: ', project, 'EDIT_PROJECT'
        )

    def delete_project(self, project):
        self._switch_to_page(
            'Deleting project: ', project, 'DELETE_PROJECT'
        )

    def _switch_to_page(self, arg0, project, arg2):
        logging.debug(f"{arg0}{project.name}")
        self.parentApp.getForm(arg2).value = project
        self.parentApp.switchForm(arg2)
