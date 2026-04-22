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
        # Keep enough vertical room for all cards including conversion values.
        self.geometry("760x800")
        self.minsize(700, 620)
        self.resizable(True, True)
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
        # Workflow summary for this method:
        # 1) Build the main container and header.
        # 2) Display theoretical and practical purchase sections.
        # 3) Display the practical remaining power section by tranche.
        # 4) Display the reduced-power conversion section in Wh.
        # 5) Display the tariff-based journalier/weekend pricing section.
        # 6) Show summary text and action button.

        # Main wrapper contains a canvas + vertical scrollbar.
        # This keeps bottom sections visible even on shorter screens.
        wrapper = tk.Frame(self, bg=BG_COLOR)
        wrapper.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            wrapper,
            bg=BG_COLOR,
            highlightthickness=0,
            borderwidth=0,
        )
        scrollbar = ttk.Scrollbar(
            wrapper,
            orient="vertical",
            command=canvas.yview,
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Content frame actually holds all cards and labels.
        container = tk.Frame(canvas, bg=BG_COLOR, padx=20, pady=20)
        canvas_window = canvas.create_window((0, 0), window=container, anchor="nw")

        # Keep canvas scrolling region synced with content height.
        def _on_container_configure(_event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        # Keep content width synced with canvas width.
        def _on_canvas_configure(event):
            canvas.itemconfigure(canvas_window, width=event.width)

        # Mouse wheel support for smooth vertical scrolling.
        def _on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-event.delta / 120), "units")

        container.bind("<Configure>", _on_container_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Unbind wheel handler when this window is destroyed.
        self.bind("<Destroy>", lambda _event: canvas.unbind_all("<MouseWheel>"))

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

        # Show remaining practical power per tranche when available.
        # This data is produced by calculer_puissance_restante_pratique(...)
        # and injected in AppareilApp.calculer before opening this window.
        puissance_restante = self._resultats.get("puissance_restante_pratique")
        if puissance_restante:
            self._build_section(
                container,
                "Puissance restante pratique",
                SOFT_ACCENT,
                TEXT_COLOR,
                [
                    (
                        "Pic de consommation",
                        puissance_restante["pic_w"],
                        "W",
                        "kW",
                    ),
                    (
                        "Reste T1",
                        puissance_restante["puissance_restante_t1_w"],
                        "W",
                        "kW",
                    ),
                    (
                        "Reste T2",
                        puissance_restante["puissance_restante_t2_w"],
                        "W",
                        "kW",
                    ),
                    (
                        "Reste T3",
                        puissance_restante["puissance_restante_t3_w"],
                        "W",
                        "kW",
                    ),
                    (
                        "Reste total",
                        puissance_restante["puissance_restante_totale_w"],
                        "W",
                        "kW",
                    ),
                ],
                highlight=True,
            )

        # Display the tariff outputs for journalier and weekend.
        # Supports pack pricing baseline (nb) and peak-hour surcharge display.
        prix_tarifaire = self._resultats.get("prix_tarifaire_wh - ETU4339")
        if prix_tarifaire:
            est_pointe = prix_tarifaire.get("est_heures_pointe", False)
            pointe_label = " (HEURES DE POINTE)" if est_pointe else " (BASE)"

            rows = [
                (
                    "Tarif journalier (pack)",
                    prix_tarifaire["prix_journalier_pack"],
                    "Ar",
                    "Ar",
                ),
                (
                    "Base journalier",
                    prix_tarifaire["nb_journalier_wh"],
                    "Wh",
                    "Wh",
                ),
                (
                    "Tarif journalier unitaire (base)",
                    prix_tarifaire["prix_journalier_base"],
                    "Ar/Wh",
                    "Ar/Wh",
                ),
                (
                    "Coût journalier (base)",
                    prix_tarifaire["cout_journalier_base"],
                    "Ar",
                    "Ar",
                ),
            ]

            if est_pointe:
                rows.extend(
                    [
                        (
                            f"Tarif journalier avec pointe (+{prix_tarifaire['surcharge_journalier_pct']:.0f}%)",
                            prix_tarifaire["prix_journalier_pointe"],
                            "Ar/Wh",
                            "Ar/Wh",
                        ),
                        (
                            "Coût journalier (heures de pointe)",
                            prix_tarifaire["cout_journalier_pointe"],
                            "Ar",
                            "Ar",
                        ),
                    ]
                )

            rows.extend(
                [
                    (
                        "Tarif weekend (pack)",
                        prix_tarifaire["prix_weekend_pack"],
                        "Ar",
                        "Ar",
                    ),
                    (
                        "Base weekend",
                        prix_tarifaire["nb_weekend_wh"],
                        "Wh",
                        "Wh",
                    ),
                    (
                        "Tarif weekend unitaire (base)",
                        prix_tarifaire["prix_weekend_base"],
                        "Ar/Wh",
                        "Ar/Wh",
                    ),
                    (
                        "Coût weekend (base)",
                        prix_tarifaire["cout_weekend_base"],
                        "Ar",
                        "Ar",
                    ),
                ]
            )

            if est_pointe:
                rows.extend(
                    [
                        (
                            f"Tarif weekend avec pointe (+{prix_tarifaire['surcharge_weekend_pct']:.0f}%)",
                            prix_tarifaire["prix_weekend_pointe"],
                            "Ar/Wh",
                            "Ar/Wh",
                        ),
                        (
                            "Coût weekend (heures de pointe)",
                            prix_tarifaire["cout_weekend_pointe"],
                            "Ar",
                            "Ar",
                        ),
                    ]
                )

            self._build_section(
                container,
                f"Prix selon le tarif{pointe_label}",
                SOFT_ACCENT,
                TEXT_COLOR,
                rows,
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
            elif unit == "h":
                # Hours are already in their base unit, no conversion needed.
                converted = value
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
                    text=(
                        f"{value:.2f} {unit} ({converted:.2f} {converted_unit})"
                        if unit in ("W", "Wh")
                        else f"{value:.2f} {unit}"
                    ),
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
