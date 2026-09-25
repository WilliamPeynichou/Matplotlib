"""L'écran : dessin, animation, curseurs et véhicules (features 4, 6, 9, 11, 14, 15).
Les collisions apparaissent en croix rouges qui s'effacent (ML-4).
Des boutons choisissent la conduite : hasard, règle ou apprise (ML-9)."""

import math
import random
import time

import matplotlib.pyplot as plt
from matplotlib.colors import same_color, to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch, Polygon
from matplotlib.path import Path
from matplotlib.widgets import Button, RadioButtons, Slider, TextBox

from learning import DRIVINGS, make_policy
from models import Node, NodeType, Segment
from network import RoadNetwork
from traffic import Traffic

try:
    import tkinter as tk
    from tkinter import font as tkfont
except ImportError:  # Linux sans python3-tk : pas de presse-papiers ni d'historique
    tk = None

THEMES = {  # "dark" : notes du prof ; "light" : les couleurs d'origine
    "dark": {
        "background": "#191E26",
        "text": "#DCD7C3",
        "info": "#9AA3AE",  # compteur sous le réseau
        "road": "#DCD7C3",
        "colors": {
            NodeType.UNUSED: "#303844",
            NodeType.START: "#3CBE82",
            NodeType.END: "#E65A50",
            NodeType.CONNECTION: "#DCD7C3",
            NodeType.INTERSECTION: "#F5B83D",
        },
        "sizes": {
            NodeType.UNUSED: 3,
            NodeType.START: 12,
            NodeType.END: 12,
            NodeType.CONNECTION: 4,
            NodeType.INTERSECTION: 9,
        },
        "node_edge": "#191E26",
        "path": "#3C8CE6",
        "widget_face": "#303844",  # rail des curseurs
        "widget_text": "#DCD7C3",
        "accent": "#3C8CE6",  # Generate, toggle ON, champ actif, Activer
        "accent_hover": "#5A9FEA",
        "accent_text": "#FFFFFF",
        "accent_soft": "#22324A",  # carte de la seed active
        "button_face": "#252B35",  # boutons icônes : fond discret
        "button_hover": "#303844",
        "button_text": "#DCD7C3",
        "field_face": "#252B35",
        "field_border": "#3A4350",
        "toggle_off": "#4A5462",
        "knob": "#FFFFFF",
        "card_face": "#222832",  # cartes de l'historique
        "card_hover": "#2A313C",
        "muted": "#8A93A0",  # petit texte gris
        "legend_text": "#DCD7C3",
    },
    "light": {
        "background": "#FFFFFF",
        "text": "#000000",
        "info": "#555555",
        "road": "#303844",
        "colors": {
            NodeType.UNUSED: "#D0D4DA",
            NodeType.START: "#3CBE82",
            NodeType.END: "#E65A50",
            NodeType.CONNECTION: "#303844",
            NodeType.INTERSECTION: "#F5B83D",
        },
        "sizes": {
            NodeType.UNUSED: 3,
            NodeType.START: 11,
            NodeType.END: 11,
            NodeType.CONNECTION: 5,
            NodeType.INTERSECTION: 8,
        },
        "node_edge": "#FFFFFF",
        "path": "#3C8CE6",
        "widget_face": "#D9D9D9",
        "widget_text": "#000000",
        "accent": "#3C8CE6",
        "accent_hover": "#2F7AD0",
        "accent_text": "#FFFFFF",
        "accent_soft": "#E3EEFB",
        "button_face": "#EEF0F3",
        "button_hover": "#E2E5EA",
        "button_text": "#303844",
        "field_face": "#FFFFFF",
        "field_border": "#C9CED6",
        "toggle_off": "#C4C9D1",
        "knob": "#FFFFFF",
        "card_face": "#F4F5F7",
        "card_hover": "#EBEDF0",
        "muted": "#7A828E",
        "legend_text": "#000000",
    },
}
DEFAULT_THEME = "dark"
LABELS = {
    NodeType.START: "Start",
    NodeType.END: "End",
    NodeType.CONNECTION: "Connection",
    NodeType.INTERSECTION: "Intersection",
    NodeType.UNUSED: "Unused",
}
ROAD_WIDTH = 2
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
SELECTION_COLOR = "#B3D4FC"  # fond du champ seed après Ctrl+A
MODIFIER_KEYS = ("control", "shift", "alt", "super", "cmd")  # seules, elles ne tapent rien
CORNER_RADIUS = 0.3  # coins arrondis des boutons et du champ, en fraction de leur hauteur
FIELD_FONT_SIZE = 11
TOGGLE_SIZE = (0.34, 0.18)  # interrupteur Randomize (pouces) : largeur, hauteur de la pilule
HISTORY_SIZE = "300x400"
HISTORY_PADDING = 16
HISTORY_FONTS = ("Segoe UI", "Helvetica Neue", "Helvetica", "DejaVu Sans")  # le 1er présent
HISTORY_MONO_FONTS = ("Consolas", "Menlo", "DejaVu Sans Mono")


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


