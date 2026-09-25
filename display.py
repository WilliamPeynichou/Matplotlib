"""L'écran : dessin, animation, curseurs et véhicules (features 4, 6, 9, 11, 14, 15).
Les collisions apparaissent en croix rouges qui s'effacent (ML-4).
Des boutons choisissent la conduite : hasard, règle ou apprise (ML-9)."""

import random
import time

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from matplotlib.widgets import Button, RadioButtons, Slider

from learning import DRIVINGS, make_policy
from models import Node, NodeType, Segment
from network import RoadNetwork
from traffic import Traffic

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
VEHICLE_COLORS = ["#8E44AD", "#E67E22", "#16A085", "#C0392B", "#2980B9", "#D35400",
                  "#27AE60", "#7F8C8D", "#F1C40F", "#E84393"]
VEHICLE_SIZE = 70
CRASH_COLOR = "#FF1744"
CRASH_SIZE = 220
CRASH_DURATION = 0.6  # secondes : la croix de collision s'efface pendant ce temps
CURVED_ROADS = True  # False = segments droits
JITTER = 0.3  # décalage max à l'écran ; < 0.5 garde l'ordre des nodes (aucun croisement)
layout = {"seed": 0}  # seed du décalage, changée à chaque réseau
CURVE_STRENGTH = 0.5  # 0 = droit, 0.5 = courbe douce
FRAME_INTERVAL = 50  # millisecondes entre deux images (20 fps : fluide, CPU raisonnable)
SEGMENTS_PER_FRAME = 1  # vitesse de construction
MAX_DT = 0.1  # secondes : évite un saut si la fenêtre a gelé
FIGURE_SIZE = (10, 7)
MAX_ROADS = 10
MAX_INTERSECTIONS = 15
MAX_VEHICLES = 20


def get_position(node: Node) -> tuple[float, float]:
    """Position à l'écran : la case de la grille + un petit décalage au hasard (aspect organique).
    Même seed + même case = même décalage. Le modèle, lui, reste sur la grille."""
    rng = random.Random(f"{layout['seed']}-{node.x}-{node.y}")
    return (node.x + rng.uniform(-JITTER, JITTER), node.y + rng.uniform(-JITTER, JITTER))


def get_curve_points(a: Node, b: Node) -> list[tuple[float, float]]:
    """4 points de contrôle d'une courbe de Bézier à tangentes horizontales (a à gauche)."""
    (ax_, ay), (bx, by) = get_position(a), get_position(b)
    bend = CURVE_STRENGTH * (bx - ax_)
    return [(ax_, ay), (ax_ + bend, ay), (bx - bend, by), (bx, by)]


def get_point_on_segment(a: Node, b: Node, t: float) -> tuple[float, float]:
    """Position à t (0 -> 1) sur la route a -> b, en suivant la même forme que le dessin."""
    if not CURVED_ROADS:
        (x0, y0), (x1, y1) = get_position(a), get_position(b)
        return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
    if a.x > b.x:
        a, b, t = b, a, 1 - t
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = get_curve_points(a, b)
    u = 1 - t
    x = u**3 * x0 + 3 * u**2 * t * x1 + 3 * u * t**2 * x2 + t**3 * x3
    y = u**3 * y0 + 3 * u**2 * t * y1 + 3 * u * t**2 * y2 + t**3 * y3
    return x, y


def draw_segment(ax, segment: Segment, color: str = ROAD_COLOR, width: float = ROAD_WIDTH,
                 zorder: float = 1) -> None:
    """Dessine un segment, droit ou en courbe douce."""
    a, b = segment.start, segment.end
    if a.x > b.x:
        a, b = b, a  # toujours dessiner de gauche à droite
    if CURVED_ROADS:
        codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
        ax.add_patch(PathPatch(Path(get_curve_points(a, b), codes), fill=False,
                               edgecolor=color, linewidth=width, capstyle="round",
                               zorder=zorder))
    else:
        (x0, y0), (x1, y1) = get_position(a), get_position(b)
        ax.plot([x0, x1], [y0, y1], color=color, linewidth=width,
                solid_capstyle="round", zorder=zorder)


