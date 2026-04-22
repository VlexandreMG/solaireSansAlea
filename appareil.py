import tkinter as tk
from tkinter import messagebox, ttk

from calculations import calculer_pratique, calculer_theorique
import db
from results_window import ResultsWindow


class AppareilApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Solaire - Saisie des appareils")
        self.root.geometry("900x520")

        self.tranches_by_label = {}
        self._build_ui()

        try:
            db.ensure_tranches()
            self._load_tranches()
            self._refresh_tree()
        except Exception as exc:
            messagebox.showerror(
                "Erreur DB",
                f"Connexion SQL Server impossible:\n{exc}",
            )

    def _build_ui(self):
        form = ttk.LabelFrame(self.root, text="Ajouter un appareil")
        form.pack(fill="x", padx=12, pady=12)

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

        ttk.Label(form, text="Durée (h)").grid(
            row=0,
            column=6,
            padx=8,
            pady=8,
            sticky="w",
        )
        self.duree_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.duree_var, width=10).grid(
            row=0, column=7, padx=8, pady=8, sticky="w"
        )

        ttk.Button(form, text="Ajouter", command=self.ajouter).grid(
            row=0, column=8, padx=8, pady=8
        )

        table_frame = ttk.LabelFrame(self.root, text="Appareils saisis")
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        columns = (
            "util_id",
            "nom",
            "puissance",
            "tranche",
            "duree",
        )
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=14,
        )

        self.tree.heading("util_id", text="ID")
        self.tree.heading("nom", text="Nom")
        self.tree.heading("puissance", text="Puissance (W)")
        self.tree.heading("tranche", text="Tranche")
        self.tree.heading("duree", text="Durée (h)")

        self.tree.column("util_id", width=70, anchor="center")
        self.tree.column("nom", width=250)
        self.tree.column("puissance", width=150, anchor="e")
        self.tree.column("tranche", width=100, anchor="center")
        self.tree.column("duree", width=120, anchor="e")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(8, 0),
            pady=8,
        )
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)

        actions = ttk.Frame(self.root)
        actions.pack(fill="x", padx=12, pady=(0, 12))

        ttk.Button(
            actions,
            text="Supprimer",
            command=self.supprimer,
        ).pack(side="left")
        ttk.Button(
            actions,
            text="Calculer",
            command=self.calculer,
        ).pack(side="right")

    def _load_tranches(self):
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
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = db.list_utilisations()
        for (
            util_id,
            _appareil_id,
            nom,
            puissance_w,
            _tranche_id,
            label,
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
                    f"{float(duree_h):.2f}",
                ),
            )

    def ajouter(self):
        nom = self.nom_var.get().strip()
        puissance_raw = self.puissance_var.get().strip()
        tranche_label = self.tranche_var.get().strip()
        duree_raw = self.duree_var.get().strip()

        if not nom:
            messagebox.showwarning("Validation", "Le nom est obligatoire.")
            return

        if tranche_label not in self.tranches_by_label:
            messagebox.showwarning(
                "Validation",
                "Sélectionnez une tranche valide (T1/T2/T3).",
            )
            return

        try:
            puissance_w = float(puissance_raw)
            duree_h = float(duree_raw)
        except ValueError:
            messagebox.showwarning(
                "Validation",
                "Puissance et durée doivent être numériques.",
            )
            return

        if puissance_w <= 0:
            messagebox.showwarning(
                "Validation",
                "La puissance doit être > 0.",
            )
            return

        if duree_h <= 0:
            messagebox.showwarning(
                "Validation",
                "La durée doit être > 0.",
            )
            return

        max_duree = {"T1": 11.0, "T2": 2.0, "T3": 11.0}
        if duree_h > max_duree.get(tranche_label, 24.0):
            messagebox.showwarning(
                "Validation",
                "La durée dépasse la plage de la tranche sélectionnée.",
            )
            return

        try:
            db.add_appareil_with_utilisation(
                nom=nom,
                puissance_w=puissance_w,
                tranche_id=self.tranches_by_label[tranche_label],
                duree_h=duree_h,
            )
            self.nom_var.set("")
            self.puissance_var.set("")
            self.duree_var.set("")
            self._refresh_tree()
        except Exception as exc:
            messagebox.showerror("Erreur DB", f"Insertion impossible:\n{exc}")

    def supprimer(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo(
                "Suppression",
                "Sélectionnez une ligne à supprimer.",
            )
            return

        util_id = int(selected[0])
        try:
            db.delete_utilisation(util_id)
            self._refresh_tree()
        except Exception as exc:
            messagebox.showerror(
                "Erreur DB",
                f"Suppression impossible:\n{exc}",
            )

    def calculer(self):
        try:
            theorique = calculer_theorique()
            resultat = calculer_pratique(theorique)
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

        ResultsWindow(self.root, resultat, self.reset_form)

    def reset_form(self):
        self.nom_var.set("")
        self.puissance_var.set("")
        self.duree_var.set("")
        if self.tranche_combo["values"]:
            self.tranche_combo.current(0)
        self.root.lift()
        self.root.focus_force()


if __name__ == "__main__":
    root = tk.Tk()
    app = AppareilApp(root)
    root.mainloop()
