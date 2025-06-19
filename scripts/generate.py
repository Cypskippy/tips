#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""generate.py – génère des articles Markdown listés dans keywords.csv.

Fonctionnement :

1. Lit keywords.csv.
2. Pour chaque mot‑clé, interroge l’API OpenAI (modèle défini via \$LLM\_MODEL).
3. Vérifie que le mot‑clé apparaît ≥ 3 fois pour valider le sujet.
4. Écrit un fichier *md* dans \_tips/ avec un front‑matter YAML complet.
5. Ajoute robots: noindex si l’article fait moins de 600 mots.

Le script affiche la progression dans stdout, ce qui permet de suivre le job
GitHub Actions. 
"""

from **future** import annotations

import csv
import datetime as dt
import os
from pathlib import Path
from typing import Final

import markdown               # pip install Markdown
from bs4 import BeautifulSoup  # pip install beautifulsoup4
from openai import OpenAI      # pip install openai

# ---------------------------------------------------------------------------

# Configuration

# ---------------------------------------------------------------------------

MODEL: Final\[str] = os.getenv("LLM\_MODEL", "gpt-4o-mini")
TEMP: Final\[float] = float(os.getenv("LLM\_TEMP", "0.3"))
API\_KEY: Final\[str] = os.getenv("OPENAI\_API\_KEY", "")

if not API\_KEY:
raise RuntimeError("OPENAI\_API\_KEY manquant dans les variables d’environnement.")

client = OpenAI()
OUTPUT\_DIR = Path("\_tips")
OUTPUT\_DIR.mkdir(parents=True, exist\_ok=True)

# ---------------------------------------------------------------------------

# Helpers

# ---------------------------------------------------------------------------

def llm(prompt: str) -> str:
"""Retourne la réponse brute du modèle OpenAI."""
response = client.chat.completions.create(
model=MODEL,
temperature=TEMP,
messages=\[{"role": "user", "content": prompt}],
timeout=60,  # 1 minute max par appel
)
return response.choices\[0].message.content.strip()

def save\_article(keyword: str, body\_md: str) -> None:
"""Écrit l’article dans \_tips/ avec front‑matter YAML."""
slug = keyword.replace(" ", "-").lower()
path = OUTPUT\_DIR / f"{slug}.md"

```
# Calcul du nombre de mots
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
print(f"✓ écrit : {path}  ({wordcount} mots)")
```

# ---------------------------------------------------------------------------

# Génération d’un article

# ---------------------------------------------------------------------------

def generate\_article(keyword: str) -> None:
print(f"• Génération : {keyword}")

```
prompt = (
    "Rédige un article de 900 à 1 200 mots en français, uniquement sur : "
    f"« {keyword} ». Utilise des H2/H3, termine par une conclusion pratique et une FAQ.\n"
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
```

# ---------------------------------------------------------------------------

# Point d’entrée

# ---------------------------------------------------------------------------

def main() -> None:
csv\_file = Path("keywords.csv")
if not csv\_file.exists():
print("⚠️  keywords.csv introuvable – aucune génération.")
return

```
with csv_file.open(encoding="utf-8", newline="") as f:
    for row in csv.reader(f):
        if row and row[0].strip():
            generate_article(row[0].strip())
```

if **name** == "**main**":
main()
