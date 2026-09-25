"""Le circuit : 4 grilles (cadres) reliées en boucle.

    Cadre 0 : Gauche -> Haut      Cadre 1 : Haut -> Droite
    Cadre 3 : Bas -> Gauche       Cadre 2 : Droite -> Bas

Chaque cadre est un RoadNetwork normal (mêmes règles, mêmes tests). Son END est la jonction
avec le START du cadre suivant : le END du cadre 3 ramène au START du cadre 0 = un tour.
Chaque cadre garde ses coordonnées locales (x, y) ; to_screen() les place sur l'écran,
le long d'un arc d'ellipse entre deux jonctions.
"""

import math

from generator import generate_network
from models import Node, NodeType
from network import RoadNetwork

FRAMES = 4
WIDTH = 1.4  # l'ellipse est plus large que haute (comme le dessin)


class Circuit:
    """4 RoadNetwork en boucle. Se comporte comme un RoadNetwork pour l'affichage et le trafic."""

    def __init__(self, columns: int, rows: int):
        if not isinstance(columns, int) or columns < 3:
            raise ValueError(f"cadre invalide {columns}x{rows} : il faut columns >= 3")
        self.columns = columns
        self.rows = rows
        self.frames = [RoadNetwork(columns, rows) for _ in range(FRAMES)]
        for index, frame in enumerate(self.frames):
            for node in frame.nodes:
                node.frame = index
        self.radius = 2 * (columns - 1) / math.pi  # quart d'ellipse ≈ longueur d'un cadre

    @property
    def nodes(self) -> list[Node]:
        """Tous les nodes des 4 cadres."""
        return [node for frame in self.frames for node in frame.nodes]

    @property
    def segments(self) -> list:
        """Tous les segments, cadre par cadre (ordre de construction)."""
        return [segment for frame in self.frames for segment in frame.segments]

    def generate(self, seed: int, roads: int, intersections: int) -> int:
        """Génère les 4 cadres (seed différente par cadre). Les intersections visées sont
        réparties entre les cadres. Renvoie le total obtenu."""
        total = 0
        for index, frame in enumerate(self.frames):
            share = intersections // FRAMES + (1 if index < intersections % FRAMES else 0)
            total += generate_network(frame, seed * FRAMES + index, roads, share,
                                      fixed_end=True)
        return total

    def get_start(self) -> Node | None:
        """START du cadre 0 = ligne de départ du circuit."""
        return self.frames[0].get_start()

    def get_next_start(self, end: Node) -> Node | None:
        """END d'un cadre -> START du cadre suivant."""
        return self.frames[(end.frame + 1) % FRAMES].get_start()

    def get_shortest_path(self) -> list[Node]:
        """Plus court tour : les plus courts chemins des 4 cadres bout à bout."""
        return [node for frame in self.frames for node in frame.get_shortest_path()]

    def get_shortest_path_length(self) -> int:
        """Longueur du plus court tour, en segments."""
        return sum(frame.get_shortest_path_length() for frame in self.frames)

    def get_bounds(self) -> tuple[float, float, float, float]:
        """(xmin, xmax, ymin, ymax) de l'écran."""
        margin = self.rows // 2 + 1
        return (-WIDTH * self.radius - margin, WIDTH * self.radius + margin,
                -self.radius - margin, self.radius + margin)

    def to_screen(self, frame: int, x: float, y: float) -> tuple[float, float]:
        """Coordonnées locales d'un cadre -> position à l'écran.
        x : avance sur l'arc (0 = jonction de départ, columns-1 = jonction d'arrivée).
        y : écart à l'arc (milieu = sur l'arc, vers l'extérieur ou l'intérieur).
        L'écart est réduit près des jonctions (sin) pour que les cadres se rejoignent."""
        t = min(1.0, max(0.0, x / (self.columns - 1)))
        angle = math.pi - (frame + t) * math.pi / 2  # tourne dans le sens des aiguilles
        offset = (y - self.rows // 2) * math.sin(math.pi * t)
        cos, sin = math.cos(angle), math.sin(angle)
        return ((WIDTH * self.radius + offset) * cos, (self.radius + offset) * sin)


def is_junction(node: Node) -> bool:
    """Vrai pour un START ou un END (point partagé par deux cadres)."""
    return node.type in (NodeType.START, NodeType.END)
