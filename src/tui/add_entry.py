import npyscreen
import datetime

class AddEntryForm(npyscreen.FormBaseNewWithMenus, npyscreen.SplitForm):
    def create(self):
        self.name = 'Add Entry'
        self.project = None
        self.date = None
        self.add_button = self.add(npyscreen.ButtonPress, name="Add Entry")
        self.cancel_button = self.add(npyscreen.ButtonPress, name="Cancel")
        self.text = self.add(npyscreen.MultiLineEdit, slow_scroll=True, rely=7)

        self.add_button.whenPressed = self.on_add
        self.cancel_button.whenPressed = self.on_cancel

    def beforeEditing(self):
        self.date = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S")


    def on_add(self):
        entry_body = self.text.value
        npyscreen.notify_confirm(f"Adding entry: {self.date} - {entry_body}")
        # Add entry
        self.parentApp.switchFormPrevious()

    def on_cancel(self):
        self.parentApp.switchFormPrevious()