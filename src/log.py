from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from datetime import datetime
from typing import List

Base = declarative_base()

class Project(Base):
    
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    archive = Column(Boolean, nullable=False, default=False)
    
    # Used for subprojects - if a project is a subproject, this will be the parent project's id
    parent_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    parent = relationship("Project", remote_side=[id], back_populates="subprojects")
    
    # Relationship to access subprojects
    subprojects = relationship("Project", back_populates="parent", cascade="all, delete-orphan") # The cascade="all, delete-orphan" ensures that if a parent project is deleted, all its subprojects are also deleted.
    
    # Relationship with logs
    logs = relationship("LogEntry", back_populates="project", cascade="all, delete-orphan")
        
    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name}, parent_id={self.parent_id})>"

class LogEntry(Base):
    
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, default=datetime.now)
    log = Column(String, nullable=False)
    
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    project = relationship("Project", back_populates="logs")
    
    todos = relationship("Todo", back_populates="log", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LogEntry(id={self.id}, date={self.date}, log={self.log}, project_id={self.project_id})>"
    
class Todo(Base):
    
    __tablename__ = "todos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String, nullable=False)
    completed = Column(Boolean, nullable=False, default=False)
    due_date = Column(DateTime, nullable=True)
    
    log_id = Column(Integer, ForeignKey("logs.id"), nullable=False)
    log = relationship("LogEntry", back_populates="todos")
        
    def __repr__(self):
        return f"<Todo(id={self.id}, description={self.description}, completed={self.completed})>"


# Database setup
DATABASE_URL = "sqlite:///logs.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Create tables
Base.metadata.create_all(engine)

def _create_project(session: Session, name: str, parent_id: int = None) -> None:
    parent = session.query(Project).filter_by(id=parent_id).first() if parent_id else None
    project = Project(name=name, parent=parent)
    project_id = project.id
    session.add(project)
    session.commit()
    session.close()

# Functions to interact with the database
def create_project(name: str, parent_id: int = None) -> None:
    """Create a new project or subproject."""
    session = Session()
    
    # Check if a project with the same name already exists
    if session.query(Project).filter_by(name=name).first():
        print(f"Project with name {name} already exists.")
        return
    else:
        _create_project(session, name, parent_id)  


def get_project_id(name: str) -> int:
    """Get the ID of a project by name."""
    session = Session()
    
    if project:= session.query(Project).filter_by(name=name).first():
        return project.id
    print(f"Project with name {name} not found.")
    return None


def get_subprojects(project_id: int) -> None:
    """Retrieve subprojects for a specific project."""
    session = Session()
    
    if project:= session.query(Project).filter_by(id=project_id).first():
        print(f"Subprojects for {project.name}:")
        for subproject in project.subprojects:
            print(subproject)
    else:
        print(f"Project with ID {project_id} not found.")
    
    session.close()
    
    
def add_log_to_project(project_id: int, log_text: str) -> int:
    """Add a log entry to a project.
        Returns the ID of the log entry.
    """
    session = Session()
    
    if project:= session.query(Project).filter_by(id=project_id).first():
        log = LogEntry(log=log_text, project=project)
        session.add(log)
        session.commit()
        print(f"Log added to project {project.name}.")
        return log.id
    else:
        print(f"Project with ID {project_id} not found.")
        return None

    session.close()

def update_log(log_id: int, new_text: str) -> None:
    """Update the text of a log entry."""
    session = Session()
    
    if log:= session.query(LogEntry).filter_by(id=log_id).first():
        log.log = new_text
        session.commit()
        print("Log updated.")
    else:
        print(f"Log entry with ID {log_id} not found.")
    
    session.close()


def get_logs_from_project(project_id: int, number: int) -> List[LogEntry]:
    """Returns a sorted list of logs for a specific project, ordered by date.

    Args:
        project_id (int): Project ID for which logs are to be retrieved.
        number (int): The maximum number of logs to retrieve; if 0, retrieves all logs.

    Returns:
        List[LogEntry]: A list of LogEntry objects, ordered by date.
    """
    session = Session()
    
    # Fetch the project by ID
    project = session.query(Project).filter_by(id=project_id).first()
    if not project:
        session.close()
        print(f"Project with ID {project_id} not found.")
        return []
    
    # Order logs by date in descending order (latest logs first)
    logs_query = session.query(LogEntry).filter_by(project_id=project_id).order_by(LogEntry.date.desc())
    
    # Limit the number of logs if a specific number is provided
    if number:
        logs_query = logs_query.limit(number)
    
    logs = logs_query.all()
    session.close()
    
    return logs


def add_todo_to_log(log_id: int, completed: bool, todo_description: str, due_date: DateTime = None) -> None:
    """Add a todo to a log entry."""
    session = Session()
    
    if log:= session.query(LogEntry).filter_by(id=log_id).first():
        todo = Todo(description=todo_description, log=log, completed=completed, due_date=due_date)
        session.add(todo)
        session.commit()
    else:
        print(f"Log entry with ID {log_id} not found.")
    
    session.close()
    

def update_todo_status(todo_id: int, completed: bool, todo_description: str = None, due_date: DateTime = None) -> None:
    """Update the status of a todo.

    Args:
        todo_id (int): Todo ID to be updated.
        completed (bool): New status of the todo.
    """
    session = Session()
    
    if todo:= session.query(Todo).filter_by(id=todo_id).first():
        todo.completed = completed
        todo.description = todo_description or todo.description
        todo.due_date = due_date
        session.commit()
    else:
        print(f"Todo with ID {todo_id} not found.")
    
    session.close()

def get_project_name_from_log(log_id: int) -> str:
    """Returns the name of the project for a specific log entry.

    Args:
        log_id (int): Log entry ID for which project name is to be retrieved.

    Returns:
        str: Name of the project.
    """
    session = Session()
    
    if log:= session.query(LogEntry).filter_by(id=log_id).first():
        project_name = log.project.name
        session.close()
        return project_name
    else:
        session.close()
        print(f"Log entry with ID {log_id} not found.")
        return ""

def get_todos_from_log(log_id: int) -> List[Todo]:
    """Returns all todos for a specific log entry.

    Args:
        log_id (int): Log entry ID for which todos are to be retrieved.

    Returns:
        List[Todo]: A list of Todo objects.
    """
    session = Session()
    
    if log:= session.query(LogEntry).filter_by(id=log_id).first():
        todos = log.todos
        session.close()
        return todos
    else:
        session.close()
        print(f"Log entry with ID {log_id} not found.")
        return []
    


def get_all_todos_from_project(project_id: int) -> List[Todo]:
    """Returns all todos for a specific project.

    Args:
        project_id (int): Project ID for which todos are to be retrieved.

    Returns:
        List[Todo]: A list of Todo objects.
    """
    session = Session()
    
    if session.query(Project).filter_by(id=project_id).first():
        return session.query(Todo).join(LogEntry).filter(LogEntry.project_id == project_id).all()

    session.close()
    print(f"Project with ID {project_id} not found.")
    return []


def get_all_todos() -> List[Todo]:
    """Returns all todos from the database.

    Returns:
        List[Todo]: A list of Todo objects.
    """
    session = Session()
    todos = session.query(Todo).all()
    session.close()
    return todos

def list_all_projects() -> List[Project]:
    """Returns all projects from the database.

    Returns:
        List[Project]: A list of unarchived Project objects.
    """
    session = Session()
    projects = session.query(Project).filter(Project.archive == False).all()
    session.close()
    return projects

def delete_project(project_id) -> None:
    """Delete a project and its subprojects."""
    session = Session()
    
    if project:= session.query(Project).filter_by(id=project_id).first():
        session.delete(project)
        session.commit()
        print(f"Project '{project.name}' deleted.")
    else:
        print(f"Project with ID {project_id} not found.")
    
    session.close()


def archive_project(project_id) -> None:
    """Archive a project."""
    session = Session()
    
    if project:= session.query(Project).filter_by(id=project_id).first():
        project.archive = True
        session.commit()
        print(f"Project '{project.name}' archived.")
    else:
        print(f"Project with ID {project_id} not found.")
    
    session.close()


def unarchive_project(project_id) -> None:
    """Unarchive a project."""
    session = Session()
    
    if project:= session.query(Project).filter_by(id=project_id).first():
        project.archive = False
        session.commit()
        print(f"Project '{project.name}' unarchived.")
    else:
        print(f"Project with ID {project_id} not found.")
    
    session.close()


# create_project("Main Project")
# # add_log_to_project(1, "Initial log entry for the project.")
# # add_log_to_project(4, "Initial log entry for the sub-project.")

# # create_project("Subproject 1", parent_id=1)
# # create_project("Subproject 2", parent_id=1)
# # get_subprojects(1)
# # print(get_logs_from_project(1))
# # print(get_logs_from_project(4))
# add_todo_to_log(2, "Create a new log entry.")
# add_todo_to_log(2, "Update the README file.")
# # print(get_todos_from_log(1))
# # update_todo_status(1, True)
# # print(get_todos_from_log(1))
# print(get_all_todos_from_project(1))
# print(get_all_todos())

# create_project("Test_sub", parent_id=1)
# print(list_all_projects())
# print(get_subprojects(1))