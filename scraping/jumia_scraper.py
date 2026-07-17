"""
jumia_scraper.py — Scraper de recherche pour Jumia Cote d'Ivoire (jumia.ci).

Fournit search_jumia() pour l'application EcoSort-Search. Base sur
requests + BeautifulSoup (contenu produits present dans le HTML brut,
verifie via Ctrl+U).

CONTRAT D'INTERFACE (identique au mock, remplacement transparent) :

    search_jumia(keyword, max_results=5) -> list[dict]
        Chaque produit : {"nom", "prix", "remise", "image_url", "lien"}

    search_jumia_detaille(keyword, max_results=5) -> dict
        Variante qui expose le STATUT ("ok" | "vide" | "bloque" | "erreur_reseau")
        pour distinguer les causes d'echec. search_jumia() en est un wrapper.

Comportements cles :
  - Pagination de SECOURS : la page 1 est scrapee d'abord ; on ne va chercher
    la page suivante QUE si la page 1 ne fournit pas assez de produits valides
    (rapide dans le cas normal, robuste dans le cas limite).
  - Requetes multi-mots correctement transmises ("bluetooth sans fil oraimo").
  - Detection de blocage anti-bot, retry + backoff, Session persistante,
    throttling, logging.

Note selecteurs : article.prd / a.core / h3.name / div.prc sont verifies par
inspection du site a un instant T. Si Jumia change sa structure, le scraper
loggue un avertissement au lieu d'echouer silencieusement.
"""

import logging
import random
import re
import time

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("jumia_scraper")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] jumia_scraper: %(message)s"))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)

BASE_URL = "https://www.jumia.ci"
SEARCH_URL = BASE_URL + "/catalog/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

MIN_RESULTATS = 3       # seuil en dessous duquel on tente la page suivante
MAX_RESULTATS = 5       # borne haute (contrat "3 a 5 resultats")
MAX_PAGES = 3           # nombre max de pages a parcourir en secours

TIMEOUT = 12
NB_TENTATIVES = 3
DELAI_BASE = 1.5
DELAI_COURTOISIE = (0.5, 1.2)

SIGNES_BLOCAGE = (
    "cf-browser-verification", "cf-challenge", "cloudflare",
    "captcha", "g-recaptcha", "hcaptcha",
    "attention required", "checking your browser",
    "access denied", "request unsuccessful",
    "px-captcha", "perimeterx", "akamai",
)

_session = requests.Session()
_session.headers.update(HEADERS)


# ---------------------------------------------------------------------------
# Extraction des champs d'une carte produit
# ---------------------------------------------------------------------------
def _texte(element) -> str:
    return element.get_text(strip=True) if element else ""


def _parse_remise(carte) -> int:
    badge = carte.select_one(".bdg._dsct, ._dsct, [class*='dsct']")
    if badge:
        m = re.search(r"(\d+)\s*%", badge.get_text())
        if m:
            return int(m.group(1))
    lien = carte.select_one("a.core")
    if lien and lien.get("data-ga4-discount"):
        try:
            return int(round(float(lien["data-ga4-discount"])))
        except (ValueError, TypeError):
            pass
    return 0


def _parse_image(carte) -> str:
    img = carte.select_one("img.img") or carte.select_one("img")
    if not img:
        return ""
    return img.get("data-src") or img.get("src") or ""


def _parse_lien(carte) -> str:
    lien = carte.select_one("a.core")
    if not lien or not lien.get("href"):
        return BASE_URL
    href = lien["href"]
    return href if href.startswith("http") else BASE_URL + href


def _parse_nom(carte) -> str:
    lien = carte.select_one("a.core")
    if lien and lien.get("data-ga4-item_name"):
        return lien["data-ga4-item_name"].strip()
    return _texte(carte.select_one("h3.name"))


