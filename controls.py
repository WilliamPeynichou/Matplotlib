"""Contrôles Tk pour la seed : champ natif (Ctrl+A/C/V), case Randomize et bouton Generate.

Isolé de display.py : ce module ne connaît que des widgets Tk, jamais le réseau ni matplotlib.
"""

import tkinter as tk


class SeedControls:
    """Barre Tk ajoutée sous la fenêtre matplotlib (backend TkAgg requis)."""

    def __init__(self, window, seed: int, on_generate, on_submit):
        """on_generate() : clic sur le bouton Generate.
        on_submit() : touche Entrée dans le champ Seed."""
        self.frame = tk.Frame(window)
        self.frame.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Label(self.frame, text="Seed").pack(side=tk.LEFT, padx=(10, 4), pady=6)
        self.seed_var = tk.StringVar(value=str(seed))
        self.entry = tk.Entry(self.frame, textvariable=self.seed_var, width=10)
        self.entry.pack(side=tk.LEFT, padx=4, pady=6)
        self.entry.bind("<Return>", lambda event: on_submit())
        self.entry.bind("<Control-a>", self._select_all)

        self.randomize_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.frame, text="Randomize", variable=self.randomize_var).pack(
            side=tk.LEFT, padx=4, pady=6)

        tk.Button(self.frame, text="Generate", command=on_generate).pack(
            side=tk.LEFT, padx=10, pady=6)

        self._grow_window(window)

    def _grow_window(self, window) -> None:
        """Agrandit la fenêtre pour laisser de la place à la barre, sans rogner le graphique."""
        window.update_idletasks()
        extra = self.frame.winfo_reqheight()
        width = window.winfo_width()
        height = window.winfo_height()
        window.geometry(f"{width}x{height + extra}")

    def _select_all(self, event) -> str:
        """Ctrl+A : sélectionne tout le texte (pas un raccourci natif de tk.Entry)."""
        self.entry.select_range(0, tk.END)
        self.entry.icursor(tk.END)
        return "break"  # empêche tk d'insérer le caractère 'a'

    def is_randomize(self) -> bool:
        """Vrai si la case Randomize est cochée."""
        return self.randomize_var.get()

    def get_text(self) -> str:
        """Texte actuellement dans le champ Seed."""
        return self.seed_var.get()

    def set_seed(self, seed: int) -> None:
        """Synchronise le champ avec la seed réellement utilisée."""
        self.seed_var.set(str(seed))
