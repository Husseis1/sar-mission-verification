from pathlib import Path

import yaml

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def example_raw(name: str = "baltic_maritime.yaml", **mission_overrides) -> dict:
    raw = yaml.safe_load((EXAMPLES / name).read_text())
    raw["mission"].update(mission_overrides)
    return raw
