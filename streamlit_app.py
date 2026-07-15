# -*- coding: utf-8 -*-
"""
Outil Pilotage RS — version Streamlit in Snowflake (SiS).

Réutilise TEL QUEL le dashboard HTML/JS existant (dashboard_template.html) et y
injecte des données LIVE lues dans Snowflake. À déployer dans Snowsight
(Projects -> Streamlit). Aucun identifiant à gérer : l'app utilise la session
Snowflake active de l'utilisateur connecté.

Fichiers à joindre à l'app (même stage) :
  - streamlit_app.py         (ce fichier)
  - dashboard_template.html  (le gabarit, sans données)
"""

import json
from collections import defaultdict

import streamlit as st
import streamlit.components.v1 as components

# Récupération de la session Snowflake, avec repli si l'API varie selon la
# version du runtime Streamlit in Snowflake.
try:
    from snowflake.snowpark.context import get_active_session
except Exception:  # pragma: no cover
    get_active_session = None


def get_session():
    """Retourne une session Snowpark active (méthode standard + repli)."""
    if get_active_session is not None:
        try:
            return get_active_session()
        except Exception:
            pass
    # Repli : connexion Streamlit par défaut définie dans le runtime SiS
    return st.connection("snowflake").session()

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Outil Pilotage RS", layout="wide")

MONTHS = [1, 2, 3, 4, 5]
YEARS = [2025, 2026]

SQL_QUERY = """
SELECT
    CODE_CLIENT            AS STORE_CODE,
    CLI_ENSEIGNE           AS ENSEIGNE,
    CLI_RAISON_SOCIALE     AS RAISON_SOC,
    GROUPE_1               AS GROUPE,
    REGION                 AS SECTEUR,
    LIBELLE_REPRESENTANT   AS VENDEUR,
    ART_CODE_ARTICLE       AS ART_CODE,
    LIBELLE_ARTICLE        AS ART_LABEL,
    CATEGORIE,
    ANNEE,
    MOIS,
    SUM(PPGC_MONTANT_TTC)  AS MONTANT,
    SUM(QTE_SORTIE_SAISSE) AS QUANTITE
FROM DLK_POC_01."2 - Transfo (Staging)"."Transfo_BI_SortiesCaisses"
WHERE ANNEE IN (2025, 2026)
  AND MOIS BETWEEN 1 AND 5
GROUP BY
    CODE_CLIENT, CLI_ENSEIGNE, CLI_RAISON_SOCIALE, GROUPE_1, REGION,
    LIBELLE_REPRESENTANT, ART_CODE_ARTICLE, LIBELLE_ARTICLE, CATEGORIE, ANNEE, MOIS
"""

# --- Périmètre (mêmes règles que le dashboard) ------------------------------
APPLY_PERIMETER = True
EXCLUDE_SECTEURS = {"DCN"}
EXCLUDE_GROUPES = {"CULTURA", "NOSOLI"}
MIN_PDV_PAR_ENSEIGNE = 5
REQUIRE_ACTIVE_2026 = True


def normalize_groupe(g):
    if g and "LECLERC" in str(g).upper():
        return "LECLERC"
    return g


def apply_perimeter(rows):
    kept = []
    for r in rows:
        r["groupe"] = normalize_groupe(r["groupe"])
        if r["secteur"] in EXCLUDE_SECTEURS:
            continue
        if (str(r["groupe"] or "")).upper() in EXCLUDE_GROUPES:
            continue
        kept.append(r)
    stores_by_grp = defaultdict(set)
    active2026 = defaultdict(set)
    for r in kept:
        stores_by_grp[r["groupe"]].add(r["store_code"])
        if int(r["annee"]) == 2026 and float(r["montant"] or 0) != 0:
            active2026[r["groupe"]].add(r["store_code"])
    valid = set()
    for g, pdvs in stores_by_grp.items():
        if len(pdvs) < MIN_PDV_PAR_ENSEIGNE:
            continue
        if REQUIRE_ACTIVE_2026 and not active2026.get(g):
            continue
        valid.add(g)
    return [r for r in kept if r["groupe"] in valid]


# --- Construction de l'objet D (identique au script de refresh) -------------
def build_D(rows):
    nmon = len(MONTHS)
    slot_of = {m: i for i, m in enumerate(sorted(MONTHS))}
    stores = {}
    repGA = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0, 0.0, 0.0]))
    artCat = {}
    repRegion = {}
    artStores = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))

    for r in rows:
        try:
            yr = int(r["annee"]); mo = int(r["mois"])
        except (TypeError, ValueError):
            continue
        if mo not in slot_of or yr not in YEARS:
            continue
        amt = float(r["montant"] or 0)
        qte = float(r.get("quantite") or 0)
        code = str(r["store_code"])
        artfull = f"{r['art_code']} - {r['art_label']}"
        cat = r["categorie"]; g1 = r["groupe"]; rep = r["vendeur"]
        slot = slot_of[mo] + (0 if yr == YEARS[0] else nmon)

        st_ = stores.get(code)
        if st_ is None:
            st_ = {"c": code, "e": r["enseigne"], "rs": r["raison_soc"],
                   "g1": g1, "r": r["secteur"], "rep": rep, "cm": {}}
            stores[code] = st_
        arr = st_["cm"].get(cat)
        if arr is None:
            arr = [0.0] * (2 * nmon); st_["cm"][cat] = arr
        arr[slot] += amt

        artCat[artfull] = cat
        repRegion[rep] = r["secteur"]
        g = repGA[rep][f"{g1}|{artfull}"]
        if yr == YEARS[0]:
            g[0] += amt; g[2] += qte
        else:
            g[1] += amt; g[3] += qte
        a = artStores[artfull][code]
        if yr == YEARS[0]:
            a[0] += amt
        else:
            a[1] += amt

    def r1(x):
        return round(x + 0.0, 1)

    stores_list = []
    for st_ in stores.values():
        st_["cm"] = {c: [r1(v) for v in arr] for c, arr in st_["cm"].items()}
        stores_list.append(st_)
    repGA_out = {rep: {k: [r1(v) for v in vals] for k, vals in d.items()}
                 for rep, d in repGA.items()}
    artStores_out = {art: [[c, r1(v[0]), r1(v[1])] for c, v in d.items()]
                     for art, d in artStores.items()}
    return {"stores": stores_list, "repGA": repGA_out, "artCat": artCat,
            "repRegion": repRegion, "artStores": artStores_out}


# ---------------------------------------------------------------------------
# CHARGEMENT DES DONNÉES (mis en cache ; bouton pour rafraîchir)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner="Lecture des sorties caisses dans Snowflake…")
def load_D():
    session = get_session()
    df = session.sql(SQL_QUERY).to_pandas()
    df.columns = [c.lower() for c in df.columns]
    rows = df.to_dict("records")
    if APPLY_PERIMETER:
        rows = apply_perimeter(rows)
    return build_D(rows), len(rows)


def render():
    D, nrows = load_D()
    with open("dashboard_template.html", encoding="utf-8") as f:
        template = f.read()
    blob = json.dumps(D, ensure_ascii=False, separators=(",", ":"))
    html = template.replace("/*__DASHBOARD_DATA__*/", blob)
    components.html(html, height=1500, scrolling=True)
    return D, nrows


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
top = st.container()
with top:
    c1, c2 = st.columns([1, 6])
    if c1.button("🔄 Rafraîchir"):
        st.cache_data.clear()

D, nrows = render()
st.caption(f"Source : DLK_POC_01 · {len(D['stores'])} magasins · "
           f"{len(D['artCat'])} articles · {nrows:,} lignes agrégées · "
           f"données live Snowflake.")