def draw_node(ax, node: Node) -> None:
    """Dessine un node avec la couleur et la taille de son type."""
    ax.plot(*get_position(node), marker="o", color=COLORS[node.type],
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
    handles.append(Line2D([], [], marker="x", linestyle="", color=CRASH_COLOR,
                          markersize=9, markeredgewidth=2.5, label="Collision"))
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False)


def draw_network(ax, network: RoadNetwork) -> None:
    """Dessine le réseau complet : chemin surligné, segments, puis nodes par-dessus."""
    draw_shortest_path(ax, network)
    for segment in network.segments:
        draw_segment(ax, segment)
    for node in network.nodes:
        draw_node(ax, node)


def draw_grid(ax, network: RoadNetwork, title: str) -> None:
    """Efface l'écran et dessine la grille vide (tous les nodes en UNUSED)."""
    ax.clear()
    ax.set_title(title)
    ax.set_xlim(-1, network.columns)
    ax.set_ylim(-1, network.rows)
    ax.set_aspect("equal")
    ax.axis("off")
    draw_legend(ax)
    for node in network.nodes:
        ax.plot(*get_position(node), marker="o", color=COLORS[NodeType.UNUSED], alpha=0.5,
                markersize=SIZES[NodeType.UNUSED], zorder=2)


def draw_step(ax, network: RoadNetwork, index: int) -> None:
    """Étape de construction : un segment et ses deux nodes ; à la fin, le plus court chemin."""
    segment = network.segments[index]
    draw_segment(ax, segment)
    draw_node(ax, segment.start)
    draw_node(ax, segment.end)
    if index == len(network.segments) - 1:
        draw_shortest_path(ax, network)


def get_vehicle_positions(traffic: Traffic) -> list[tuple[float, float]]:
    """Position (x, y) de chaque véhicule parti."""
    positions = []
    for vehicle in traffic.get_moving():
        if vehicle.target is None:
            positions.append(get_position(vehicle.current))
        else:
            positions.append(get_point_on_segment(vehicle.current, vehicle.target,
                                                  vehicle.progress))
    return positions


def get_recent_crashes(traffic: Traffic) -> list[tuple[float, float, float]]:
    """Collisions de moins de CRASH_DURATION secondes : (x, y, opacité de 1 à 0)."""
    crashes = []
    for moment, _a, _b, (current, target, progress) in reversed(traffic.collision_events):
        age = traffic.time - moment
        if age > CRASH_DURATION:
            break  # les événements sont dans l'ordre : tous les suivants sont plus vieux
        x, y = get_point_on_segment(current, target, progress)
        crashes.append((x, y, 1 - age / CRASH_DURATION))
    return crashes


