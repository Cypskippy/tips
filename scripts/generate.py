#!/usr/bin/env python3
"""generate.py — Génère des articles Markdown à partir d'une liste de mots‑clés.

✅ Points clés :
    • Prompt verrouillé sur le sujet EXACT pour éviter les hors‑sujets.
    • Température réduite (0.3) pour moins de dérives.
    • Validation : le mot‑clé doit apparaître ≥ 3 fois, sinon on retente (3 essais max).
    • `wordcount` ajouté au front‑matter, et `robots: noindex` si < 600 mots.
    • Compatible GitHub Actions (aucune dépendance exotique hors bs4/markdown/openai).
"""

from __future__ import annotations
import os
import csv
import datetime as dt
from pathlib import Path
from typing import Final

import markdown
from bs4 import BeautifulSoup
from openai import OpenAI

###########################################################################
# Configuration
###########################################################################
# ➜ Variables d'environnement (préférées car masquées dans GitHub Actions)
MODEL: Final[str] = os.getenv("LLM_MODEL", "gpt-4o-mini")
TEMP: Final[float] = float(os.getenv("LLM_TEMP", "0.3"))  # 0.3 = ton plus stable
OPENAI_KEY: Final[str] = os.getenv("OPENAI_API_KEY", "")

if not OPENAI_KEY:
    raise RuntimeError("OPENAI_API_KEY est manquant dans les variables d'env !")

client = OpenAI()
OUTPUT_DIR = Path("_tips")
OUTPUT_DIR.mkdir(exist_ok=True)

###########################################################################
# Helper : appel LLM
###########################################################################

def llm(prompt: str) -> str:
    """Envoie le prompt au LLM et renvoie le contenu brut."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=TEMP,
    )
    return response.choices[0].message.content.strip()

###########################################################################
# Génération d'un article
###########################################################################

def generate_article(keyword: str) -> None:
    """Génère un article et l'enregistre dans _tips/slug.md."""

    slug = keyword.replace(" ", "-").lower()
    outfile = OUTPUT_DIR / f"{slug}.md"

    base_prompt = (
        "Rédige un article de blog de 900 à 1 200 mots en français, "
        f"uniquement sur le sujet EXACT suivant, sans t’en éloigner : « {keyword} ». "
        "Utilise H2/H3, ajoute une conclusion pratique et une FAQ de 3 questions. "
        "Ne traite AUCUN autre thème."
    )

    # Boucle de validation — max 3 tentatives
    attempts = 0
    while attempts < 3:
        attempts += 1
        body_md = llm(base_prompt)
        # Vérifie la présence du mot‑clé principal ≥ 3 fois dans le contenu
        if body_md.lower().count(keyword.split()[0].lower()) >= 3:
            break
        print(f"↻ Hors sujet pour ‘{keyword}’ — nouvelle tentative {attempts}/3…")
    else:
        body_md = (
            f"# {keyword}\n\n"
            "Contenu non disponible – génération hors sujet après 3 tentatives."
        )

    # Calcul du nombre de mots (HTML ➜ texte brut)
    html_body = markdown.markdown(body_md)
    wordcount = len(BeautifulSoup(html_body, "html.parser").get_text().split())

    # Front‑matter YAML :
    fm = {
        "title": keyword.title(),
        "date": dt.date.today().isoformat(),
        "last_updated": dt.date.today().isoformat(),
        "wordcount": wordcount,
    }
    if wordcount < 600:
        fm["robots"] = "noindex"

    # Conversion dict ➜ YAML simple
    front_matter = "---\n" + "\n".join(f"{k}: {v}" for k, v in fm.items()) + "\n---\n\n"

    outfile.write_text(front_matter + body_md, encoding="utf‑8")
    print(f"✓ {outfile.relative_to(Path.cwd())} — {wordcount} mots")

###########################################################################
# Point d'entrée : lit keywords.csv et lance la génération
###########################################################################

def main() -> None:
    keywords_csv = Path("keywords.csv")
    if not keywords_csv.exists():
        print("⚠️  keywords.csv introuvable ; rien à générer.")
        return

    with keywords_csv.open(newline="", encoding="utf‑8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            keyword = row[0].strip()
            if keyword:
                generate_article(keyword)

if __name__ == "__main__":
    main()