def draw_segment(ax, segment: Segment, theme: dict, color: str | None = None,
                 width: float = ROAD_WIDTH, zorder: float = 1) -> None:
    """Dessine un segment, droit ou en courbe douce (couleur des routes du thème par défaut)."""
    color = color or theme["road"]
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


def draw_node(ax, node: Node, theme: dict) -> None:
    """Dessine un node avec la couleur et la taille de son type."""
    ax.plot(*get_position(node), marker="o", color=theme["colors"][node.type],
            markersize=theme["sizes"][node.type], markeredgecolor=theme["node_edge"], zorder=3)


def draw_shortest_path(ax, network: RoadNetwork, theme: dict) -> None:
    """Surligne le plus court chemin START -> END sous les routes."""
    path = network.get_shortest_path()
    for a, b in zip(path, path[1:]):
        draw_segment(ax, Segment(a, b), theme, color=theme["path"], width=PATH_WIDTH, zorder=0.5)


def draw_legend(ax, theme: dict) -> None:
    """Légende : un rond par type de node + le plus court chemin."""
    handles = [
        Line2D([], [], marker="o", linestyle="", color=theme["colors"][node_type],
               markersize=8, label=LABELS[node_type])
        for node_type in LABELS
    ]
    handles.append(Line2D([], [], color=theme["path"], linewidth=PATH_WIDTH,
                          label="Plus court chemin"))
    handles.append(Line2D([], [], marker="x", linestyle="", color=CRASH_COLOR,
                          markersize=9, markeredgewidth=2.5, label="Collision"))
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False,
              labelcolor=theme["legend_text"])


def draw_network(ax, network: RoadNetwork, theme: dict) -> None:
    """Dessine le réseau complet : chemin surligné, segments, puis nodes par-dessus."""
    draw_shortest_path(ax, network, theme)
    for segment in network.segments:
        draw_segment(ax, segment, theme)
    for node in network.nodes:
        draw_node(ax, node, theme)


def draw_grid(ax, network: RoadNetwork, title: str, theme: dict) -> None:
    """Efface l'écran et dessine la grille vide (tous les nodes en UNUSED)."""
    ax.clear()
    ax.set_title(title, color=theme["text"])
    ax.set_xlim(-1, network.columns)
    ax.set_ylim(-1, network.rows)
    ax.set_aspect("equal")
    ax.axis("off")
    draw_legend(ax, theme)
    for node in network.nodes:
        ax.plot(*get_position(node), marker="o", color=theme["colors"][NodeType.UNUSED],
                alpha=0.5, markersize=theme["sizes"][NodeType.UNUSED], zorder=2)


def draw_step(ax, network: RoadNetwork, index: int, theme: dict) -> None:
    """Étape de construction : un segment et ses deux nodes ; à la fin, le plus court chemin."""
    segment = network.segments[index]
    draw_segment(ax, segment, theme)
    draw_node(ax, segment.start, theme)
    draw_node(ax, segment.end, theme)
    if index == len(network.segments) - 1:
        draw_shortest_path(ax, network, theme)