def _carte_vers_produit(carte):
    nom = _parse_nom(carte)
    prix = _texte(carte.select_one("div.prc"))
    image_url = _parse_image(carte)
    lien = _parse_lien(carte)
    remise = _parse_remise(carte)
    if not nom or not image_url:
        return None
    return {
        "nom": nom,
        "prix": prix or "Prix indisponible",
        "remise": remise,
        "image_url": image_url,
        "lien": lien,
    }


def _extraire_produits(html: str, limite: int, deja_vus: set) -> list:
    """
    Extrait les produits d'une page HTML, en evitant les doublons (via le
    lien produit, cle unique). S'arrete a `limite` produits.

    `deja_vus` : ensemble des liens deja collectes (mute par la fonction).
    """
    soup = BeautifulSoup(html, "html.parser")
    cartes = soup.select("article.prd")
    produits = []
    for carte in cartes:
        if len(produits) >= limite:
            break
        try:
            produit = _carte_vers_produit(carte)
        except Exception as exc:
            logger.debug("carte non exploitable (%s).", type(exc).__name__)
            continue
        if not produit:
            continue
        if produit["lien"] in deja_vus:
            continue  # doublon entre pages
        deja_vus.add(produit["lien"])
        produits.append(produit)
    return produits


# ---------------------------------------------------------------------------
# Detection de blocage anti-bot
# ---------------------------------------------------------------------------
def _page_est_bloquee(html: str, status_code: int) -> bool:
    if status_code in (403, 429, 503):
        return True
    echantillon = html[:6000].lower()
    return any(signe in echantillon for signe in SIGNES_BLOCAGE)


# ---------------------------------------------------------------------------
# Requete d'UNE page avec retry + backoff exponentiel
# ---------------------------------------------------------------------------
def _requete_page(keyword: str, page: int = 1):
    """
    Recupere une page de resultats. Multi-mots gere : `keyword` est passe
    tel quel comme valeur du parametre q (requests l'encode correctement).

    Returns (statut, html) ou statut in {"ok", "bloque", "erreur_reseau"}.
    """
    params = {"q": keyword}
    if page > 1:
        params["page"] = page  # Jumia pagine via ?page=N

    for tentative in range(1, NB_TENTATIVES + 1):
        time.sleep(random.uniform(*DELAI_COURTOISIE))  # throttling
        try:
            reponse = _session.get(SEARCH_URL, params=params, timeout=TIMEOUT)
        except requests.RequestException as exc:
            logger.warning(
                "page %d, tentative %d/%d : erreur reseau (%s)",
                page, tentative, NB_TENTATIVES, type(exc).__name__,
            )
        else:
            if _page_est_bloquee(reponse.text, reponse.status_code):
                logger.warning(
                    "page %d, tentative %d/%d : blocage anti-bot (code %d)",
                    page, tentative, NB_TENTATIVES, reponse.status_code,
                )
                if reponse.status_code in (403, 429, 503) and tentative < NB_TENTATIVES:
                    time.sleep(DELAI_BASE * (2 ** tentative))
                    continue
                return "bloque", reponse.text
            if reponse.status_code == 200:
                return "ok", reponse.text
            logger.warning(
                "page %d, tentative %d/%d : code HTTP inattendu %d",
                page, tentative, NB_TENTATIVES, reponse.status_code,
            )
        if tentative < NB_TENTATIVES:
            time.sleep(DELAI_BASE * (2 ** (tentative - 1)))

    return "erreur_reseau", None


