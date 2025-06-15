\#!/usr/bin/env python3
"""generate.py — Génère des articles Markdown à partir d'une liste de mots-clés.

Version corrigée :
• Validation de mot-clé.
• wordcount + noindex.
• Impression du chemin sans relative\_to pour éviter ValueError sur GitHub Actions.
"""

from **future** import annotations
import os
import csv
import datetime as dt
from pathlib import Path
from typing import Final

import markdown
from bs4 import BeautifulSoup
from openai import OpenAI

MODEL: Final\[str] = os.getenv("LLM\_MODEL", "gpt-4o-mini")
TEMP: Final\[float] = float(os.getenv("LLM\_TEMP", "0.3"))
OPENAI\_KEY: Final\[str] = os.getenv("OPENAI\_API\_KEY", "")
if not OPENAI\_KEY:
raise RuntimeError("OPENAI\_API\_KEY est manquant !")

client = OpenAI()
OUTPUT\_DIR = Path("\_tips")
OUTPUT\_DIR.mkdir(parents=True, exist\_ok=True)

def llm(prompt: str) -> str:
resp = client.chat.completions.create(
model=MODEL,
messages=\[{"role": "user", "content": prompt}],
temperature=TEMP,
)
return resp.choices\[0].message.content.strip()

def generate\_article(keyword: str) -> None:
slug = keyword.replace(" ", "-").lower()
outfile = OUTPUT\_DIR / f"{slug}.md"

```
base_prompt = (
    "Rédige un article de blog de 900 à 1 200 mots en français, "
    f"uniquement sur le sujet EXACT suivant, sans t’en éloigner : « {keyword} ». "
    "Utilise H2/H3, ajoute une conclusion pratique et une FAQ de 3 questions. "
    "Ne traite AUCUN autre thème."
)

attempts = 0
while attempts < 3:
    attempts += 1
    body_md = llm(base_prompt)
    if body_md.lower().count(keyword.split()[0].lower()) >= 3:
        break
    print(f"↻ Hors sujet pour ‘{keyword}’ — tentative {attempts}/3…")
else:
    body_md = f"# {keyword}\n\nContenu non disponible — génération hors sujet."

html_body = markdown.markdown(body_md)
wordcount = len(BeautifulSoup(html_body, "html.parser").get_text().split())

fm = {
    "title": keyword.title(),
    "date": dt.date.today().isoformat(),
    "last_updated": dt.date.today().isoformat(),
    "wordcount": wordcount,
}
if wordcount < 600:
    fm["robots"] = "noindex"

front_matter = "---\n" + "\n".join(f"{k}: {v}" for k, v in fm.items()) + "\n---\n\n"
outfile.write_text(front_matter + body_md, encoding="utf-8")
print(f"✓ {outfile} — {wordcount} mots")
```

def main() -> None:
csv\_file = Path("keywords.csv")
if not csv\_file.exists():
print("⚠️  keywords.csv introuvable.")
return

```
with csv_file.open(newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        if row and row[0].strip():
            generate_article(row[0].strip())
```

if **name** == "**main**":
main()