def add_rounded_background(ax, edgecolor: str = "none") -> FancyBboxPatch:
    """Remplace le rectangle d'un axe (bouton, champ) par un fond plat aux coins arrondis."""
    ax.patch.set_visible(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    box = ax.get_position()
    width, height = ax.get_figure().get_size_inches()
    aspect = (box.width * width) / (box.height * height)  # l'axe est plus large que haut
    # mutation_aspect : coins ronds (et non ovales) même si l'axe est allongé
    background = FancyBboxPatch((0, 0), 1, 1, transform=ax.transAxes, mutation_aspect=aspect,
                                boxstyle=f"round,pad=0,rounding_size={CORNER_RADIUS / aspect}",
                                linewidth=1, edgecolor=edgecolor, zorder=0, gid="background")
    ax.add_artist(background)  # add_artist : ne change pas les limites de l'axe (icônes)
    return background


def clear_icon(ax) -> None:
    """Efface l'icône dessinée dans un bouton (le fond arrondi et le texte restent)."""
    for artist in [*ax.patches, *ax.lines]:
        if artist.get_gid() != "background":
            artist.remove()


def set_icon_limits(ax) -> None:
    """Repère de l'icône : x de 0 à 1, même échelle en y (cercle rond), centré, sans zoom auto."""
    box = ax.get_position()
    width, height = ax.get_figure().get_size_inches()
    ratio = (box.height * height) / (box.width * width)
    ax.set(xlim=(0, 1), ylim=(0.5 - ratio / 2, 0.5 + ratio / 2), autoscale_on=False)


def draw_history_icon(ax, color: str) -> None:
    """Icône historique : une horloge, un cercle + 2 aiguilles, en trait fin."""
    set_icon_limits(ax)
    ax.add_patch(Circle((0.5, 0.5), 0.19, fill=False, edgecolor=color, linewidth=1))
    ax.plot([0.5, 0.5, 0.59], [0.62, 0.5, 0.5], color=color, linewidth=1,
            solid_capstyle="round", solid_joinstyle="round")


def get_arc_points(x: float, y: float, radius: float, start: float, end: float,
                   steps: int = 24) -> list[tuple[float, float]]:
    """Points d'un arc de cercle, de l'angle start à l'angle end (radians)."""
    angles = [start + (end - start) * i / (steps - 1) for i in range(steps)]
    return [(x + radius * math.cos(a), y + radius * math.sin(a)) for a in angles]


def draw_theme_icon(ax, theme_name: str, color: str) -> None:
    """Icône du bouton thème : soleil en mode sombre (passer au clair), lune en mode clair."""
    set_icon_limits(ax)
    if theme_name == "dark":  # soleil : un disque + 8 rayons
        ax.add_patch(Circle((0.5, 0.5), 0.11, color=color))
        for i in range(8):
            angle = i * math.pi / 4
            ax.plot([0.5 + 0.175 * math.cos(angle), 0.5 + 0.25 * math.cos(angle)],
                    [0.5 + 0.175 * math.sin(angle), 0.5 + 0.25 * math.sin(angle)],
                    color=color, linewidth=1, solid_capstyle="round")
        return
    # lune : un grand cercle moins un petit cercle décalé (croissant, sans trou à recolorer)
    (x1, y1), r1 = (0.5, 0.5), 0.21
    (x2, y2), r2 = (0.6, 0.57), 0.175
    d = math.hypot(x2 - x1, y2 - y1)
    phi = math.atan2(y2 - y1, x2 - x1)
    a = math.acos((d * d + r1 * r1 - r2 * r2) / (2 * d * r1))  # points de croisement
    b = math.acos((d * d + r2 * r2 - r1 * r1) / (2 * d * r2))
    outer = get_arc_points(x1, y1, r1, phi + a, phi + 2 * math.pi - a)
    inner = get_arc_points(x2, y2, r2, phi + math.pi + b, phi + math.pi - b)
    ax.add_patch(Polygon(outer + inner, color=color))


def pick_font(root, families: tuple[str, ...], fallback: str) -> str:
    """Première police installée de la liste, sinon la police Tk par défaut (fallback)."""
    installed = set(tkfont.families(root))
    return next((family for family in families if family in installed), fallback)


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
        self.theme = DEFAULT_THEME  # "dark" ou "light" : clé de THEMES
        self.randomize = True  # interrupteur Randomize : seule source de vérité
        self.hover_targets = []  # (axe, fond arrondi, couleur, couleur au survol)
        self.animation = None
        self.fig, self.ax = plt.subplots(figsize=FIGURE_SIZE)
        self.fig.canvas.manager.set_window_title("RoadNetwork")
        self.fig.subplots_adjust(right=0.8, bottom=0.28)
        self.info = self.fig.text(0.5, 0.25, "", ha="center", animated=True)
        self.vehicle_artist = None
        self.crash_artist = None
        self.notice = ""  # message si la conduite demandée n'a pas pu être chargée
        self.background = None  # image du réseau sans véhicules (blitting)
        self.fig.canvas.mpl_connect("draw_event", self.on_draw)
        # Avant create_controls : on_key passe avant le TextBox et peut changer son texte.
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)
        self.create_controls()
        # Après create_controls : on_click passe après le TextBox (il sait s'il est actif).
        self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.apply_theme()
        self.regenerate()

    def create_controls(self) -> None:
        """Curseurs, champ seed, Randomize, Generate, historique, conduite, bouton thème."""
        self.roads_slider = Slider(self.fig.add_axes([0.25, 0.17, 0.45, 0.03]), "Routes",
                                   1, MAX_ROADS, valinit=self.settings["roads"], valstep=1)
        self.intersections_slider = Slider(
            self.fig.add_axes([0.25, 0.12, 0.45, 0.03]), "Intersections",
            0, MAX_INTERSECTIONS, valinit=self.settings["intersections"], valstep=1)
        self.vehicles_slider = Slider(self.fig.add_axes([0.25, 0.07, 0.45, 0.03]), "Véhicules",
                                      0, MAX_VEHICLES, valinit=self.settings["vehicles"],
                                      valstep=1)
        # Barre du bas : même hauteur, 0.012 d'écart entre chaque élément.
        self.seed_box = TextBox(self.fig.add_axes([0.1, 0.01, 0.1, 0.045]), "Seed",
                                initial=str(self.seed))
        self.seed_box.label.set_fontsize(FIELD_FONT_SIZE)
        self.seed_box.text_disp.set_fontsize(FIELD_FONT_SIZE)
        self.seed_background = add_rounded_background(self.seed_box.ax)
        # useblit=False partout : sinon les widgets se dessinent à part, hors de self.background,
        # et update_frame recolle un fond où la case, le point radio ou le survol sont anciens.
        self.history_button = Button(self.fig.add_axes([0.212, 0.01, 0.0315, 0.045]), "",
                                     useblit=False)  # carré ; icône dessinée par apply_theme
        self.randomize_ax = self.fig.add_axes([0.2555, 0.01, 0.1525, 0.045], frame_on=False)
        self.create_toggle()
        self.button = Button(self.fig.add_axes([0.42, 0.01, 0.16, 0.045]), "Generate",
                             useblit=False)
        for button in (self.history_button, self.button):
            button.background = add_rounded_background(button.ax)
        self.roads_slider.on_changed(self.on_network_change)
        self.intersections_slider.on_changed(self.on_network_change)
        self.vehicles_slider.on_changed(self.on_vehicles_change)
        self.seed_box.on_submit(self.on_submit)
        self.history_button.on_clicked(self.on_history)
        self.button.on_clicked(self.on_generate)
        driving_ax = self.fig.add_axes([0.81, 0.03, 0.17, 0.17], frame_on=False)
        # loc="left" : titre rangé à part (pas dans ax.title) → garder le Text pour le recolorer
        self.driving_title = driving_ax.set_title("Conduite", fontsize=10, loc="left")
        self.driving_radio = RadioButtons(driving_ax, list(DRIVINGS.values()),
                                          active=list(DRIVINGS).index(self.settings["driving"]),
                                          useblit=False)
        self.driving_radio.on_clicked(self.on_driving_change)
        self.theme_button = Button(self.fig.add_axes([0.955, 0.94, 0.0315, 0.045]), "",
                                   useblit=False)  # en haut à droite, icône soleil / lune
        self.theme_button.background = add_rounded_background(self.theme_button.ax)
        self.theme_button.on_clicked(self.on_theme)

    def create_toggle(self) -> None:
        """Interrupteur Randomize : pilule arrondie + rond qui glisse, puis le label."""
        ax = self.randomize_ax
        box = ax.get_position()
        width, height = self.fig.get_size_inches()
        ax.set_xlim(0, box.width * width)  # unités = pouces : le rond reste rond
        ax.set_ylim(0, box.height * height)
        ax.set_axis_off()
        pill_width, pill_height = TOGGLE_SIZE
        middle = box.height * height / 2
        self.toggle_pill = FancyBboxPatch(
            (0.02, middle - pill_height / 2), pill_width, pill_height, linewidth=0,
            boxstyle=f"round,pad=0,rounding_size={pill_height / 2}")
        self.toggle_knob = Circle((0, middle), pill_height / 2 - 0.025, linewidth=0, zorder=3)
        ax.add_patch(self.toggle_pill)
        ax.add_patch(self.toggle_knob)
        self.toggle_label = ax.text(0.02 + pill_width + 0.1, middle, "Randomize", va="center",
                                    fontsize=FIELD_FONT_SIZE)

    def draw_toggle(self) -> None:
        """Met l'interrupteur à l'état de self.randomize : ON = accent à droite, OFF = gris."""
        theme = THEMES[self.theme]
        pill_width, pill_height = TOGGLE_SIZE
        left, right = 0.02 + pill_height / 2, 0.02 + pill_width - pill_height / 2
        self.toggle_pill.set_facecolor(theme["accent"] if self.randomize else theme["toggle_off"])
        self.toggle_knob.set_facecolor(theme["knob"])
        self.toggle_knob.center = (right if self.randomize else left, self.toggle_knob.center[1])
        self.toggle_label.set_color(theme["widget_text"])

    def set_randomize(self, randomize: bool) -> None:
        """Change l'interrupteur et redessine (on_draw recapture le fond : blitting)."""
        self.randomize = randomize
        self.draw_toggle()
        self.background = None  # pas de blitting avec l'ancien fond d'ici le redessin
        self.fig.canvas.draw_idle()

    def on_click(self, event) -> None:
        """Clic : l'interrupteur (rond ou label) bascule ; bordure accent si le champ est actif."""
        if event.inaxes is self.randomize_ax:
            self.set_randomize(not self.randomize)
        self.draw_seed_border()

    def draw_seed_border(self) -> None:
        """Bordure fine du champ seed : couleur accent pendant la saisie."""
        theme = THEMES[self.theme]
        color = theme["accent"] if self.seed_box.capturekeystrokes else theme["field_border"]
        if not same_color(self.seed_background.get_edgecolor(), color):
            self.seed_background.set_edgecolor(color)
            self.background = None
            self.fig.canvas.draw_idle()

    def on_motion(self, event) -> None:
        """Survol : fond plus clair (ou accent plus vif) sous la souris, redessin si ça change."""
        changed = False
        for ax, background, color, hover in self.hover_targets:
            wanted = hover if event.inaxes is ax else color
            if not same_color(background.get_facecolor(), wanted):
                background.set_facecolor(wanted)
                changed = True
        if changed:
            self.background = None
            self.fig.canvas.draw_idle()

    def on_theme(self, event) -> None:
        """Bouton thème : sombre <-> clair. Même réseau, les véhicules continuent où ils sont."""
        self.theme = "light" if self.theme == "dark" else "dark"
        self.apply_theme()
        self.draw_static()
        self.background = None  # pas de blitting avec l'ancien fond d'ici le redessin
        self.fig.canvas.draw_idle()  # on_draw recapture le fond aux nouvelles couleurs

    def draw_static(self) -> None:
        """Redessine la partie fixe telle qu'elle est : grille + segments déjà construits."""
        theme = THEMES[self.theme]
        draw_grid(self.ax, self.network, self.get_title(), theme)
        for index in range(self.built):  # le dernier ajoute le plus court chemin
            draw_step(self.ax, self.network, index, theme)
        if self.vehicle_artist is not None:  # ax.clear() les a retirés : on les remet
            self.ax.add_collection(self.vehicle_artist, autolim=False)
            self.ax.add_collection(self.crash_artist, autolim=False)

    def apply_theme(self) -> None:
        """Recolore la fenêtre, les widgets et l'historique avec le thème courant."""
        theme = THEMES[self.theme]
        text = theme["widget_text"]
        self.fig.set_facecolor(theme["background"])
        self.ax.set_facecolor(theme["background"])
        self.info.set_color(theme["info"])
        for slider in (self.roads_slider, self.intersections_slider, self.vehicles_slider):
            slider.label.set_color(text)
            slider.valtext.set_color(text)
            slider.track.set_facecolor(theme["widget_face"])
        box = self.seed_box
        box.color = box.hovercolor = theme["field_face"]  # survol du TextBox : rien à redessiner
        box.ax.set_facecolor(box.color)
        self.seed_background.set_facecolor(theme["field_face"])
        self.draw_seed_border()
        box.label.set_color(text)
        box.text_disp.set_color(text)
        box.cursor.set_color(text)
        # Generate = bouton principal (accent) ; historique et thème = secondaires (discrets)
        styles = [(self.button, theme["accent"], theme["accent_hover"], theme["accent_text"]),
                  (self.history_button, theme["button_face"], theme["button_hover"],
                   theme["button_text"]),
                  (self.theme_button, theme["button_face"], theme["button_hover"],
                   theme["button_text"])]
        self.hover_targets = []
        for button, color, hover, label in styles:
            button.color = button.hovercolor = color  # survol géré par on_motion
            button.ax.set_facecolor(color)
            button.background.set_facecolor(color)
            button.label.set_color(label)
            self.hover_targets.append((button.ax, button.background, color, hover))
        self.draw_toggle()
        self.driving_radio.set_label_props({"color": [text] * len(DRIVINGS)})
        self.driving_radio.set_radio_props({"facecolor": text, "edgecolor": text})
        self.driving_title.set_color(theme["text"])
        for ax in (self.driving_radio.ax, self.randomize_ax):  # axes sans cadre
            ax.set_facecolor(theme["background"])
        clear_icon(self.history_button.ax)
        draw_history_icon(self.history_button.ax, theme["button_text"])
        clear_icon(self.theme_button.ax)
        draw_theme_icon(self.theme_button.ax, self.theme, theme["button_text"])
        self.refresh_history()

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
        """Bouton Generate : nouvelle seed si Randomize est activé, sinon la seed du champ."""
        if self.randomize:
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
        window.geometry(HISTORY_SIZE)
        window.fonts = (pick_font(window, HISTORY_FONTS, "TkDefaultFont"),
                        pick_font(window, HISTORY_MONO_FONTS, "TkFixedFont"))
        # En-tête : "Historique" + nombre de seeds en petit gris (mis à jour par refresh_history)
        header = tk.Frame(window)
        header.pack(fill="x", padx=HISTORY_PADDING, pady=(HISTORY_PADDING, 8))
        window.title_label = tk.Label(header, text="Historique", font=(window.fonts[0], 13, "bold"))
        window.title_label.pack(side="left")
        window.count_label = tk.Label(header, font=(window.fonts[0], 9))
        window.count_label.pack(side="left", padx=8, pady=(4, 0))
        # Liste qui défile à la molette (pas de barre : plus sobre).
        scroll_canvas = tk.Canvas(window, highlightthickness=0, bd=0)
        scroll_canvas.pack(fill="both", expand=True, padx=HISTORY_PADDING,
                           pady=(0, HISTORY_PADDING))
        self.history_rows = tk.Frame(scroll_canvas)
        rows_id = scroll_canvas.create_window((0, 0), window=self.history_rows, anchor="nw")
        self.history_rows.bind("<Configure>", lambda e: scroll_canvas.configure(
            scrollregion=scroll_canvas.bbox("all")))
        scroll_canvas.bind("<Configure>",  # les cartes prennent toute la largeur
                           lambda e: scroll_canvas.itemconfigure(rows_id, width=e.width))
        window.header = header
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
        theme = THEMES[self.theme]
        window = self.history_window
        font, mono = window.fonts
        for widget in (window, window.header, self.history_rows.master, self.history_rows):
            widget.configure(bg=theme["background"])  # history_rows.master = le Canvas
        window.title_label.configure(bg=theme["background"], fg=theme["text"])
        count = len(self.history)
        window.count_label.configure(bg=theme["background"], fg=theme["muted"],
                                     text=f"{count} seed{'s' if count > 1 else ''}")
        for card in self.history_rows.winfo_children():
            card.destroy()
        for seed in reversed(self.history):
            self.create_history_card(seed, theme, font, mono)

    def create_history_card(self, seed: int, theme: dict, font: str, mono: str) -> None:
        """Une carte plate : seed (copiable) à gauche, Activer à droite ; active = surlignée."""
        active = seed == self.seed
        color = theme["accent_soft"] if active else theme["card_face"]
        card = tk.Frame(self.history_rows, bg=color)
        card.pack(fill="x", pady=3)
        # barre accent à gauche de la seed active
        tk.Frame(card, width=3, bg=theme["accent"] if active else color).pack(side="left",
                                                                                fill="y")
        text = tk.StringVar(card, str(seed))
        # readonly sans bordure : on ne peut pas modifier, mais sélection + Ctrl+C restent possibles
        entry = tk.Entry(card, textvariable=text, width=8, state="readonly", relief="flat", bd=0,
                         font=(mono, 11), readonlybackground=color, fg=theme["text"],
                         highlightthickness=0)
        entry.pack(side="left", padx=(10, 0), pady=10)
        if active:
            tk.Label(card, text="Active", font=(font, 9), bg=color, fg=theme["muted"],
                     padx=12).pack(side="right", padx=10)
        else:
            tk.Button(card, text="Activer", font=(font, 9), relief="flat", bd=0, padx=12, pady=3,
                      cursor="hand2", bg=theme["accent"], fg=theme["accent_text"],
                      activebackground=theme["accent_hover"],
                      activeforeground=theme["accent_text"],
                      command=lambda: self.on_activate(seed)).pack(side="right", padx=10)
            # survol : carte un peu plus claire (sauf la carte active, déjà surlignée)
            for widget in (card, *card.winfo_children()):
                widget.bind("<Enter>", lambda e: self.color_card(card, theme["card_hover"]),
                            add="+")
                widget.bind("<Leave>", lambda e: self.color_card(card, theme["card_face"])
                            if not self.is_inside(card, e) else None, add="+")
        card.text = text  # garder une référence, sinon Tk vide le champ

    def color_card(self, card, color: str) -> None:
        """Fond d'une carte de l'historique (le bouton Activer garde sa couleur)."""
        card.configure(bg=color)
        for widget in card.winfo_children():
            if isinstance(widget, tk.Entry):
                widget.configure(readonlybackground=color)
            elif isinstance(widget, tk.Frame):
                widget.configure(bg=color)  # barre de gauche, invisible hors seed active

    def is_inside(self, card, event) -> bool:
        """La souris est-elle encore sur la carte (ou sur un de ses enfants) ?"""
        widget = card.winfo_containing(event.x_root, event.y_root)
        return widget is not None and str(widget).startswith(str(card))

    def on_activate(self, seed: int) -> None:
        """Bouton Activer de l'historique : seed dans le champ, Randomize désactivé, régénère."""
        if self.randomize:
            self.set_randomize(False)
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
        draw_grid(self.ax, self.network, self.get_title(), THEMES[self.theme])
        self.built = 0
        if not build:
            draw_network(self.ax, self.network, THEMES[self.theme])
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
                    draw_step(self.ax, self.network, self.built, THEMES[self.theme])
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
