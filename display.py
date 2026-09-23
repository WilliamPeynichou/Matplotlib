"""L'écran : dessin du réseau avec Matplotlib (features 4, 6, 9 et 11)."""

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from matplotlib.widgets import Button

from models import Node, NodeType, Segment
from network import RoadNetwork

COLORS = {
    NodeType.UNUSED: "#D0D4DA",
    NodeType.START: "#3CBE82",
    NodeType.END: "#E65A50",
    NodeType.CONNECTION: "#303844",
    NodeType.INTERSECTION: "#F5B83D",
}
SIZES = {
    NodeType.UNUSED: 3,
    NodeType.START: 11,
    NodeType.END: 11,
    NodeType.CONNECTION: 5,
    NodeType.INTERSECTION: 8,
}
LABELS = {
    NodeType.START: "Start",
    NodeType.END: "End",
    NodeType.CONNECTION: "Connection",
    NodeType.INTERSECTION: "Intersection",
    NodeType.UNUSED: "Unused",
}
ROAD_COLOR = "#303844"
ROAD_WIDTH = 2
PATH_COLOR = "#3C8CE6"
PATH_WIDTH = 6
CURVED_ROADS = True  # False = segments droits
CURVE_STRENGTH = 0.5  # 0 = droit, 0.5 = courbe douce
ANIMATION_INTERVAL = 60  # millisecondes entre deux segments
FIGURE_SIZE = (10, 6)


def draw_segment(ax, segment: Segment, color: str = ROAD_COLOR, width: float = ROAD_WIDTH,
                 zorder: float = 1) -> None:
    """Dessine un segment, droit ou en courbe douce (tangentes horizontales aux nodes)."""
    a, b = segment.start, segment.end
    if a.x > b.x:
        a, b = b, a  # toujours dessiner de gauche à droite
    if CURVED_ROADS and a.y != b.y:
        bend = CURVE_STRENGTH * (b.x - a.x)
        points = [(a.x, a.y), (a.x + bend, a.y), (b.x - bend, b.y), (b.x, b.y)]
        codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
        ax.add_patch(PathPatch(Path(points, codes), fill=False, edgecolor=color,
                               linewidth=width, capstyle="round", zorder=zorder))
    else:
        ax.plot([a.x, b.x], [a.y, b.y], color=color, linewidth=width,
                solid_capstyle="round", zorder=zorder)


def draw_node(ax, node: Node) -> None:
    """Dessine un node avec la couleur et la taille de son type."""
    ax.plot(node.x, node.y, marker="o", color=COLORS[node.type],
            markersize=SIZES[node.type], markeredgecolor="white", zorder=3)


def draw_shortest_path(ax, network: RoadNetwork) -> None:
    """Surligne le plus court chemin START -> END sous les routes."""
    path = network.get_shortest_path()
    for a, b in zip(path, path[1:]):
        draw_segment(ax, Segment(a, b), color=PATH_COLOR, width=PATH_WIDTH, zorder=0.5)


def draw_legend(ax) -> None:
    """Légende : un rond par type de node + le plus court chemin."""
    handles = [
        Line2D([], [], marker="o", linestyle="", color=COLORS[node_type],
               markersize=8, label=LABELS[node_type])
        for node_type in LABELS
    ]
    handles.append(Line2D([], [], color=PATH_COLOR, linewidth=PATH_WIDTH,
                          label="Plus court chemin"))
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False)


def setup_axes(ax, network: RoadNetwork, seed: int) -> None:
    """Efface l'écran et prépare le repère, le titre et la légende."""
    ax.clear()
    ax.set_title(f"RoadNetwork  —  seed {seed}")
    ax.set_xlim(-1, network.columns)
    ax.set_ylim(-1, network.rows)
    ax.set_aspect("equal")
    ax.axis("off")
    draw_legend(ax)


def draw_network(ax, network: RoadNetwork) -> None:
    """Dessine le réseau complet : chemin surligné, segments, puis nodes par-dessus."""
    draw_shortest_path(ax, network)
    for segment in network.segments:
        draw_segment(ax, segment)
    for node in network.nodes:
        draw_node(ax, node)


def draw_grid(ax, network: RoadNetwork, seed: int) -> None:
    """Dessine la grille vide (tous les nodes en UNUSED)."""
    setup_axes(ax, network, seed)
    for node in network.nodes:
        ax.plot(node.x, node.y, marker="o", color=COLORS[NodeType.UNUSED],
                markersize=SIZES[NodeType.UNUSED], zorder=2)


def draw_step(ax, network: RoadNetwork, index: int) -> None:
    """Étape d'animation : un segment et ses deux nodes ; à la fin, le plus court chemin."""
    segment = network.segments[index]
    draw_segment(ax, segment)
    draw_node(ax, segment.start)
    draw_node(ax, segment.end)
    if index == len(network.segments) - 1:
        draw_shortest_path(ax, network)


def animate_network(fig, ax, network: RoadNetwork, seed: int) -> FuncAnimation | None:
    """Rejoue la construction : les segments apparaissent dans leur ordre de création."""
    draw_grid(ax, network, seed)
    if not network.segments:
        return None
    return FuncAnimation(
        fig,
        lambda index: draw_step(ax, network, index),
        frames=len(network.segments),
        interval=ANIMATION_INTERVAL,
        repeat=False,
    )


def show(network: RoadNetwork, seed: int, on_randomize) -> None:
    """Ouvre la fenêtre : animation + bouton Randomize."""
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    fig.canvas.manager.set_window_title("RoadNetwork")
    fig.subplots_adjust(right=0.8, bottom=0.12)
    fig.animation = animate_network(fig, ax, network, seed)  # référence gardée

    button_ax = fig.add_axes([0.4, 0.02, 0.2, 0.06])
    button = Button(button_ax, "Randomize")

    def on_click(event) -> None:
        """Callback du bouton : stoppe l'animation en cours, régénère, rejoue."""
        if fig.animation is not None:
            fig.animation.event_source.stop()
        new_seed = on_randomize()
        fig.animation = animate_network(fig, ax, network, new_seed)
        fig.canvas.draw_idle()

    button.on_clicked(on_click)
    fig.button = button  # garder une référence, sinon le bouton ne répond plus
    plt.show()
