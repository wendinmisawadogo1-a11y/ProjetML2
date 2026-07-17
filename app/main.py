"""
main.py — Application EcoSort-Search (interface Streamlit).

Flux : recherche produit -> vignettes Jumia -> selection -> analyse IA ->
revelation plein ecran de la couleur de poubelle.

Version actuelle : branchee sur les donnees factices (mock_data).
Pour passer aux vraies implementations, remplacer uniquement l'import
ci-dessous par :
    from scraping.jumia_scraper import search_jumia
    from app.inference import predict_bin
"""

import sys
import os

# Permet à Python de trouver les modules du projet (scraping/, app/)
# quel que soit le dossier depuis lequel Streamlit est lancé.
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)


import streamlit as st

from mapping import infos_poubelle, POUBELLES
from scraping.jumia_scraper import search_jumia
from mock_data import predict_bin   # on garde le mock pour l'IA en attendant le modèle


SEUIL_CONFIANCE = 0.55

st.set_page_config(
    page_title="EcoSort-Search",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Styles — direction visuelle : fond clair "table de tri", accents = les
# 5 couleurs de poubelles, typo caracterielle (Fraunces) pour les titres.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap');

:root {
    --ink: #1B2A24;
    --muted: #6B7C74;
    --line: #E7ECE8;
    --paper: #FBFCFB;
    --leaf: #1F8A54;
    --leaf-dark: #14663D;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--ink); }
.stApp { background: var(--paper); }
.block-container { padding-top: 2.2rem; max-width: 1080px; }

/* ---- en-tete ---- */
.eco-brand {
    display: flex; align-items: baseline; gap: 10px; margin-bottom: 2px;
}
.eco-brand .mark {
    font-family: 'Fraunces', serif; font-weight: 700; font-size: 2.5rem;
    color: var(--ink); letter-spacing: -0.02em; line-height: 1;
}
.eco-brand .mark .g { color: var(--leaf); }
.eco-brand .leaf { font-size: 1.6rem; }
.eco-tag {
    color: var(--muted); font-size: 1.05rem; margin: 6px 0 26px 0; max-width: 640px;
}

/* ---- barre de recherche ---- */
.stTextInput input {
    background: #FFFFFF; color: var(--ink);
    caret-color: var(--leaf);       /* curseur de saisie bien visible (vert) */
    border: 1.5px solid var(--line); border-radius: 12px;
    padding: 14px 16px; font-size: 1.02rem;
}
.stTextInput input:focus { border-color: var(--leaf); box-shadow: 0 0 0 3px rgba(31,138,84,.12); }
.stButton > button {
    background: var(--leaf); color: #fff; border: none; font-weight: 600;
    border-radius: 12px; padding: 14px 8px; font-size: 1rem;
    transition: background .15s ease;
}
.stButton > button:hover { background: var(--leaf-dark); color: #fff; }

/* ---- carte produit facon Jumia ---- */
.pcard {
    background: #FFFFFF; border: 1px solid var(--line);
    border-radius: 14px; overflow: hidden;
    transition: box-shadow .18s ease, transform .18s ease, border-color .18s ease;
    height: 100%;
    display: flex; flex-direction: column;   /* colonne : image en haut, corps dessous */
}
.pcard:hover {
    box-shadow: 0 10px 26px rgba(20,60,40,.10);
    transform: translateY(-3px); border-color: #CDE3D6;
}
.pcard-imgwrap { position: relative; background: #F4F7F5; }
.pcard-imgwrap img { width: 100%; aspect-ratio: 1/1; object-fit: cover; display: block; }
.pcard-badge {
    position: absolute; top: 10px; left: 10px;
    background: #E7492E; color: #fff; font-weight: 700; font-size: .78rem;
    padding: 3px 8px; border-radius: 6px;
}
.pcard-body {
    padding: 12px 13px 12px 13px;
    display: flex; flex-direction: column; flex: 1 1 auto;  /* occupe la hauteur restante */
}
.pcard-name {
    font-size: .9rem; font-weight: 500; line-height: 1.32; color: var(--ink);
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    overflow: hidden; min-height: 2.35em;
}
.pcard-price {
    font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.12rem;
    color: var(--ink); margin-top: auto;         /* colle le prix en bas de la carte */
    line-height: 1.25; white-space: nowrap;      /* prix sur une seule ligne */
    overflow: hidden; text-overflow: ellipsis;   /* fourchette trop longue -> ... */
}

/* ---- eyebrow / titres de section ---- */
.eyebrow {
    text-transform: uppercase; letter-spacing: .14em; font-size: .74rem;
    font-weight: 700; color: var(--leaf); margin-bottom: 4px;
}
.section-title {
    font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.5rem;
    color: var(--ink); margin: 0 0 4px 0;
}
.section-hint { color: var(--muted); font-size: .96rem; margin-bottom: 14px; }

/* ---- panneau resultat : LE moment signature ---- */
.result-panel {
    border-radius: 26px; padding: 60px 44px; text-align: center;
    position: relative; overflow: hidden;
    animation: reveal .55s cubic-bezier(.2,.8,.2,1);
}
@keyframes reveal { from { opacity:0; transform: scale(.94) translateY(10px);} to {opacity:1; transform:none;} }
.result-emoji { font-size: 4.4rem; line-height: 1; }
.result-bin {
    font-family: 'Fraunces', serif; font-weight: 700; font-size: 3.1rem;
    letter-spacing: -0.02em; margin: 10px 0 2px 0;
}
.result-mat { font-size: 1.12rem; font-weight: 600; opacity: .82; }
.result-desc { max-width: 540px; margin: 18px auto 0; font-size: 1.04rem; line-height: 1.55; opacity: .92; }
.result-pill {
    display: inline-block; margin-top: 24px; padding: 9px 22px; border-radius: 999px;
    font-weight: 600; font-size: .92rem; background: rgba(255,255,255,.22);
    backdrop-filter: blur(2px);
}

/* ---- tuile poubelle (accueil) ---- */
.bin-tile {
    background: #FFFFFF; border: 1px solid var(--line); border-radius: 16px;
    padding: 18px 16px; height: 100%; border-top: 4px solid var(--tilecolor);
}
.bin-tile .be { font-size: 1.9rem; }
.bin-tile .bn { font-weight: 700; font-size: .96rem; margin: 8px 0 4px; color: var(--ink); }
.bin-tile .bd { color: var(--muted); font-size: .82rem; line-height: 1.42; }

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Etat de session
# ---------------------------------------------------------------------------
st.session_state.setdefault("resultats", None)
st.session_state.setdefault("prediction", None)
st.session_state.setdefault("produit_choisi", None)


def lancer_recherche():
    kw = st.session_state.get("champ_recherche", "").strip()
    st.session_state.prediction = None
    st.session_state.produit_choisi = None
    st.session_state.resultats = search_jumia(kw) if kw else None


def analyser_produit(produit: dict):
    st.session_state.produit_choisi = produit
    st.session_state.prediction = predict_bin(produit["image_url"], nom_produit=produit["nom"])


# ---------------------------------------------------------------------------
# En-tete + recherche
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="eco-brand"><span class="mark">Eco<span class="g">Sort</span></span>'
    '<span class="leaf">♻️</span></div>'
    '<p class="eco-tag">Tapez le nom d\'un produit du quotidien. On le retrouve sur Jumia, '
    'et l\'IA vous dit dans quelle poubelle le trier.</p>',
    unsafe_allow_html=True,
)

col_input, col_btn = st.columns([5, 1])
with col_input:
    st.text_input(
        "Nom du produit", key="champ_recherche",
        placeholder="bouteille d'eau, bocal de confiture, ecouteurs...",
        label_visibility="collapsed", on_change=lancer_recherche,
    )
with col_btn:
    st.button("Rechercher", on_click=lancer_recherche, use_container_width=True)

st.write("")


def _prix_affichage(prix: str) -> str:
    """
    Raccourcit une fourchette de prix ('4 522 FCFA - 5 250 FCFA') en gardant
    seulement le prix de depart suivi de '+', pour tenir sur une ligne.
    Un prix simple est renvoye tel quel.
    """
    if prix and "-" in prix:
        debut = prix.split("-")[0].strip()
        return f"{debut}+"
    return prix


def carte_produit_html(produit: dict) -> str:
    badge = ""
    if produit.get("remise"):
        badge = f'<div class="pcard-badge">-{produit["remise"]}%</div>'
    prix = _prix_affichage(produit["prix"])
    return f"""
    <div class="pcard">
        <div class="pcard-imgwrap">{badge}
            <img src="{produit['image_url']}" alt="{produit['nom']}">
        </div>
        <div class="pcard-body">
            <div class="pcard-name">{produit['nom']}</div>
            <div class="pcard-price">{prix}</div>
        </div>
    </div>
    """


# ---------------------------------------------------------------------------
# 1) Ecran RESULTAT (prioritaire)
# ---------------------------------------------------------------------------
if st.session_state.prediction is not None:
    pred = st.session_state.prediction
    produit = st.session_state.produit_choisi

    st.markdown(f'<div class="eyebrow">Produit analyse</div>'
                f'<div class="section-hint">{produit["nom"]}</div>', unsafe_allow_html=True)

    if pred["confiance"] < SEUIL_CONFIANCE:
        st.markdown(f"""
        <div class="result-panel" style="background:#EEF1F0; color:#2B3A33;">
            <div class="result-emoji">🤔</div>
            <div class="result-bin">Resultat incertain</div>
            <div class="result-mat">L'IA n'est pas assez sure pour ce produit</div>
            <div class="result-desc">
                Confiance de {pred['confiance']:.0%}, sous le seuil de {SEUIL_CONFIANCE:.0%}.
                Verifiez la matiere de l'emballage vous-meme, ou reessayez avec un produit
                plus proche du votre.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        infos = infos_poubelle(pred["classe_matiere"])
        st.markdown(f"""
        <div class="result-panel" style="background:{infos['couleur']}; color:{infos['couleur_texte']};">
            <div class="result-emoji">{infos['emoji']}</div>
            <div class="result-bin">{infos['nom']}</div>
            <div class="result-mat">Matiere detectee : {infos['matiere']}</div>
            <div class="result-desc">{infos['description']}</div>
            <div class="result-pill">Confiance de l'IA : {pred['confiance']:.0%}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    c1, c2, _ = st.columns([1.2, 1.2, 3])
    with c1:
        if st.button("Retour aux resultats", use_container_width=True):
            st.session_state.prediction = None
            st.rerun()
    with c2:
        if st.button("Nouvelle recherche", use_container_width=True):
            st.session_state.resultats = None
            st.session_state.prediction = None
            st.rerun()

# ---------------------------------------------------------------------------
# 2) Ecran RESULTATS de recherche
# ---------------------------------------------------------------------------
elif st.session_state.resultats is not None:
    resultats = st.session_state.resultats
    if len(resultats) == 0:
        st.markdown('<div class="eyebrow">Aucun resultat</div>'
                    '<div class="section-title">Rien trouve pour cette recherche</div>'
                    '<div class="section-hint">Essayez un mot-cle plus simple ou plus courant '
                    '— par exemple "bouteille", "cahier" ou "bocal".</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="eyebrow">Resultats Jumia</div>'
                    f'<div class="section-title">{len(resultats)} produits trouves</div>'
                    f'<div class="section-hint">Choisissez celui qui correspond a ce que vous '
                    f'avez en main.</div>', unsafe_allow_html=True)
        cols = st.columns(len(resultats))
        for i, produit in enumerate(resultats):
            with cols[i]:
                st.markdown(carte_produit_html(produit), unsafe_allow_html=True)
                st.button("Choisir", key=f"choix_{i}", on_click=analyser_produit,
                          args=(produit,), use_container_width=True)

# ---------------------------------------------------------------------------
# 3) Ecran ACCUEIL : les 5 poubelles
# ---------------------------------------------------------------------------
else:
    st.markdown('<div class="eyebrow">Guide de tri</div>'
                '<div class="section-title">Les 5 destinations possibles</div>'
                '<div class="section-hint">Chaque produit analyse tombe dans l\'une de ces '
                'categories.</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    for col, (code, p) in zip(cols, POUBELLES.items()):
        with col:
            st.markdown(f"""
            <div class="bin-tile" style="--tilecolor:{p['couleur']};">
                <div class="be">{p['emoji']}</div>
                <div class="bn">{p['nom']}</div>
                <div class="bd">{p['description']}</div>
            </div>
            """, unsafe_allow_html=True)
