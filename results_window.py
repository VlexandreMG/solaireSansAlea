import tkinter as tk
from tkinter import ttk


def _format_kw(value_w):
    return value_w / 1000.0


def _format_kwh(value_wh):
    return value_wh / 1000.0


class ResultsWindow(tk.Toplevel):
    def __init__(self, master, resultats, on_new_calculation):
        super().__init__(master)
        self.title("Solaire - Résultats")
        self.geometry("640x420")
        self.resizable(False, False)
        self.configure(background="#f4f7fb")

        self._resultats = resultats
        self._on_new_calculation = on_new_calculation

        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(self, bg="#f4f7fb", padx=18, pady=18)
        container.pack(fill="both", expand=True)

        title = tk.Label(
            container,
            text="Résultats du dimensionnement",
            font=("Segoe UI", 18, "bold"),
            bg="#f4f7fb",
            fg="#203040",
        )
        title.pack(anchor="w", pady=(0, 14))

        self._build_section(
            container,
            "Calcul théorique",
            "#dce9f8",
            "#1e3d59",
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

        self._build_section(
            container,
            "Ce que vous devez acheter",
            "#fff1d6",
            "#8a4b00",
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
            bg="#f4f7fb",
            fg="#243447",
            pady=10,
        )
        resume_label.pack(fill="x", pady=(10, 12))

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
            bg="#f4f7fb",
            fg="#516070",
            pady=2,
        )
        details_label.pack(fill="x", pady=(0, 10))

        button_row = tk.Frame(container, bg="#f4f7fb")
        button_row.pack(fill="x")

        ttk.Button(
            button_row,
            text="Nouveau calcul",
            command=self._new_calculation,
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
        section = tk.Frame(parent, bg=bg_color, padx=14, pady=12)
        section.pack(fill="x", pady=(0, 12))

        title_label = tk.Label(
            section,
            text=title,
            font=("Segoe UI", 12, "bold"),
            bg=bg_color,
            fg=fg_color,
        )
        title_label.pack(anchor="w", pady=(0, 8))

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
        self._on_new_calculation()
        self.destroy()
