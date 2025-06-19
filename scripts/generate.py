#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate.py — génère automatiquement des articles Markdown depuis keywords.csv.

Points clés :
• Sujet verrouillé (mot-clé ≥ 3 occurrences).
• wordcount + robots: noindex si < 600 mots.
• Chemin affiché simplement (pas de relative_to) pour GitHub Actions.
"""

from __future__ import annotations

import csv
import datetime as dt
import os
from pathlib import Path
from typing import Final

import markdown               # pip install Markdown
from bs4 import BeautifulSoup  # pip install beautifulsoup4
from openai import OpenAI      # pip install openai

###############################################################################
# Configuration
###############################################################################
MODEL: Final[str] = os.getenv("LLM_MODEL", "gpt-4o-mini")
TEMP: Final[float] = float(os.getenv("LLM_TEMP", "0.3"))
API_KEY: Final[str] = os.getenv("OPENAI_API_KEY", "")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY manquant dans les variables d’environnement.")

client = OpenAI()
OUTPUT_DIR = Path("_tips")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

###############################################################################
# Helpers
###############################################################################
def llm(prompt: str) -> str:
    """Interroge le modèle OpenAI et renvoie la réponse brute."""
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=TEMP,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


def save_article(keyword: str, body_md: str) -> None:
    """Enregistre l’article avec front-matter YAML."""
    slug = keyword.replace(" ", "-").lower()
    path = OUTPUT_DIR / f"{slug}.md"

    # Nombre de mots
    wordcount = len(
        BeautifulSoup(markdown.markdown(body_md), "html.parser")
        .get_text()
        .split()
    )

    fm = {
        "title": keyword.title(),
        "date": dt.date.today().isoformat(),
        "last_updated": dt.date.today().isoformat(),
        "wordcount": wordcount,
    }
    if wordcount < 600:
        fm["robots"] = "noindex"

    front = "---\n" + "\n".join(f"{k}: {v}" for k, v in fm.items()) + "\n---\n\n"
    path.write_text(front + body_md, encoding="utf-8")
    print(f"✓ écrit : {path} ({wordcount} mots)")

###############################################################################
# Génération principale
###############################################################################
def generate_article(keyword: str) -> None:
    prompt = (
        "Rédige un article de 900 à 1 200 mots en français, uniquement sur : "
        f"« {keyword} ». Utilise H2/H3, termine par une conclusion pratique et une FAQ.\n"
        "Ne traite aucun autre sujet."
    )

    for attempt in range(1, 4):
        body = llm(prompt)
        if body.lower().count(keyword.split()[0].lower()) >= 3:
            save_article(keyword, body)
            return
        print(f"↻ Hors sujet pour '{keyword}' (tentative {attempt}/3)…")

    # Fallback après 3 tentatives
    save_article(keyword, f"# {keyword}\n\nContenu non disponible – hors sujet.")

def main() -> None:
    csv_file = Path("keywords.csv")
    if not csv_file.exists():
        print("⚠️ keywords.csv introuvable – aucune génération.")
        return

    with csv_file.open(encoding="utf-8", newline="") as f:
        for row in csv.reader(f):
            if row and row[0].strip():
                generate_article(row[0].strip())

if __name__ == "__main__":
    main()
