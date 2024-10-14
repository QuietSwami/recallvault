import json
import logging

logger = logging.getLogger(__name__)

class Config:

    def __init__(self, config_path: str) -> None:
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> dict:
        if not self.config_path:
            raise FileNotFoundError("Config file not found.")
        
        with open(self.config_path, "r") as f:
            return json.load(f)
        
    def save_config(self) -> None:
        if not self.config_path:
            raise FileNotFoundError("Config file not found.")
        
        with open(self.config_path, "w") as f:
            json.dump(self.config, f)

    def change(self, key: str, value: str) -> None:
        if key not in self.config:
            raise KeyError(f"Key {key} not found in config.")
            
        self.config[key] = value
        self.save_config()