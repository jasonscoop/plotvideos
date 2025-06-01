import json
from pathlib import Path
from typing import Union


def save_json(path: Union[str, Path], json_data: dict):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False))
