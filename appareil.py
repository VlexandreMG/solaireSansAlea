import tkinter as tk
from tkinter import messagebox, ttk

from calculations import (
    calculer_pratique,
    calculer_puissance_reduite_wh,
    calculer_puissance_restante_pratique,
    calculer_theorique,
)
import db
from results_window import ResultsWindow


# Shared colors for a soft, minimal visual style.
BG_COLOR = "#f5f7fb"
CARD_COLOR = "#ffffff"
BORDER_COLOR = "#d9e2ec"
TEXT_COLOR = "#1f2933"
MUTED_COLOR = "#52606d"
ACCENT_COLOR = "#2f6f9f"
ACCENT_DARK = "#24577d"

TRANCHE_HOURS = {
    "T1": (6.0, 17.0),
    "T2": (17.0, 19.0),
    "T3": (19.0, 6.0),
}


class AppareilApp:
    def __init__(self, root):
        # Keep a direct reference to the main window.
        self.root = root
        self.root.title("Solaire - Saisie des appareils")
        self.root.geometry("980x600")
        self.root.minsize(900, 560)
        self.root.configure(background=BG_COLOR)

        # Map tranche labels to their database identifiers.
        self.tranches_by_label = {}

        # Prepare the visual style before drawing widgets.
        self._setup_styles()
        self._build_ui()

        try:
            # Load fixed tranches once at startup.
            db.ensure_tranches()
            self._load_tranches()
            self._refresh_tree()
        except Exception as exc:
            messagebox.showerror(
                "Erreur DB",
                f"Connexion SQL Server impossible:\n{exc}",
            )

    def _setup_styles(self):
        # Keep the interface calm and consistent.
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("App.TFrame", background=BG_COLOR)
        style.configure(
            "Card.TLabelframe",
            background=CARD_COLOR,
            foreground=TEXT_COLOR,
            bordercolor=BORDER_COLOR,
            padding=14,
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=BG_COLOR,
            foreground=TEXT_COLOR,
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Minimal.TButton",
            background=ACCENT_COLOR,
            foreground="#ffffff",
            padding=(14, 8),
            borderwidth=0,
            focusthickness=0,
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Minimal.TButton",
            background=[("active", ACCENT_DARK), ("pressed", ACCENT_DARK)],
        )
        style.configure(
            "Ghost.TButton",
            background="#edf2f7",
            foreground=TEXT_COLOR,
            padding=(14, 8),
            borderwidth=0,
            focusthickness=0,
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Ghost.TButton",
            background=[("active", "#d9e2ec"), ("pressed", "#cbd2d9")],
        )
        style.configure(
            "Minimal.Treeview",
            background=CARD_COLOR,
            fieldbackground=CARD_COLOR,
            foreground=TEXT_COLOR,
            bordercolor=BORDER_COLOR,
            rowheight=30,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Minimal.Treeview.Heading",
            background="#edf2f7",
            foreground=TEXT_COLOR,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        style.map("Minimal.Treeview", background=[("selected", "#dbeafe")])

    def _build_ui(self):
        # Main page container with consistent spacing.
        container = ttk.Frame(self.root, style="App.TFrame", padding=18)
        container.pack(fill="both", expand=True)

        # Header with a title and a short explanation.
        header = tk.Frame(container, bg=BG_COLOR)
        header.pack(fill="x", pady=(0, 14))

        title = tk.Label(
            header,
            text="Gestion des appareils",
            font=("Segoe UI", 20, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR,
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            header,
            text="Saisie simple des appareils, puis calcul de la puissance solaire et de la batterie.",
            font=("Segoe UI", 10),
            bg=BG_COLOR,
            fg=MUTED_COLOR,
        )
        subtitle.pack(anchor="w", pady=(4, 0))

        # Card used for the input form.
        form = ttk.LabelFrame(
            container,
            text="Ajouter un appareil",
            style="Card.TLabelframe",
        )
        form.pack(fill="x", pady=(0, 14))

        # The form stays on one line to keep the layout compact.
        ttk.Label(form, text="Nom").grid(
            row=0,
            column=0,
            padx=8,
            pady=8,
            sticky="w",
        )
        self.nom_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.nom_var, width=26).grid(
            row=0, column=1, padx=8, pady=8, sticky="w"
        )

        ttk.Label(form, text="Puissance (W)").grid(
            row=0, column=2, padx=8, pady=8, sticky="w"
        )
        self.puissance_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.puissance_var, width=14).grid(
            row=0, column=3, padx=8, pady=8, sticky="w"
        )

        ttk.Label(form, text="Tranche").grid(
            row=0,
            column=4,
            padx=8,
            pady=8,
            sticky="w",
        )
        self.tranche_var = tk.StringVar()
        self.tranche_combo = ttk.Combobox(
            form,
            textvariable=self.tranche_var,
            state="readonly",
            width=10,
            values=["T1", "T2", "T3"],
        )
        self.tranche_combo.grid(row=0, column=5, padx=8, pady=8, sticky="w")

        ttk.Label(form, text="Heure début").grid(
            row=0,
            column=6,
            padx=8,
            pady=8,
            sticky="w",
        )
        self.heure_debut_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.heure_debut_var, width=10).grid(
            row=0, column=7, padx=8, pady=8, sticky="w"
        )

        ttk.Label(form, text="Heure fin").grid(
            row=0,
            column=8,
            padx=8,
            pady=8,
            sticky="w",
        )
        self.heure_fin_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.heure_fin_var, width=10).grid(
            row=0, column=9, padx=8, pady=8, sticky="w"
        )

        ttk.Button(form, text="Ajouter", command=self.ajouter).grid(
            row=0, column=10, padx=8, pady=8
        )

        # Card used for the saved usages table.
        table_frame = ttk.LabelFrame(
            container,
            text="Appareils saisis",
            style="Card.TLabelframe",
        )
        table_frame.pack(fill="both", expand=True, pady=(0, 14))

        # Only the useful columns are shown to the user.
        columns = (
            "util_id",
            "nom",
            "puissance",
            "tranche",
            "heure_debut",
            "heure_fin",
            "duree",
        )
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=14,
            style="Minimal.Treeview",
        )

        # Column titles are short so the table stays readable.
        self.tree.heading("util_id", text="ID")
        self.tree.heading("nom", text="Nom")
        self.tree.heading("puissance", text="Puissance (W)")
        self.tree.heading("tranche", text="Tranche")
        self.tree.heading("heure_debut", text="Début")
        self.tree.heading("heure_fin", text="Fin")
        self.tree.heading("duree", text="Durée (h)")

        # Size each column according to the expected content.
        self.tree.column("util_id", width=70, anchor="center")
        self.tree.column("nom", width=220)
        self.tree.column("puissance", width=150, anchor="e")
        self.tree.column("tranche", width=100, anchor="center")
        self.tree.column("heure_debut", width=80, anchor="center")
        self.tree.column("heure_fin", width=80, anchor="center")
        self.tree.column("duree", width=100, anchor="e")

        # Add a vertical scrollbar for long histories.
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Place the list and the scrollbar side by side.
        self.tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(8, 0),
            pady=8,
        )
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)

        # Keep the action row visually separated from the content card.
        actions = tk.Frame(container, bg=BG_COLOR)
        actions.pack(fill="x")

        ttk.Button(
            actions,
            text="Supprimer",
            command=self.supprimer,
            style="Ghost.TButton",
        ).pack(side="left")
        ttk.Button(
            actions,
            text="Calculer",
            command=self.calculer,
            style="Minimal.TButton",
        ).pack(side="right")

    def _load_tranches(self):
        # Load the predefined tranches and expose them in the combo box.
        rows = db.get_tranches()
        if not rows:
            raise RuntimeError("Aucune tranche disponible dans la base.")

        labels = []
        self.tranches_by_label.clear()
        for tranche_id, label in rows:
            labels.append(label)
            self.tranches_by_label[label] = int(tranche_id)

        self.tranche_combo["values"] = labels
        if labels:
            self.tranche_combo.current(0)

    def _refresh_tree(self):
        # Refresh the table from the database state.
        for item in self.tree.get_children():
            self.tree.delete(item)

        def _format_hour(hour_value):
            if hour_value is None:
                return "--"
            return f"{float(hour_value):.2f}"

        rows = db.list_utilisations()
        for (
            util_id,
            _appareil_id,
            nom,
            puissance_w,
            _tranche_id,
            label,
            heure_debut,
            heure_fin,
            duree_h,
        ) in rows:
            self.tree.insert(
                "",
                "end",
                iid=str(util_id),
                values=(
                    util_id,
                    nom,
                    puissance_w,
                    label,
                    _format_hour(heure_debut),
                    _format_hour(heure_fin),
                    f"{float(duree_h):.2f}",
                ),
            )

    def _is_hour_in_tranche(self, hour_value, tranche_label):
        start, end = TRANCHE_HOURS[tranche_label]

        if start < end:
            return start <= hour_value <= end

        return hour_value >= start or hour_value <= end

    def _compute_duration_hours(self, heure_debut, heure_fin):
        duration = heure_fin - heure_debut
        if duration <= 0:
            duration += 24.0
        return duration

    def ajouter(self):
        # Read and normalize form inputs before validation.
        nom = self.nom_var.get().strip()
        puissance_raw = self.puissance_var.get().strip()
        tranche_label = self.tranche_var.get().strip()
        heure_debut_raw = self.heure_debut_var.get().strip()
        heure_fin_raw = self.heure_fin_var.get().strip()

        if not nom:
            messagebox.showwarning("Validation", "Le nom est obligatoire.")
            return

        if tranche_label not in self.tranches_by_label:
            messagebox.showwarning(
                "Validation",
                "Sélectionnez une tranche valide (T1/T2/T3).",
            )
            return

        # Convert numbers only after the text checks succeed.
        try:
            puissance_w = float(puissance_raw)
            heure_debut = float(heure_debut_raw)
            heure_fin = float(heure_fin_raw)
        except ValueError:
            messagebox.showwarning(
                "Validation",
                "Puissance, heure début et heure fin doivent être numériques.",
            )
            return

        if puissance_w <= 0:
            messagebox.showwarning(
                "Validation",
                "La puissance doit être > 0.",
            )
            return

        if not (0.0 <= heure_debut < 24.0) or not (0.0 <= heure_fin < 24.0):
            messagebox.showwarning(
                "Validation",
                "Les heures doivent être entre 0 et 23.99.",
            )
            return

        if heure_debut == heure_fin:
            messagebox.showwarning(
                "Validation",
                "Heure début et heure fin doivent être différentes.",
            )
            return

        if not self._is_hour_in_tranche(heure_debut, tranche_label):
            messagebox.showwarning(
                "Validation",
                "L'heure de début n'est pas dans la tranche sélectionnée.",
            )
            return

        if not self._is_hour_in_tranche(heure_fin, tranche_label):
            messagebox.showwarning(
                "Validation",
                "L'heure de fin n'est pas dans la tranche sélectionnée.",
            )
            return

        duree_h = self._compute_duration_hours(heure_debut, heure_fin)

        # Each tranche has a maximum duration linked to its time slot.
        max_duree = {"T1": 11.0, "T2": 2.0, "T3": 11.0}
        if duree_h > max_duree.get(tranche_label, 24.0):
            messagebox.showwarning(
                "Validation",
                "La durée dépasse la plage de la tranche sélectionnée.",
            )
            return

        try:
            # Save the appliance and its usage in one transaction.
            db.add_appareil_with_utilisation(
                nom=nom,
                puissance_w=puissance_w,
                tranche_id=self.tranches_by_label[tranche_label],
                heure_debut=heure_debut,
                heure_fin=heure_fin,
                duree_h=duree_h,
            )
            # Reset the fields the user is expected to fill again.
            self.nom_var.set("")
            self.puissance_var.set("")
            self.heure_debut_var.set("")
            self.heure_fin_var.set("")
            self._refresh_tree()
        except Exception as exc:
            messagebox.showerror("Erreur DB", f"Insertion impossible:\n{exc}")

    def supprimer(self):
        # Force a deliberate selection before deleting anything.
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo(
                "Suppression",
                "Sélectionnez une ligne à supprimer.",
            )
            return

        util_id = int(selected[0])
        try:
            # Delete the selected row and refresh the table immediately.
            db.delete_utilisation(util_id)
            self._refresh_tree()
        except Exception as exc:
            messagebox.showerror(
                "Erreur DB",
                f"Suppression impossible:\n{exc}",
            )

    def calculer(self):
        # Run the theoretical and practical sizing steps.
        try:
            theorique = calculer_theorique()
            resultat = calculer_pratique(theorique)

            # Compute the practical remaining power by tranche from the
            # recommended panel size so the results window can display it.
            resultat["puissance_restante_pratique"] = (
                calculer_puissance_restante_pratique(
                    resultat["panneau_achat_w"]
                )
            )

            # Convert the reduced practical remaining power into Wh so the
            # result window can display an energy-oriented value as requested.
            resultat["conversion_puissance_reduite_wh"] = (
                calculer_puissance_reduite_wh(
                    resultat["puissance_restante_pratique"][
                        "puissance_restante_totale_w"
                    ]
                )
            )

            # Persist the current calculation for later reference.
            db.save_resultat(
                resultat["panneau_theorique_w"],
                resultat["panneau_achat_w"],
                resultat["batterie_theorique_wh"],
                resultat["batterie_achat_wh"],
            )
        except Exception as exc:
            messagebox.showerror(
                "Erreur calcul",
                f"Impossible de calculer les besoins théoriques:\n{exc}",
            )
            return

        # Open the dedicated result window after successful computation.
        ResultsWindow(self.root, resultat, self.reset_form)

    def reset_form(self):
        # Clear the form so the next entry starts from a blank state.
        self.nom_var.set("")
        self.puissance_var.set("")
        self.heure_debut_var.set("")
        self.heure_fin_var.set("")
        if self.tranche_combo["values"]:
            self.tranche_combo.current(0)
        # Bring the main window back to the foreground.
        self.root.lift()
        self.root.focus_force()


if __name__ == "__main__":
    # Standard Tk bootstrap for the app entry point.
    root = tk.Tk()
    app = AppareilApp(root)
    root.mainloop()
