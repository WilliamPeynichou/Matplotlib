"""Les briques du réseau : types de node, Node et Segment (feature 2)."""

from enum import Enum


class NodeType(Enum):
    """Les types possibles d'un node de la grille."""

    UNUSED = 0
    START = 1
    END = 2
    CONNECTION = 3
    INTERSECTION = 4


class Node:
    """Une position de la grille, reliée à d'autres nodes par des segments."""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.type = NodeType.UNUSED
        self.segments = []  # créée ici : une liste propre à chaque node

    def update_type(self) -> None:
        """Recalcule le type selon le nombre de segments (START et END ne changent jamais)."""
        if self.type in (NodeType.START, NodeType.END):
            return
        count = len(self.segments)
        if count == 0:
            self.type = NodeType.UNUSED
        elif count <= 2:
            self.type = NodeType.CONNECTION
        else:
            self.type = NodeType.INTERSECTION

    def __repr__(self) -> str:
        return f"Node({self.x}, {self.y}, {self.type.name})"


class Segment:
    """Un tronçon de route entre deux nodes."""

    def __init__(self, start: Node, end: Node):
        self.start = start
        self.end = end

    def __repr__(self) -> str:
        return f"Segment({self.start.x},{self.start.y} -> {self.end.x},{self.end.y})"
