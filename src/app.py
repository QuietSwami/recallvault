import npyscreen
from tui.main_menu import MainMenu
from tui.create_project import CreateProjectForm
from tui.add_entry import AddEntryForm
from tui.list_entries import ListEntriesForm
from tui.list_todos import ListTodosForm
from tui.list_project import ListProjectsForm
import logging

# Configure the logger
logging.basicConfig(
    filename='app.log',    # Specify the log file
    level=logging.DEBUG,    # Set log level (DEBUG, INFO, WARNING, etc.)
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MyApp(npyscreen.NPSAppManaged):
    def onStart(self):
        # Register forms
        self.addForm('MAIN', MainMenu)
        self.addForm('CREATE_PROJECT', CreateProjectForm)
        self.addForm('LIST_PROJECTS', ListProjectsForm)
        self.addForm('ADD_ENTRY', AddEntryForm)
        self.addForm('LIST_ENTRIES', ListEntriesForm)
        self.addForm('LIST_TODOS', ListTodosForm)

if __name__ == '__main__':
    MyApp().run()