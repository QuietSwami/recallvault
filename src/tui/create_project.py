import npyscreen
from src import log

class CreateProjectForm(npyscreen.FormBaseNew):
    def create(self):
        self.name = 'Create Project'
        self.project_name = self.add(npyscreen.TitleText, name="Project Name")
        self.project_description = self.add(npyscreen.TitleText, name="Project Description")
        self.create_button = self.add(npyscreen.ButtonPress, name="Create Project")
        self.cancel_button = self.add(npyscreen.ButtonPress, name="Cancel")

        self.create_button.whenPressed = self.on_create
        self.cancel_button.whenPressed = self.on_cancel

    def on_create(self):
        project_name = self.project_name.value
        project_description = self.project_description.value

        # Create project
        log.create_project(project_name, project_description)
    
        self.parentApp.switchFormPrevious()
    
    def on_cancel(self):
        self.parentApp.switchFormPrevious()
    
    