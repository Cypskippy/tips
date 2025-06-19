#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate.py – create Markdown articles from keywords.csv via OpenAI.

Process:
1. Read keywords.csv (one keyword per line).
2. For each keyword, call the model (LLM_MODEL env var, default gpt-4o-mini).
3. Accept the result if the keyword appears at least 3 times; otherwise retry 2x.
4. Write the article to _tips/<slug>.md with YAML front‑matter.
5. Add robots: noindex when the article is under 600 words.

Progress is printed so GitHub Actions logs stay active.
"""

from __future__ import annotations

import csv
import datetime as dt
import os
from pathlib import Path
from typing import Final

from bs4 import BeautifulSoup  # pip install beautifulsoup4
import markdown                 # pip install Markdown
from openai import OpenAI, OpenAIError  # pip install openai

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
MODEL: Final[str] = os.getenv("LLM_MODEL", "gpt-4o-mini")
TEMP: Final[float] = float(os.getenv("LLM_TEMP", "0.3"))
API_KEY: Final[str] = os.getenv("OPENAI_API_KEY", "")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing")

client = OpenAI()
OUTPUT_DIR = Path("_tips")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------
# OpenAI helper
# ----------------------------------------------------------------------------

def call_llm(prompt: str) -> str:
    """Call the chat model (60‑s timeout) and return text."""
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            temperature=TEMP,
            messages=[{"role": "user", "content": prompt}],
            timeout=60,
        )
        return resp.choices[0].message.content.strip()
    except OpenAIError as err:
        print(f"[OpenAI error] {err}")
        return ""

# ----------------------------------------------------------------------------
# File writer
# ----------------------------------------------------------------------------

def save_article(keyword: str, text: str) -> None:
    slug = keyword.replace(" ", "-").lower()
    path = OUTPUT_DIR / f"{slug}.md"

    wordcount = len(
        BeautifulSoup(markdown.markdown(text), "html.parser").get_text().split()
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
    path.write_text(front + text, encoding="utf-8")
    print(f"✓ {path} ({wordcount} words)")

# ----------------------------------------------------------------------------
# Article generator
# ----------------------------------------------------------------------------

def generate(keyword: str) -> None:
    print(f"→ {keyword}")

    prompt = (
        "Rédige un article de 900 à 1200 mots en français uniquement sur : "
        f"« {keyword} ». Utilise des titres H2/H3, conclus par une FAQ."
    )

    for attempt in range(3):
        text = call_llm(prompt)
        if text and text.lower().count(keyword.split()[0].lower()) >= 3:
            save_article(keyword, text)
            return
        print(f"  retry {attempt + 1}/3 – hors sujet")

    save_article(keyword, f"# {keyword}\n\nContenu non disponible – hors sujet.")

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> None:
    csv_path = Path("keywords.csv")
    if not csv_path.exists():
        print("keywords.csv not found – aborting.")
        return

    with csv_path.open(encoding="utf-8", newline="") as f:
        for row in csv.reader(f):
            if row and row[0].strip():
                generate(row[0].strip())


if __name__ == "__main__":
    main()
