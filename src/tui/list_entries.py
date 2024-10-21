import npyscreen

class ListEntriesForm(npyscreen.FormBaseNew):
    def create(self):
        self.name = 'List Entries'
        self.entries = self.add(npyscreen.MultiLineAction, name="Entries", max_height=20)
        self.entries.values = ['Entry 1', 'Entry 2', 'Entry 3']
        self.entries.action = self.on_entry_selected

    def on_entry_selected(self, widget, selected_entry):
        self.parentApp.switchFormPrevious()
