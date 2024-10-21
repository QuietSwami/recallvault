import npyscreen

class MainMenu(npyscreen.FormBaseNew):
    def create(self):
        self.name = 'RecallVault'
        self.create_project_button = self.add(npyscreen.ButtonPress, name="Create Project")
        self.list_projects_button = self.add(npyscreen.ButtonPress, name="List Projects")
        self.add_entry_button = self.add(npyscreen.ButtonPress, name="Add Entry")
        self.list_entries_button = self.add(npyscreen.ButtonPress, name="List Entries")
        self.list_todos_button = self.add(npyscreen.ButtonPress, name="List Todos")

        self.create_project_button.whenPressed = self.on_create_project
        self.list_projects_button.whenPressed = self.on_list_projects
        self.list_entries_button.whenPressed = self.on_list_entries
        self.add_entry_button.whenPressed = self.on_add_entry
        self.list_entries_button.whenPressed = self.on_list_entries
        self.list_todos_button.whenPressed = self.on_list_todos

    def on_create_project(self):
        self.parentApp.switchForm('CREATE_PROJECT')

    def on_list_projects(self):
        self.parentApp.switchForm('LIST_PROJECTS')

    def on_add_entry(self):
        self.parentApp.switchForm('ADD_ENTRY')

    def on_list_entries(self):
        self.parentApp.switchForm('LIST_ENTRIES')

    def on_list_todos(self):
        self.parentApp.switchForm('LIST_TODOS')