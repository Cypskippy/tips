#!/usr/bin/env python3
"""Generate or update markdown articles from keywords.csv
- Internal linking (Articles connexes)
- AI‑generated FAQ + JSON‑LD Schema
- Stub for MaPrimeRénov' barèmes refresh
"""
import csv
import datetime
import json
import os
import random
import pathlib

import frontmatter
import openai
from slugify import slugify

# ---------- Config ---------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
KEYWORDS_CSV = ROOT / "keywords.csv"
MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
BATCH = int(os.getenv("BATCH", 5))
openai.api_key = os.environ["OPENAI_API_KEY"]

# ---------- Helpers --------------------------------------------------------

def llm(prompt: str) -> str:
    """Call the LLM and return plain text."""
    resp = openai.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


def build_related(slug: str) -> str:
    """Return a markdown section listing up to 3 internal links."""
    others = [p.stem for p in CONTENT_DIR.glob("*.md") if p.stem != slug]
    if not others:
        return ""
    links = random.sample(others, k=min(3, len(others)))
    bullets = "
".join(
        f"- [{l.replace('-', ' ').title()}](/{l}/)" for l in links
    )
    return f"

## Articles connexes
{bullets}
"


def build_faq(keyword: str) -> tuple[str, str]:
    """Return (markdown FAQ, JSON‑LD FAQPage)."""
    qa_prompt = (
        "Donne deux questions fréquentes très courtes (max 12 mots) avec leur réponse concise (1 phrase) "
        f"au sujet : {keyword}. Format : Q:question puis A:réponse sur la ligne suivante. Répète pour la 2ᵉ question."
    )
    qa_raw = llm(qa_prompt)
    lines = [l.strip() for l in qa_raw.splitlines() if l.strip()]
    pairs: list[tuple[str, str]] = []
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            q = lines[i].lstrip("Qq: ").strip()
            a = lines[i + 1].lstrip("Aa: ").strip()
            pairs.append((q, a))

    if not pairs:
        return "", ""

    md_part = "

## FAQ
" + "

".join(f"**{q}**
: {a}" for q, a in pairs)

    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in pairs
        ],
    }
    json_ld = (
        "

<script type=\"application/ld+json\">
"
        + json.dumps(schema, ensure_ascii=False, indent=2)
        + "
</script>
"
    )
    return md_part, json_ld

# ---------- Core -----------------------------------------------------------

def generate_article(keyword: str):
    slug = slugify(keyword)[:90]
    path = CONTENT_DIR / f"{slug}.md"
    today = datetime.date.today().isoformat()

    # Front‑matter
    if path.exists():
        post = frontmatter.load(path)
    else:
        post = frontmatter.loads("")
        post["title"] = keyword.title()
        post["date"] = today
    post["last_updated"] = today

    # Main body
    outline = llm(
        "Rédige un article de blog de 500 mots en français, structuré (h2/h3), avec une introduction claire, "
        "un tableau si pertinent, et une conclusion pratique. Sujet : " + keyword
    )

    faq_md, faq_json = build_faq(keyword)
    related_md = build_related(slug)

    post.content = outline + faq_md + related_md + faq_json

    CONTENT_DIR.mkdir(exist_ok=True)
    frontmatter.dump(post, path, sort_keys=False)
    print(f"✅ {slug} mis à jour")


def main():
    with KEYWORDS_CSV.open() as f:
        keywords = [row[0].strip() for row in csv.reader(f) if row and row[0].strip()]

    pending = [kw for kw in keywords if not (CONTENT_DIR / f"{slugify(kw)}.md").exists()]
    for kw in pending[:BATCH]:
        generate_article(kw)


if __name__ == "__main__":
    main()
