from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Tuple


@dataclass
class Theme:
    name: str
    is_dark: bool
    colors: Dict[str, str] = field(default_factory=dict)
    fonts: Dict[str, Tuple[str, int, str]] = field(default_factory=dict)
    corner_radius: int = 6

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["fonts"] = {
            k: {"family": v[0], "size": v[1], "weight": v[2] if len(v) > 2 else "normal"}
            for k, v in self.fonts.items()
        }
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Theme:
        fonts = data.pop("fonts", {})
        parsed_fonts: Dict[str, Tuple[str, int, str]] = {}
        for k, v in fonts.items():
            if isinstance(v, dict):
                parsed_fonts[k] = (v["family"], v["size"], v.get("weight", "normal"))
            elif isinstance(v, (list, tuple)):
                if len(v) >= 3:
                    parsed_fonts[k] = (v[0], v[1], v[2])
                elif len(v) == 2:
                    parsed_fonts[k] = (v[0], v[1], "normal")
            else:
                parsed_fonts[k] = ("Segoe UI", 13, "normal")
        data["fonts"] = parsed_fonts
        return cls(**data)
