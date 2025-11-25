import yaml
import os

def load_config(config_path: str = "config/config.yml") -> dict:
    """Loads the YAML configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at: {config_path}")
    
    with open(config_path, "r") as f:
        try:
            config = yaml.safe_load(f)
            return config
        except yaml.YAMLError as exc:
            raise RuntimeError(f"Error parsing YAML: {exc}")