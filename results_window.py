import tkinter as tk
from tkinter import ttk


BG_COLOR = "#f5f7fb"
CARD_COLOR = "#ffffff"
TEXT_COLOR = "#1f2933"
MUTED_COLOR = "#52606d"
ACCENT_COLOR = "#2f6f9f"
SOFT_ACCENT = "#eef4f9"


def _format_kw(value_w):
    # Convert watts to kilowatts for display.
    return value_w / 1000.0


def _format_kwh(value_wh):
    # Convert watt-hours to kilowatt-hours for display.
    return value_wh / 1000.0


class ResultsWindow(tk.Toplevel):
    def __init__(self, master, resultats, on_new_calculation):
        super().__init__(master)
        self.title("Solaire - Résultats")
        self.geometry("700x470")
        self.minsize(660, 440)
        self.resizable(False, False)
        self.configure(background=BG_COLOR)

        # Keep the data and the callback available for the result view.
        self._resultats = resultats
        self._on_new_calculation = on_new_calculation

        # Apply a small, consistent style layer for the result window.
        self._setup_styles()

        self._build_ui()

    def _setup_styles(self):
        # Reuse a light, minimal style in this top-level window.
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Result.TButton", padding=(14, 8), font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        # Main container with airy margins.
        container = tk.Frame(self, bg=BG_COLOR, padx=20, pady=20)
        container.pack(fill="both", expand=True)

        # Header stays short so the actual numbers remain the focus.
        title = tk.Label(
            container,
            text="Résultats du dimensionnement",
            font=("Segoe UI", 20, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR,
        )
        title.pack(anchor="w", pady=(0, 14))

        subtitle = tk.Label(
            container,
            text="Une lecture simple des besoins théoriques et de l'achat conseillé.",
            font=("Segoe UI", 10),
            bg=BG_COLOR,
            fg=MUTED_COLOR,
        )
        subtitle.pack(anchor="w", pady=(0, 14))

        # Theoretical sizing card.
        self._build_section(
            container,
            "Calcul théorique",
            SOFT_ACCENT,
            ACCENT_COLOR,
            [
                (
                    "Panneau",
                    self._resultats["panneau_theorique_w"],
                    "W",
                    "kW",
                ),
                (
                    "Batterie",
                    self._resultats["batterie_theorique_wh"],
                    "Wh",
                    "kWh",
                ),
            ],
        )

        # Practical sizing card, presented as the recommended purchase.
        self._build_section(
            container,
            "Ce que vous devez acheter",
            CARD_COLOR,
            TEXT_COLOR,
            [
                (
                    "Panneau solaire",
                    self._resultats["panneau_achat_w"],
                    "W",
                    "kW",
                ),
                (
                    "Batterie",
                    self._resultats["batterie_achat_wh"],
                    "Wh",
                    "kWh",
                ),
            ],
            highlight=True,
        )

        # One short sentence summarizes the final answer.
        resume = (
            "Avec vos appareils, vous avez besoin d'un panneau de "
            f"{self._resultats['panneau_achat_w']:.2f} W "
            "et d'une batterie de "
            f"{self._resultats['batterie_achat_wh']:.2f} Wh "
            "pour couvrir vos usages."
        )

        resume_label = tk.Label(
            container,
            text=resume,
            wraplength=590,
            justify="left",
            font=("Segoe UI", 10, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            pady=10,
        )
        resume_label.pack(fill="x", pady=(10, 12))

        # Keep the usage rule visible without cluttering the page.
        details = (
            "Le calcul se base sur les usages saisis par tranche horaire: "
            "T1 en journée, T2 en fin d'apres-midi et T3 la nuit."
        )
        details_label = tk.Label(
            container,
            text=details,
            wraplength=590,
            justify="left",
            font=("Segoe UI", 9, "normal"),
            bg=BG_COLOR,
            fg=MUTED_COLOR,
            pady=2,
        )
        details_label.pack(fill="x", pady=(0, 10))

        # Single action: start a fresh calculation flow.
        button_row = tk.Frame(container, bg=BG_COLOR)
        button_row.pack(fill="x")

        ttk.Button(
            button_row,
            text="Nouveau calcul",
            command=self._new_calculation,
            style="Result.TButton",
        ).pack(side="right")

    def _build_section(
        self,
        parent,
        title,
        bg_color,
        fg_color,
        rows,
        highlight=False,
    ):
        # Each result is displayed in a compact card-like block.
        section = tk.Frame(parent, bg=bg_color, padx=16, pady=14)
        section.pack(fill="x", pady=(0, 12))

        title_label = tk.Label(
            section,
            text=title,
            font=("Segoe UI", 12, "bold"),
            bg=bg_color,
            fg=fg_color,
        )
        title_label.pack(anchor="w", pady=(0, 8))

        # Build one row per technical value.
        for label, value, unit, converted_unit in rows:
            if unit == "W":
                converted = _format_kw(value)
            else:
                converted = _format_kwh(value)
            if unit == "Wh":
                converted = _format_kwh(value)

            row = tk.Frame(section, bg=bg_color)
            row.pack(fill="x", pady=2)

            name_label = tk.Label(
                row,
                text=f"- {label} :",
                bg=bg_color,
                fg=fg_color,
                font=("Segoe UI", 10, "normal"),
                width=18,
                anchor="w",
            )
            name_label.pack(side="left")

            value_label = tk.Label(
                row,
                text=f"{value:.2f} {unit} ({converted:.2f} {converted_unit})",
                bg=bg_color,
                fg=fg_color,
                font=("Segoe UI", 10, "bold" if highlight else "normal"),
                anchor="w",
            )
            value_label.pack(side="left")

    def _new_calculation(self):
            # Delegate the reset action to the main window and close this view.
        self._on_new_calculation()
        self.destroy()
