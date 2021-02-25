from dataclasses import dataclass, field
from typing import List, Optional

default_empty_list = field(default_factory=lambda: [])


@dataclass
class Material:
    object: str
    material: str


@dataclass
class Model:
    id: int
    name: str
    rotation: [float]
    scale: float
    thumbnail_url: str = None
    materials: [Material] = default_empty_list
