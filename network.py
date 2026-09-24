"""Le plateau : la grille de nodes et les segments qui les relient (features 3 et 12)."""

from collections import deque

from models import Node, NodeType, Segment


class RoadNetwork:
    """Grille de columns x rows nodes, rangée dans une liste plate colonne par colonne."""

    def __init__(self, columns: int, rows: int):
        if not isinstance(columns, int) or not isinstance(rows, int) or columns < 2 or rows < 1:
            raise ValueError(f"grille invalide {columns}x{rows} : il faut columns >= 2 "
                             "(START et END séparés) et rows >= 1")
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

    def get_start(self) -> Node | None:
        """Renvoie le node START, ou None s'il n'y en a pas."""
        for node in self.nodes:
            if node.type is NodeType.START:
                return node
        return None

    def get_shortest_path(self) -> list[Node]:
        """Plus court chemin START -> END en nombre de segments (parcours en largeur, BFS)."""
        start = self.get_start()
        if start is None:
            return []
        queue = deque([start])
        parents = {start: None}  # node -> node d'où on vient ; sert aussi de "déjà visités"
        while queue:
            node = queue.popleft()
            if node.type is NodeType.END:
                return self.build_path(parents, node)
            for segment in node.segments:
                neighbor = segment.end if segment.start is node else segment.start
                if neighbor not in parents:
                    parents[neighbor] = node
                    queue.append(neighbor)
        return []

    def build_path(self, parents: dict, end: Node) -> list[Node]:
        """Remonte les parents depuis END pour reconstruire le chemin START -> END."""
        path = []
        node = end
        while node is not None:
            path.append(node)
            node = parents[node]
        path.reverse()
        return path
