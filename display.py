"""L'écran : dessin, animation, curseurs et véhicules (features 4, 6, 9, 11, 14, 15).
Les collisions apparaissent en croix rouges qui s'effacent (ML-4).
Des boutons choisissent la conduite : hasard, règle ou apprise (ML-9)."""

import random
import time

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Arc, Circle, PathPatch, Polygon
from matplotlib.path import Path
from matplotlib.widgets import Button, CheckButtons, RadioButtons, Slider, TextBox

from learning import DRIVINGS, make_policy
from models import Node, NodeType, Segment
from network import RoadNetwork
from traffic import Traffic

try:
    import tkinter as tk
except ImportError:  # Linux sans python3-tk : pas de presse-papiers ni d'historique
    tk = None

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
SELECTION_COLOR = "#B3D4FC"  # fond du champ seed après Ctrl+A, seed active de l'historique
MODIFIER_KEYS = ("control", "shift", "alt", "super", "cmd")  # seules, elles ne tapent rien
ICON_COLOR = "#303844"  # icône historique


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


def draw_history_icon(ax) -> None:
    """Icône historique : une horloge (cercle + 2 aiguilles) et une flèche en arc anti-horaire."""
    ax.set_aspect("equal", adjustable="datalim")  # cercle rond même si le bouton est large
    ax.add_patch(Circle((0.5, 0.5), 0.2, fill=False, edgecolor=ICON_COLOR, linewidth=1.2))
    ax.plot([0.5, 0.5, 0.6], [0.63, 0.5, 0.5], color=ICON_COLOR, linewidth=1.2,
            solid_capstyle="round")
    ax.add_patch(Arc((0.5, 0.5), 0.72, 0.72, theta1=150, theta2=450, edgecolor=ICON_COLOR,
                     linewidth=1.2))
    # pointe au bout de l'arc (en haut), tournée vers la gauche : sens anti-horaire
    ax.add_patch(Polygon([(0.38, 0.86), (0.5, 0.95), (0.5, 0.77)], color=ICON_COLOR))


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

    def __init__(self, network: RoadNetwork, seed: int, settings: dict, generate, new_seed,
                 max_seed: int):
        self.network = network
        self.seed = seed
        self.settings = settings  # {"roads", "intersections", "vehicles" : int, "driving" : str}
        self.generate = generate  # generate(seed, roads, intersections) -> intersections
        self.new_seed = new_seed  # new_seed() -> int
        self.max_seed = max_seed
        self.history = []  # seeds générées, dans l'ordre
        self.history_window = None
        self.history_rows = None  # cadre Tk des lignes de l'historique
        self.writing_seed = False  # set_val déclenche on_submit : évite la boucle
        self.enter_pressed = False  # on_submit vient aussi d'un clic hors du champ
        self.select_all = False  # après Ctrl+A, la prochaine frappe remplace tout
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
        # Avant create_controls : on_key passe avant le TextBox et peut changer son texte.
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)
        self.create_controls()
        self.regenerate()

    def create_controls(self) -> None:
        """Curseurs, champ seed, Randomize, Generate, historique, choix de la conduite."""
        self.roads_slider = Slider(self.fig.add_axes([0.25, 0.17, 0.45, 0.03]), "Routes",
                                   1, MAX_ROADS, valinit=self.settings["roads"], valstep=1)
        self.intersections_slider = Slider(
            self.fig.add_axes([0.25, 0.12, 0.45, 0.03]), "Intersections",
            0, MAX_INTERSECTIONS, valinit=self.settings["intersections"], valstep=1)
        self.vehicles_slider = Slider(self.fig.add_axes([0.25, 0.07, 0.45, 0.03]), "Véhicules",
                                      0, MAX_VEHICLES, valinit=self.settings["vehicles"],
                                      valstep=1)
        self.seed_box = TextBox(self.fig.add_axes([0.1, 0.01, 0.1, 0.045]), "Seed",
                                initial=str(self.seed))
        # useblit=False partout : sinon les widgets se dessinent à part, hors de self.background,
        # et update_frame recolle un fond où la case, le point radio ou le survol sont anciens.
        self.history_button = Button(self.fig.add_axes([0.205, 0.01, 0.035, 0.045]), "",
                                     useblit=False)
        draw_history_icon(self.history_button.ax)
        self.randomize_check = CheckButtons(
            self.fig.add_axes([0.25, 0.01, 0.15, 0.045], frame_on=False), ["Randomize"], [True],
            useblit=False)
        self.button = Button(self.fig.add_axes([0.42, 0.01, 0.16, 0.045]), "Generate",
                             useblit=False)
        self.roads_slider.on_changed(self.on_network_change)
        self.intersections_slider.on_changed(self.on_network_change)
        self.vehicles_slider.on_changed(self.on_vehicles_change)
        self.seed_box.on_submit(self.on_submit)
        self.history_button.on_clicked(self.on_history)
        self.button.on_clicked(self.on_generate)
        self.randomize_check.on_clicked(self.on_randomize_change)
        driving_ax = self.fig.add_axes([0.81, 0.03, 0.17, 0.17], frame_on=False)
        driving_ax.set_title("Conduite", fontsize=10, loc="left")
        self.driving_radio = RadioButtons(driving_ax, list(DRIVINGS.values()),
                                          active=list(DRIVINGS).index(self.settings["driving"]),
                                          useblit=False)
        self.driving_radio.on_clicked(self.on_driving_change)

    def on_randomize_change(self, label: str) -> None:
        """Case Randomize : redessin complet, on_draw recapture le fond avec la case à jour.
        L'état n'est pas copié ici : on_generate le lit dans la case au moment du clic."""
        self.background = None  # pas de blitting avec l'ancien fond d'ici le redessin
        self.fig.canvas.draw_idle()

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

    def on_generate(self, event) -> None:
        """Bouton Generate : nouvelle seed si Randomize est coché, sinon la seed du champ."""
        if self.randomize_check.get_status()[0]:
            self.seed = self.new_seed()
            self.regenerate()
        else:
            self.generate_from_text(self.seed_box.text)

    def on_submit(self, text: str) -> None:
        """Entrée dans le champ seed : génère avec la seed écrite."""
        if self.writing_seed or not self.enter_pressed:
            return  # set_val, ou simple clic hors du champ
        self.enter_pressed = False
        self.generate_from_text(text)

    def generate_from_text(self, text: str) -> None:
        """Génère avec la seed écrite ; si elle est invalide, garde la précédente."""
        try:
            seed = int(text)
        except ValueError:
            seed = -1
        if not 0 <= seed <= self.max_seed:
            self.notice = f"Seed invalide {text.strip()!r} : entier de 0 à {self.max_seed}."
            self.info.set_text(self.notice)
            self.fig.canvas.draw_idle()
            return
        self.seed = seed
        self.regenerate()

    def write_seed(self, seed: int) -> None:
        """Écrit la seed dans le champ sans déclencher on_submit."""
        self.writing_seed = True
        self.seed_box.set_val(str(seed))
        self.writing_seed = False
        self.seed_box.cursor_index = len(self.seed_box.text)
        if not self.seed_box.capturekeystrokes:
            self.seed_box.cursor.set_visible(False)  # set_val affiche le curseur

    def on_key(self, event) -> None:
        """Raccourcis du champ seed : Ctrl+A, Ctrl+C, Ctrl+V. Le TextBox traite la touche après."""
        box = self.seed_box
        if not box.capturekeystrokes or event.key is None:
            return
        key = event.key
        self.enter_pressed = key in ("enter", "return")
        if key == "ctrl+a":
            self.set_select_all(True)
            return
        if key == "ctrl+c":
            self.set_clipboard(box.text)
            return
        if key in MODIFIER_KEYS:
            return
        if self.select_all and (len(key) == 1 or key in ("backspace", "delete", "ctrl+v")):
            box.text_disp.set_text("")  # tout est sélectionné : la frappe remplace le texte
            box.cursor_index = 0
        self.set_select_all(False)
        if key == "ctrl+v":
            pasted = self.get_clipboard().strip()
            text, index = box.text, box.cursor_index
            box.text_disp.set_text(text[:index] + pasted + text[index:])
            box.cursor_index = index + len(pasted)

    def set_select_all(self, selected: bool) -> None:
        """Ctrl+A : surligne tout le champ seed."""
        self.select_all = selected
        if selected:
            self.seed_box.text_disp.set_backgroundcolor(SELECTION_COLOR)
        else:
            self.seed_box.text_disp.set_bbox(None)

    def get_tk_widget(self):
        """Le widget Tk derrière Matplotlib, ou None (autre backend, ou tkinter absent)."""
        if tk is None or not hasattr(self.fig.canvas, "get_tk_widget"):
            return None
        return self.fig.canvas.get_tk_widget()

    def get_clipboard(self) -> str:
        """Texte du presse-papiers ("" s'il est vide ou inaccessible)."""
        widget = self.get_tk_widget()
        if widget is None:
            return ""
        try:
            return widget.clipboard_get()
        except tk.TclError:  # presse-papiers vide ou pas du texte
            return ""

    def set_clipboard(self, text: str) -> None:
        """Copie le texte dans le presse-papiers (rien si pas de Tk)."""
        widget = self.get_tk_widget()
        if widget is not None:
            widget.clipboard_clear()
            widget.clipboard_append(text)

    def on_history(self, event) -> None:
        """Bouton ↺ : petite fenêtre avec l'historique des seeds (une seule à la fois)."""
        if self.history_window is not None and self.history_window.winfo_exists():
            self.history_window.lift()
            self.history_window.focus_set()
            return
        widget = self.get_tk_widget()
        if widget is None:
            self.notice = "Historique indisponible : il faut le backend Tk (python3-tk)."
            self.info.set_text(self.notice)
            self.fig.canvas.draw_idle()
            return
        window = tk.Toplevel(widget)
        # liée à la fenêtre du jeu : reste devant, se minimise avec elle (pas de grab_set :
        # la fenêtre du jeu doit rester cliquable)
        window.transient(widget.winfo_toplevel())
        window.title("Historique des seeds")
        window.geometry("230x320")
        # Liste qui défile : un cadre dans un Canvas Tk, avec une barre de défilement.
        scroll_canvas = tk.Canvas(window, highlightthickness=0)
        scrollbar = tk.Scrollbar(window, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        scroll_canvas.pack(side="left", fill="both", expand=True)
        self.history_rows = tk.Frame(scroll_canvas)
        scroll_canvas.create_window((0, 0), window=self.history_rows, anchor="nw")
        self.history_rows.bind("<Configure>", lambda e: scroll_canvas.configure(
            scrollregion=scroll_canvas.bbox("all")))
        window.bind("<MouseWheel>",  # molette (Windows, macOS)
                    lambda e: scroll_canvas.yview_scroll(-1 if e.delta > 0 else 1, "units"))
        window.bind("<Button-4>", lambda e: scroll_canvas.yview_scroll(-1, "units"))  # Linux
        window.bind("<Button-5>", lambda e: scroll_canvas.yview_scroll(1, "units"))
        self.history_window = window
        self.refresh_history()

    def refresh_history(self) -> None:
        """Redessine la liste si la fenêtre est ouverte : plus récente en haut, active surlignée."""
        if self.history_window is None or not self.history_window.winfo_exists():
            return
        for row in self.history_rows.winfo_children():
            row.destroy()
        for seed in reversed(self.history):
            row = tk.Frame(self.history_rows)
            row.pack(fill="x", padx=6, pady=2)
            text = tk.StringVar(row, str(seed))
            background = SELECTION_COLOR if seed == self.seed else "white"
            # readonly : on ne peut pas modifier, mais sélection + Ctrl+C restent possibles
            tk.Entry(row, textvariable=text, width=10, state="readonly",
                     readonlybackground=background).pack(side="left")
            tk.Button(row, text="▶ Activer",
                      command=lambda seed=seed: self.on_activate(seed)).pack(side="left", padx=4)
            row.text = text  # garder une référence, sinon Tk vide le champ

    def on_activate(self, seed: int) -> None:
        """Bouton Activer de l'historique : seed dans le champ, Randomize décoché, régénère."""
        if self.randomize_check.get_status()[0]:
            self.randomize_check.set_active(0)
        self.seed = seed
        self.regenerate()

    def regenerate(self) -> None:
        """Génère le réseau puis rejoue sa construction."""
        self.intersections = self.generate(self.seed, self.settings["roads"],
                                           self.settings["intersections"])
        if self.seed not in self.history:  # une seed déjà présente n'est pas ajoutée deux fois
            self.history.append(self.seed)
        self.refresh_history()  # nouvelle ligne ou nouvelle seed surlignée
        self.write_seed(self.seed)
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


def show(network: RoadNetwork, seed: int, settings: dict, generate, new_seed,
         max_seed: int) -> None:
    """Ouvre la fenêtre et attend sa fermeture."""
    view = NetworkView(network, seed, settings, generate, new_seed, max_seed)
    view.fig.view = view  # garder une référence (animation, curseurs, boutons, champ seed)
    plt.show()
