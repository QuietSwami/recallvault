from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from datetime import datetime
from typing import List

Base = declarative_base()

class Project(Base):
    
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    
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
    print(f"Project created: {project}")
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
    
    
def add_log_to_project(project_id: int, log_text: str) -> None:
    """Add a log entry to a project."""
    session = Session()
    
    if project:= session.query(Project).filter_by(id=project_id).first():
        log = LogEntry(log=log_text, project=project)
        session.add(log)
        session.commit()
        print(f"Log added to project {project.name}.")
    else:
        print(f"Project with ID {project_id} not found.")
    
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


def get_logs_from_project(project_id: int) -> List[LogEntry]:
    """Returns all logs for a specific project.

    Args:
        project_id (int): Project ID for which logs are to be retrieved.

    Returns:
        List[LogEntry]: A list of LogEntry objects.
    """
    session = Session()
    
    if project:= session.query(Project).filter_by(id=project_id).first():
        logs = project.logs
        session.close()
        return logs
    else:
        session.close()
        print(f"Project with ID {project_id} not found.")
        return []
    

def add_todo_to_log(log_id: int, todo_description: str) -> None:
    """Add a todo to a log entry."""
    session = Session()
    
    if log:= session.query(LogEntry).filter_by(id=log_id).first():
        todo = Todo(description=todo_description, log=log)
        session.add(todo)
        session.commit()
        print("Todo added to log entry.")
    else:
        print(f"Log entry with ID {log_id} not found.")
    
    session.close()
    

def update_todo_status(todo_id: int, completed: bool) -> None:
    """Update the status of a todo.

    Args:
        todo_id (int): Todo ID to be updated.
        completed (bool): New status of the todo.
    """
    session = Session()
    
    if todo:= session.query(Todo).filter_by(id=todo_id).first():
        todo.completed = completed
        session.commit()
        print("Todo status updated.")
    else:
        print(f"Todo with ID {todo_id} not found.")
    
    session.close()


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
        List[Project]: A list of Project objects.
    """
    session = Session()
    projects = session.query(Project).all()
    session.close()
    return projects

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