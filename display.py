"""L'écran : dessin du réseau avec Matplotlib (feature 4, puis 6, 9, 11)."""

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button

from models import Node, NodeType
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
    NodeType.START: 10,
    NodeType.END: 10,
    NodeType.CONNECTION: 6,
    NodeType.INTERSECTION: 8,
}
ROAD_COLOR = "#303844"
ROAD_WIDTH = 2
ANIMATION_INTERVAL = 60  # millisecondes entre deux segments


def draw_segment(ax, segment) -> None:
    """Dessine un segment entre ses deux nodes."""
    ax.plot(
        [segment.start.x, segment.end.x],
        [segment.start.y, segment.end.y],
        color=ROAD_COLOR,
        linewidth=ROAD_WIDTH,
        zorder=1,
    )


def draw_node(ax, node: Node) -> None:
    """Dessine un node avec la couleur et la taille de son type."""
    ax.plot(
        node.x,
        node.y,
        marker="o",
        color=COLORS[node.type],
        markersize=SIZES[node.type],
        zorder=2,
    )


def draw_network(ax, network: RoadNetwork) -> None:
    """Dessine les segments d'abord, puis les nodes par-dessus."""
    for segment in network.segments:
        draw_segment(ax, segment)
    for node in network.nodes:
        draw_node(ax, node)
    ax.set_aspect("equal")
    ax.axis("off")


def draw_grid(ax, network: RoadNetwork, seed: int) -> None:
    """Efface l'écran et dessine la grille vide (tous les nodes en UNUSED)."""
    ax.clear()
    ax.set_title(f"Seed : {seed}")
    for node in network.nodes:
        ax.plot(node.x, node.y, marker="o", color=COLORS[NodeType.UNUSED],
                markersize=SIZES[NodeType.UNUSED], zorder=2)
    ax.set_aspect("equal")
    ax.axis("off")


def draw_step(ax, network: RoadNetwork, index: int) -> None:
    """Étape d'animation : dessine le segment n° index et ses deux nodes."""
    segment = network.segments[index]
    draw_segment(ax, segment)
    draw_node(ax, segment.start)
    draw_node(ax, segment.end)


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
    fig, ax = plt.subplots()
    fig.canvas.manager.set_window_title("RoadNetwork")
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