class NetworkView:
    """La fenêtre : construit le réseau en animation, puis fait rouler les véhicules."""

    def __init__(self, network: RoadNetwork, seed: int, settings: dict, generate, new_seed):
        self.network = network
        self.seed = seed
        self.settings = settings  # {"roads", "intersections", "vehicles" : int, "driving" : str}
        self.generate = generate  # generate(seed, roads, intersections) -> intersections
        self.new_seed = new_seed  # new_seed() -> int
        self.animation = None
        self.fig, self.ax = plt.subplots(figsize=FIGURE_SIZE)
        self.fig.canvas.manager.set_window_title("RoadNetwork")
        self.fig.subplots_adjust(right=0.8, bottom=0.28)
        self.info = self.fig.text(0.5, 0.25, "", ha="center", color="#555555", animated=True)
        self.vehicle_artist = None
        self.crash_artist = None
        self.notice = ""  # message si la conduite demandée n'a pas pu être chargée
        self.background = None  # image du réseau sans véhicules (blitting)
        self.fig.canvas.mpl_connect("draw_event", self.on_draw)
        self.create_controls()
        self.regenerate()

    def create_controls(self) -> None:
        """Curseurs (routes, intersections, véhicules), bouton Randomize, choix de la conduite."""
        self.roads_slider = Slider(self.fig.add_axes([0.25, 0.17, 0.45, 0.03]), "Routes",
                                   1, MAX_ROADS, valinit=self.settings["roads"], valstep=1)
        self.intersections_slider = Slider(
            self.fig.add_axes([0.25, 0.12, 0.45, 0.03]), "Intersections",
            0, MAX_INTERSECTIONS, valinit=self.settings["intersections"], valstep=1)
        self.vehicles_slider = Slider(self.fig.add_axes([0.25, 0.07, 0.45, 0.03]), "Véhicules",
                                      0, MAX_VEHICLES, valinit=self.settings["vehicles"],
                                      valstep=1)
        self.button = Button(self.fig.add_axes([0.42, 0.01, 0.16, 0.045]), "Randomize")
        self.roads_slider.on_changed(self.on_network_change)
        self.intersections_slider.on_changed(self.on_network_change)
        self.vehicles_slider.on_changed(self.on_vehicles_change)
        self.button.on_clicked(self.on_randomize)
        driving_ax = self.fig.add_axes([0.81, 0.03, 0.17, 0.17], frame_on=False)
        driving_ax.set_title("Conduite", fontsize=10, loc="left")
        self.driving_radio = RadioButtons(driving_ax, list(DRIVINGS.values()),
                                          active=list(DRIVINGS).index(self.settings["driving"]))
        self.driving_radio.on_clicked(self.on_driving_change)

    def on_driving_change(self, label: str) -> None:
        """Boutons de conduite : même réseau, on relance la circulation avec la nouvelle."""
        self.settings["driving"] = next(name for name, text in DRIVINGS.items() if text == label)
        self.start_traffic()

    def select_driving(self, driving: str) -> None:
        """Coche un bouton de conduite sans déclencher on_driving_change."""
        self.driving_radio.eventson = False
        self.driving_radio.set_active(list(DRIVINGS).index(driving))
        self.driving_radio.eventson = True

    def on_network_change(self, value) -> None:
        """Curseur routes ou intersections : même seed, nouveau réseau."""
        self.settings["roads"] = int(self.roads_slider.val)
        self.settings["intersections"] = int(self.intersections_slider.val)
        self.regenerate()

    def on_vehicles_change(self, value) -> None:
        """Curseur véhicules : même réseau, on relance seulement la circulation."""
        self.settings["vehicles"] = int(self.vehicles_slider.val)
        self.start_traffic()

    def on_randomize(self, event) -> None:
        """Bouton : nouvelle seed, mêmes réglages."""
        self.seed = self.new_seed()
        self.regenerate()

    def regenerate(self) -> None:
        """Génère le réseau puis rejoue sa construction."""
        self.intersections = self.generate(self.seed, self.settings["roads"],
                                           self.settings["intersections"])
        self.restart(build=True)

    def start_traffic(self) -> None:
        """Relance les véhicules sans reconstruire le réseau."""
        self.restart(build=False)

    def get_title(self) -> str:
        """Titre : seed, routes, intersections obtenues (et demandées si différent)."""
        asked = self.settings["intersections"]
        intersections = f"{self.intersections}"
        if self.intersections != asked:
            intersections += f" (demandé {asked}, impossible avec {self.settings['roads']} routes)"
        return (f"seed {self.seed}  ·  routes {self.settings['roads']}  ·  "
                f"intersections {intersections}")

    def restart(self, build: bool) -> None:
        """Arrête l'animation en cours et en démarre une nouvelle."""
        if self.animation is not None:
            self.animation.stop()
        layout["seed"] = self.seed  # nouveau réseau = nouvelle forme organique
        self.path_length = self.network.get_shortest_path_length()
        draw_grid(self.ax, self.network, self.get_title())
        self.built = 0
        if not build:
            draw_network(self.ax, self.network)
            self.built = len(self.network.segments)
        policy, driving = make_policy(self.settings["driving"])
        self.notice = ""
        if driving != self.settings["driving"]:  # table apprise absente ou abîmée
            self.notice = "Table apprise absente ou abîmée (lancer train.py) : conduite Règle."
            self.settings["driving"] = driving
            self.select_driving(driving)
        self.traffic = Traffic(self.network, self.settings["vehicles"], self.seed, policy)
        colors =[VEHICLE_COLORS[i % len(VEHICLE_COLORS)] for i in range(self.settings["vehicles"])]
        self.vehicle_artist = self.ax.scatter([], [], s=VEHICLE_SIZE, zorder=4, animated=True,
                                              edgecolors="white", linewidths=1.5)
        self.crash_artist = self.ax.scatter([], [], s=CRASH_SIZE, marker="x", linewidths=3,
                                            color=CRASH_COLOR, zorder=5, animated=True)
        self.vehicle_colors = colors
        self.last_time = time.perf_counter()
        self.info.set_text("")
        self.background = None
        # Minuteur simple au lieu de FuncAnimation : FuncAnimation redessine tout à chaque image.
        self.animation = self.fig.canvas.new_timer(interval=FRAME_INTERVAL)
        self.animation.add_callback(self.update_frame, 0)
        self.animation.start()
        self.fig.canvas.draw_idle()

    def on_draw(self, event) -> None:
        """Après chaque dessin complet : mémorise le fond, puis pose véhicules et texte."""
        self.background = self.fig.canvas.copy_from_bbox(self.fig.bbox)
        self.draw_moving_parts()

    def draw_moving_parts(self) -> None:
        """Dessine seulement ce qui bouge (véhicules, collisions, compteur)."""
        if self.vehicle_artist is not None:
            self.ax.draw_artist(self.vehicle_artist)
            self.ax.draw_artist(self.crash_artist)
        self.fig.draw_artist(self.info)

    def update_frame(self, frame: int) -> None:
        """Une image : d'abord la construction, ensuite la circulation."""
        now = time.perf_counter()
        dt = min(now - self.last_time, MAX_DT)
        self.last_time = now
        if self.built < len(self.network.segments):
            for _ in range(SEGMENTS_PER_FRAME):
                if self.built < len(self.network.segments):
                    draw_step(self.ax, self.network, self.built)
                    self.built += 1
            self.fig.canvas.draw_idle()  # construction : dessin complet
            return
        self.update_traffic(dt)
        if self.background is None:
            return
        # Blitting : on recolle le fond et on redessine seulement les véhicules (CPU / 10).
        self.fig.canvas.restore_region(self.background)
        self.draw_moving_parts()
        self.fig.canvas.blit(self.fig.bbox)

    def update_traffic(self, dt: float) -> None:
        """Avance les véhicules et met à jour leurs points, les collisions et le compteur."""
        self.traffic.update(dt)
        positions = get_vehicle_positions(self.traffic)
        moving = self.traffic.get_moving()
        self.vehicle_artist.set_offsets(positions if positions else [[float("nan")] * 2])
        if positions:
            self.vehicle_artist.set_facecolors([self.vehicle_colors[v.number] for v in moving])
        crashes = get_recent_crashes(self.traffic)
        self.crash_artist.set_offsets([(x, y) for x, y, _ in crashes] or [[float("nan")] * 2])
        if crashes:
            self.crash_artist.set_color([to_rgba(CRASH_COLOR, alpha) for _, _, alpha in crashes])
        driving = self.settings["driving"]
        info = (f"Conduite : {DRIVINGS[driving]}  ·  véhicules en route : {len(moving)}  ·  "
                f"collisions : {self.traffic.collisions}")
        if driving == "rule":  # les divergences n'existent que pour la règle
            info += f"  ·  divergences (2 s) : {self.traffic.forced_divergences}"
        info += f"  ·  plus court chemin : {self.path_length} segments"
        self.info.set_text(info + (f"\n{self.notice}" if self.notice else ""))


def show(network: RoadNetwork, seed: int, settings: dict, generate, new_seed) -> None:
    """Ouvre la fenêtre et attend sa fermeture."""
    view = NetworkView(network, seed, settings, generate, new_seed)
    view.fig.view = view  # garder une référence (animation, curseurs, bouton)
    plt.show()
