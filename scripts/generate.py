#!/usr/bin/env python3
"""generate.py

Generate Markdown articles from keywords.csv using OpenAI.
Steps:

1. Read keywords.csv (one keyword per line).
2. Call the model (LLM\_MODEL, default gpt-4o-mini) for each keyword.
3. Check that the keyword appears ≥ 3 times; retry up to 3 times.
4. Save the article to \_tips/<slug>.md with YAML front‑matter.
5. Add `robots: noindex` if the article has < 600 words.

Progress is printed for every keyword so GitHub Actions logs stay alive.
"""

from **future** import annotations

import csv
import datetime as dt
import os
from pathlib import Path
from typing import Final

from bs4 import BeautifulSoup  # pip install beautifulsoup4
import markdown                # pip install Markdown
from openai import OpenAI, OpenAIError  # pip install openai

# ---------------------------------------------------------------------------

# Configuration

# ---------------------------------------------------------------------------

MODEL: Final\[str] = os.getenv("LLM\_MODEL", "gpt-4o-mini")
TEMP: Final\[float] = float(os.getenv("LLM\_TEMP", "0.3"))
API\_KEY: Final\[str] = os.getenv("OPENAI\_API\_KEY", "")

if not API\_KEY:
raise RuntimeError("OPENAI\_API\_KEY is missing")

client = OpenAI()
OUTPUT\_DIR = Path("\_tips")
OUTPUT\_DIR.mkdir(parents=True, exist\_ok=True)

# ---------------------------------------------------------------------------

# OpenAI helper

# ---------------------------------------------------------------------------

def call\_llm(prompt: str) -> str:
"""Call the chat model with a 60‑second timeout."""
try:
resp = client.chat.completions.create(
model=MODEL,
temperature=TEMP,
messages=\[{"role": "user", "content": prompt}],
timeout=60,
)
return resp.choices\[0].message.content.strip()
except OpenAIError as err:
print(f"⚠️  OpenAI error: {err}")
return ""

# ---------------------------------------------------------------------------

# File writing

# ---------------------------------------------------------------------------

def save\_article(keyword: str, text: str) -> None:
slug = keyword.replace(" ", "-").lower()
path = OUTPUT\_DIR / f"{slug}.md"

```
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
print(f"✓ {path}  ({wordcount} words)")
```

# ---------------------------------------------------------------------------

# Article generation

# ---------------------------------------------------------------------------

def generate(keyword: str) -> None:
print(f"→ Generating: {keyword}")

```
prompt = (
    "Rédige un article de 900 à 1200 mots en français exclusivement sur le sujet : "
    f"« {keyword} ». Utilise des titres H2/H3, termine par une conclusion pratique et une FAQ."
)

for attempt in range(3):
    text = call_llm(prompt)
    if text and text.lower().count(keyword.split()[0].lower()) >= 3:
        save_article(keyword, text)
        return
    print(f"  ↻ retry {attempt + 1}/3 (topic drift)")

# fallback
save_article(keyword, f"# {keyword}\n\nContenu non disponible – hors sujet.")
```

# ---------------------------------------------------------------------------

# Main entry point

# ---------------------------------------------------------------------------

def main() -> None:
csv\_path = Path("keywords.csv")
if not csv\_path.exists():
print("keywords.csv not found – aborting.")
return

```
with csv_path.open(newline="", encoding="utf-8") as f:
    for row in csv.reader(f):
        if row and row[0].strip():
            generate(row[0].strip())
```

if **name** == "**main**":
main()
