import logging
from datetime import datetime
from collections import defaultdict
from typing import List, Optional
import os

# Get a logger for this module
logger = logging.getLogger(__name__)

class LogEntry:

    def __init__(self, date: datetime = None, log: str = None) -> None:
        self.date = date
        self.log = log

    def set_date(self, date: datetime) -> None:
        self.date = date

    def set_log(self, log: str) -> None:
        self.log = log

    def append_log(self, log: str) -> None:
        self.log += log

    # Returns a string representation of the object. To be used 
    # when printing or writing the object to the file.
    def __repr__(self) -> str:
        return f"<LogEntry: {self.date} - {self.log}>"
    
    def from_string(self, log: str) -> None:
        date, log = log.split(" - ")
        self.date = datetime.strptime(date[1:-1], "%Y-%m-%d %H:%M:%S")
        self.log = log

    def to_string(self) -> str:
        return f"[{self.date}] - {self.log}"

class SplitError(Exception):
    pass

# Class that produces a data structure to store log entries.
#   - The structure should allow search both in text as in date.
class LogVector:

    def __init__(self, **kwargs) -> None:
        self.logs: List[LogEntry] = []
        logger.debug(f"Initalized LogVector with {len(self.logs)} logs.")

    def load_logs(self, logs: list[LogEntry]) -> None:
        for log in logs:
            self.append(log)

        logger.debug(f"Loaded {len(logs)} logs into LogVector.")

    def append(self, log: LogEntry) -> None:
        self.logs.append(log)
        logger.debug(f"Appended log: {log}")
    
    def search_by_date(self, date: datetime) -> LogEntry:
        log = self.logs.get(date)
        logger.debug(f"Searching for log on date {date}. Found: {log}")
        return log
    
    def search_by_text(self, text: str) -> LogEntry:
        all_entries = [log for log in self.logs.values() if text in log.log]
        logger.debug(f"Searching for logs containing text: {text}. Found: {all_entries}")
        return all_entries

    def split(self, n: int) -> List["LogVector"]:
        """
        Splits the LogVector into 2 LogVectors, where the first has size n, and the second has the remaining logs.
        """
        if len(self.logs) <= n:
            logger.error("LogVector has less logs than the split size.")
            raise SplitError("LogVector has less logs than the split size.")

        logs = list(self.logs.items())
        logVec1, logVec2 = LogVector(logs[:n]), LogVector(logs[n:])
        logger.debug(f"Split LogVector into two LogVectors. LogVector 1 has {len(logVec1)} logs. LogVector 2 has {len(logVec2)} logs.")
        return [logVec1, logVec2]

    def __repr__(self) -> str:
        return f"<LogVector: {len(self.logs)} logs>"
        # return "\n".join([str(log) for log in self.logs.items()])
    
    def __len__(self) -> int:
        return len(self.logs)
    
    def __iter__(self):
        return iter(self.logs)

    
# Class that handles all the log segmentation process.
#  - The class should be able to read the log file, and if the number
#    of log entries exceeds a certain limit, it should create a new log
# 
class LogSegmentation:

    def __init__(self, log_limit: int, project_path: str) -> None:
        self.log_limit = log_limit
        self.project_path = project_path
        self.current_log_file = self.last_log_file()

    def set_curr_log_file(self, log_file: str) -> None:
        self.current_log_file = log_file

    def segment_logs(self, logs: LogVector) -> Optional[LogVector]:
        """
        Checks if the new LogVector is larger than the log limit.
        If it is, it splits the logs into a new log file.
        """
        if len(logs) >= int(self.log_limit):
            prev_logs, new_logs = new_logs.split(self.log_limit)
            return prev_logs, new_logs
        else:
            logger.debug("Log limit not reached. Appending to current log file.")
            return logs
    
    def generate_file_name(self) -> str:
        """
        Generates the name for the next log file. The name is based on the last log file number.
        Log file names are in the format log_{number}.txt. The number is the last log file number + 1.
        Note: If there are no log files, the function will return log_1.txt.
        File names are incremented by 1, to improve user readability.
        """
        logger.debug("Generating new log file name...")
        logger.debug(f"Current log file: {self.current_log_file}")
        number = int(self.current_log_file.split("_")[1].split(".")[0]) + 1 if self.current_log_file else 1
        logger.debug(f"Generated new log file name: log_{number}.txt")
        self.set_curr_log_file(f"log_{number}.txt")
        return f"log_{number}.txt"
    
    def last_log_file(self) -> Optional[str]:
        """
        Returns the last log file in the project path. If there are no log files, returns None.
        """
        log_files = [file for file in os.listdir(self.project_path) if file.startswith("log")]
        if log_files:
            return sorted(log_files)[-1]
        return None

# Class that reads the log file and returns a list of LogEntry objects.
#   - The class should be able to read the log file and return a list of
class LogReader:

    def __init__(self, log_project: str, log_limit: int) -> None:
        logger.debug(f"Initialized LogReader for project: {log_project}")
        self.project = log_project
        self.seg = LogSegmentation(log_limit, log_project)
    
    def read_logs(self, path: str) -> LogVector:
        logs = LogVector()
        logger.debug(f"Reading logs from file: {path}")

        if not path or not os.path.exists(os.path.join(self.seg.project_path,path)): 
            logger.debug("Log file not found.")
            return logs
        else:
            logger.debug(f"Reading logs from file: {path}")
            path = os.path.join(self.seg.project_path, path)
            with open(path, "r") as file:
                curr_log = ""
                inside_log = False
                
                for line in file:
                    # If we hit a separator, it means the current log ends
                    if line.strip() == "--------------------":
                        if curr_log:
                            logs.append(curr_log)
                        inside_log = False
                    elif line.startswith("[") and not inside_log:
                        # Match the timestamp line, expecting the format [YYYY-MM-DD HH:MM:SS] - log title
                        curr_log = LogEntry()
                        curr_log.from_string(line)
                        inside_log = True
                    elif inside_log:
                        # Continue capturing log content (including line breaks)
                        curr_log.append_log(line)
            logger.debug(f"Read {len(logs)} logs from file.")
            return logs
    
    def write_logs(self, logs: LogVector) -> None:
        logger.debug(f"Writing {len(logs)} logs to file.")

        last_log_file = self.seg.current_log_file if self.seg.current_log_file else self.seg.last_log_file()        
        logger.debug(f"Last log file: {last_log_file}")

        curr_logs = self.read_logs(last_log_file) if last_log_file else LogVector()
        logger.debug(f"Current Logs: {curr_logs}")

        # check number of logs in the current log file
        if len(curr_logs) >= self.seg.log_limit:
            new_log_file = self.seg.generate_file_name()
            new_path = os.path.join(self.seg.project_path, new_log_file)

            for log in logs:
                self.write_log(new_path, log)
 
        else:
            if not last_log_file:
                last_log_file = self.seg.generate_file_name()
            
            path = os.path.join(self.seg.project_path, last_log_file)
            for log in logs:
                self.write_log(path, log)
        
    def write_log(self, file_path:str, log: LogEntry) -> None:
        with open(file_path, "a") as file:
            file.write(log.to_string())
            file.write("\n")
            file.write("--------------------\n")
        logger.debug(f"Wrote log to file.")