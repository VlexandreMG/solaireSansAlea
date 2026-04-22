import os
import pyodbc


def get_connection():
    """Open a SQL Server connection using env vars or local defaults."""
    conn_str = os.getenv(
        "SOLAIRE_DB_CONNECTION_STRING",
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=solaire_db;"
        "Trusted_Connection=yes;",
    )
    return pyodbc.connect(conn_str)


def ensure_tranches():
    """Insert fixed time slots if they do not exist yet."""
    ensure_schema()
    tranches = [
        (1, "T1", 6, 17),
        (2, "T2", 17, 19),
        (3, "T3", 19, 6),
    ]

    with get_connection() as conn:
        cur = conn.cursor()
        for tranche_id, label, h_start, h_end in tranches:
            cur.execute(
                "SELECT COUNT(1) FROM tranches WHERE id = ?",
                (tranche_id,),
            )
            exists = cur.fetchone()[0]
            if not exists:
                cur.execute(
                    """
                    INSERT INTO tranches (id, label, heure_debut, heure_fin)
                    VALUES (?, ?, ?, ?)
                    """,
                    (tranche_id, label, h_start, h_end),
                )
        conn.commit()


def ensure_schema():
    """Apply lightweight schema migrations required by current code."""
    with get_connection() as conn:
        cur = conn.cursor()

        for column_name in ("heure_debut", "heure_fin"):
            cur.execute(
                f"SELECT COL_LENGTH('utilisations', '{column_name}')"
            )
            exists = cur.fetchone()[0] is not None
            if not exists:
                cur.execute(
                    f"ALTER TABLE utilisations ADD {column_name} FLOAT NULL"
                )
            else:
                cur.execute(
                    (
                        f"ALTER TABLE utilisations ALTER COLUMN "
                        f"{column_name} FLOAT NULL"
                    )
                )

        conn.commit()


def get_tranches():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, label FROM tranches ORDER BY id")
        return cur.fetchall()


def _next_id(table_name):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT ISNULL(MAX(id), 0) + 1 FROM {table_name}")
        return int(cur.fetchone()[0])


def add_appareil_with_utilisation(
    nom,
    puissance_w,
    tranche_id,
    duree_h,
):
    appareil_id = _next_id("appareils")
    utilisation_id = _next_id("utilisations")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO appareils (id, nom, puissance_w)
            VALUES (?, ?, ?)
            """,
            (appareil_id, nom, puissance_w),
        )
        cur.execute(
            """
            INSERT INTO utilisations (
                id,
                appareil_id,
                tranche_id,
                heure_debut,
                heure_fin,
                duree_h
            )
            VALUES (?, ?, ?, NULL, NULL, ?)
            """,
            (
                utilisation_id,
                appareil_id,
                tranche_id,
                duree_h,
            ),
        )
        conn.commit()


def list_utilisations():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                u.id,
                a.id,
                a.nom,
                a.puissance_w,
                t.id,
                t.label,
                u.duree_h
            FROM utilisations u
            INNER JOIN appareils a ON a.id = u.appareil_id
            INNER JOIN tranches t ON t.id = u.tranche_id
            ORDER BY u.id
            """
        )
        return cur.fetchall()


def delete_utilisation(utilisation_id):
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT appareil_id FROM utilisations WHERE id = ?",
            (utilisation_id,),
        )
        row = cur.fetchone()
        if not row:
            return

        appareil_id = int(row[0])

        cur.execute("DELETE FROM utilisations WHERE id = ?", (utilisation_id,))

        # Keep appareils table clean for Sprint 2 one-row-per-entry behavior.
        cur.execute(
            "SELECT COUNT(1) FROM utilisations WHERE appareil_id = ?",
            (appareil_id,),
        )
        still_used = cur.fetchone()[0]
        if not still_used:
            cur.execute("DELETE FROM appareils WHERE id = ?", (appareil_id,))

        conn.commit()


def save_resultat(
    panneau_theorique_w,
    panneau_achat_w,
    batterie_theorique_wh,
    batterie_achat_wh,
):
    with get_connection() as conn:
        cur = conn.cursor()
        resultat_id = _next_id("resultats")
        cur.execute(
            """
            INSERT INTO resultats (
                id,
                date_calcul,
                panneau_theorique_w,
                panneau_achat_w,
                batterie_theorique_wh,
                batterie_achat_wh
            )
            VALUES (?, GETDATE(), ?, ?, ?, ?)
            """,
            (
                resultat_id,
                panneau_theorique_w,
                panneau_achat_w,
                batterie_theorique_wh,
                batterie_achat_wh,
            ),
        )
        conn.commit()
