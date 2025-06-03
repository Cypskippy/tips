#!/usr/bin/env python3
"""Generate or update markdown articles into _pages/ from keywords.csv.
Adds:
- Internal linking (Articles connexes)
- AI-generated FAQ + JSON-LD Schema.org block
- Ready for nightly GitHub Actions cron
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

# --- Configuration ---------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT / "_pages"          # <- use Jekyll collection folder
KEYWORDS_CSV = ROOT / "keywords.csv"
MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
BATCH = int(os.getenv("BATCH", 5))
openai.api_key = os.environ.get("OPENAI_API_KEY", "")

# --- Helpers ---------------------------------------------------------------

def llm(prompt: str) -> str:
    """Query the LLM and return plain text."""
    resp = openai.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


def build_related(slug: str) -> str:
    """Return a markdown section with up to 3 internal links."""
    others = [p.stem for p in PAGES_DIR.glob("*.md") if p.stem != slug]
    if not others:
        return ""
    links = random.sample(others, k=min(3, len(others)))
    bullets = "
".join([
        f"- [{l.replace('-', ' ').title()}](/{l}/)" for l in links
    ])
    return f"

## Articles connexes
{bullets}
"


def build_faq(keyword: str) -> (str, str):
    """Generate a two-question FAQ (markdown + JSON-LD)."""
    prompt = (
        "Donne deux questions fréquentes très courtes (max 12 mots) "
        "avec leur réponse concise (1 phrase) au sujet : " + keyword + ". "
        "Format : Q:question puis A:réponse sur la ligne suivante. Répète pour la 2ème question."
    )
    raw = llm(prompt)
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    pairs = []
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            q = lines[i].removeprefix("Q:").removeprefix("q:").strip()
            a = lines[i + 1].removeprefix("A:").removeprefix("a:").strip()
            pairs.append((q, a))

    if not pairs:
        return "", ""

    # Build Markdown part
    faq_md = "

## FAQ
"
    faq_md += "

".join([f"**{q}**
: {a}" for q, a in pairs])

    # Build JSON-LD
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": []
    }
    for q, a in pairs:
        schema["mainEntity"].append({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a}
        })
    faq_json = (
        "

<script type=\"application/ld+json\">
"
        + json.dumps(schema, ensure_ascii=False, indent=2)
        + "
</script>
"
    )
    return faq_md, faq_json

# --- Core generation -------------------------------------------------------

def generate_article(keyword: str) -> None:
    slug = slugify(keyword)[:90]
    path = PAGES_DIR / f"{slug}.md"
    today = datetime.date.today().isoformat()

    # Prepare frontmatter
    if path.exists():
        post = frontmatter.load(path)
    else:
        post = frontmatter.loads("")
        post["title"] = keyword.title()
        post["date"] = today
    post["last_updated"] = today

    # Generate main body
    body_prompt = (
        "Rédige un article de blog de 500 mots en français, structuré (h2/h3), "
        "avec une introduction claire, un tableau si pertinent, "
        "et une conclusion pratique. Sujet : " + keyword
    )
    body = llm(body_prompt)

    # Generate FAQ and related sections
    faq_md, faq_json = build_faq(keyword)
    related_md = build_related(slug)

    # Combine content
    post.content = body + faq_md + related_md + faq_json

    PAGES_DIR.mkdir(exist_ok=True)
    frontmatter.dump(post, path, sort_keys=False)
    print(f"✅ {slug} mis à jour")


def main() -> None:
    # Read all keywords
    with KEYWORDS_CSV.open() as f:
        keywords = [row[0].strip() for row in csv.reader(f) if row and row[0].strip()]

    # Determine which to generate
    pending = []
    for kw in keywords:
        slug = slugify(kw)[:90]
        if not (PAGES_DIR / f"{slug}.md").exists():
            pending.append(kw)
    for kw in pending[:BATCH]:
        generate_article(kw)


if __name__ == "__main__":
    main()
