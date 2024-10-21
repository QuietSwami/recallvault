import npyscreen

class ListTodosForm(npyscreen.FormBaseNew):
    def create(self):
        self.name = 'List Todos'
        self.todos = self.add(npyscreen.MultiLineAction, name="Todos", max_height=20)
        self.todos.values = ['Todo 1', 'Todo 2', 'Todo 3']
        self.todos.action = self.on_todo_selected

    def on_todo_selected(self, widget, selected_todo):
        self.parentApp.switchFormPrevious()