# ---------------------------------------------------------------------------
# Fonction principale (variante detaillee) avec pagination de secours
# ---------------------------------------------------------------------------
def search_jumia_detaille(keyword: str, max_results: int = MAX_RESULTATS) -> dict:
    """
    Recherche `keyword` sur Jumia CI, avec statut explicite et pagination
    de secours.

    Returns :
        {
          "statut": "ok" | "vide" | "bloque" | "erreur_reseau",
          "produits": list[dict],
          "message": str
        }

    Pagination de SECOURS : on scrape la page 1 ; si elle fournit deja assez
    de produits (>= limite demandee), on s'arrete la (cas normal, rapide).
    Sinon on va chercher les pages suivantes (jusqu'a MAX_PAGES) pour
    completer, jusqu'a atteindre la limite ou manquer de resultats.

    Multi-mots : "bluetooth sans fil oraimo" est transmis en entier.

    max_results est une LIMITE DURE bornee a [MIN_RESULTATS=3, MAX_RESULTATS=5]
    (choix de conception, coherent avec le cahier des charges "3 a 5 resultats").
    """
    keyword = " ".join((keyword or "").split()).strip()  # normalise les espaces
    if not keyword:
        return {"statut": "vide", "produits": [], "message": "Mot-cle vide."}

    limite = max(MIN_RESULTATS, min(max_results, MAX_RESULTATS))
    produits = []
    deja_vus = set()
    structure_ok = False  # a-t-on vu au moins une carte article.prd ?

    for page in range(1, MAX_PAGES + 1):
        statut, html = _requete_page(keyword, page)

        if statut == "erreur_reseau":
            if produits:  # on a deja des resultats des pages precedentes
                break
            return {"statut": "erreur_reseau", "produits": [],
                    "message": "Impossible de joindre Jumia (reseau/timeout) "
                               f"apres {NB_TENTATIVES} tentatives."}
        if statut == "bloque":
            if produits:
                break
            return {"statut": "bloque", "produits": [],
                    "message": "Jumia a servi une page anti-bot (blocage). "
                               "Reessayez plus tard ou depuis une autre connexion."}

        # Page recuperee : la structure contient-elle des cartes ?
        if "article" in html and "prd" in html:
            structure_ok = True

        nouveaux = _extraire_produits(html, limite - len(produits), deja_vus)
        produits.extend(nouveaux)

        # Assez de produits -> on s'arrete (pagination de secours : page 1
        # suffit dans le cas normal, on ne pagine que si necessaire).
        if len(produits) >= limite:
            break
        # Page sans nouveau produit -> plus rien a paginer, on arrete.
        if not nouveaux:
            logger.debug("page %d sans nouveau produit : arret pagination.", page)
            break

    if not produits:
        if not structure_ok:
            logger.warning(
                "0 carte 'article.prd' trouvee pour '%s' : aucun resultat, "
                "ou structure HTML de Jumia modifiee (selecteurs a verifier).",
                keyword,
            )
        return {"statut": "vide", "produits": [],
                "message": f"Aucun produit trouve pour '{keyword}'."}

    return {"statut": "ok", "produits": produits,
            "message": f"{len(produits)} produit(s) trouve(s)."}


def search_jumia(keyword: str, max_results: int = MAX_RESULTATS) -> list:
    """
    Wrapper compatible avec le contrat du mock : retourne directement la
    liste de produits (vide en cas d'echec, quel qu'il soit).
    Pour distinguer les causes d'echec, utiliser search_jumia_detaille().
    """
    return search_jumia_detaille(keyword, max_results)["produits"]


# ---------------------------------------------------------------------------
# Test manuel :  python jumia_scraper.py bluetooth sans fil oraimo
# (tous les mots apres le nom du script forment la requete)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    # Recolle TOUS les arguments en une seule requete (corrige le bug
    # ou seul le premier mot etait pris en compte).
    mot = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "bouteille"
    print(f"Recherche Jumia CI : '{mot}'\n")
    debut = time.time()
    res = search_jumia_detaille(mot)
    duree = time.time() - debut

    print(f"Statut  : {res['statut']}")
    print(f"Message : {res['message']}\n")
    for i, p in enumerate(res["produits"], 1):
        print(f"{i}. {p['nom']}")
        print(f"   Prix   : {p['prix']}  (remise -{p['remise']}%)")
        print(f"   Image  : {p['image_url'][:70]}...")
        print(f"   Lien   : {p['lien'][:70]}...")
        print()
    print(f"({len(res['produits'])} produits en {duree:.1f}s)")
