"""Le plateau : la grille de nodes et les segments qui les relient (feature 3)."""

from models import Node, NodeType, Segment


class RoadNetwork:
    """Grille de columns x rows nodes, rangée dans une liste plate colonne par colonne."""

    def __init__(self, columns: int, rows: int):
        self.columns = columns
        self.rows = rows
        self.nodes = []
        self.segments = []  # dans l'ordre de création (sert à l'animation)
        for x in range(columns):
            for y in range(rows):
                self.create_node(x, y)

    def create_node(self, x: int, y: int) -> Node:
        """Crée un node UNUSED et l'ajoute à la grille."""
        node = Node(x, y)
        self.nodes.append(node)
        return node

    def is_inside(self, x: int, y: int) -> bool:
        """Vrai si la position (x, y) est dans la grille."""
        return 0 <= x < self.columns and 0 <= y < self.rows

    def get_node(self, x: int, y: int) -> Node | None:
        """Renvoie le node en (x, y), ou None si hors grille."""
        if not self.is_inside(x, y):
            return None
        return self.nodes[x * self.rows + y]

    def has_segment(self, a: Node, b: Node) -> bool:
        """Vrai si a et b sont déjà reliés directement."""
        for segment in a.segments:
            if segment.start is b or segment.end is b:
                return True
        return False

    def create_segment(self, a: Node, b: Node) -> Segment | None:
        """Relie deux nodes et met à jour leurs types. None si le lien existe déjà."""
        if a is b or self.has_segment(a, b):
            return None
        segment = Segment(a, b)
        self.segments.append(segment)
        a.segments.append(segment)
        b.segments.append(segment)
        a.update_type()
        b.update_type()
        return segment

    def reset(self) -> None:
        """Supprime tous les segments et remet chaque node en UNUSED."""
        self.segments = []
        for node in self.nodes:
            node.segments = []
            node.type = NodeType.UNUSED

    def get_shortest_path(self) -> list[Node]:
        """Plus court chemin START -> END (bonus, feature 12)."""
        return []
