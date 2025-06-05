#!/usr/bin/env python3
"""Generate or update markdown articles into _pages/ from keywords.csv.
Adds:
- Internal linking (Articles connexes)
- AI-generated FAQ + JSON-LD Schema.org block
- Skips empty lines in keywords.csv to avoid premature termination
- Wrapped LLM calls in try/except to log failures and continue
- Ready for nightly GitHub Actions cron
"""

import csv
import datetime
import json
import os
import random
import pathlib
import time

import frontmatter
import openai
from slugify import slugify

# --- Configuration ---------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT / "_tips"          # <- use Jekyll collection folder
KEYWORDS_CSV = ROOT / "keywords.csv"
MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
BATCH = int(os.getenv("BATCH", 5))

# Set your OpenAI API key in environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY", "")

# --- Helpers ---------------------------------------------------------------

def llm(prompt: str) -> str:
    """Query the LLM and return plain text. Retries up to 3 times on failure."""
    retries = 0
    while retries < 3:
        try:
            resp = openai.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            retries += 1
            print(f"  → Erreur LLM (essai {retries}/3) pour prompt : {e}")
            time.sleep(2)
    raise RuntimeError(f"Échec de l'appel LLM après 3 tentatives pour prompt: {prompt}")


def build_related(slug: str) -> str:
    """Return a markdown section with up to 3 internal links to other pages."""
    others = [p.stem for p in PAGES_DIR.glob("*.md") if p.stem != slug]
    if not others:
        return ""
    links = random.sample(others, k=min(3, len(others)))
    bullets = "\n".join([
        f"- [{l.replace('-', ' ').title()}](/{l}/)" for l in links
    ])
    return f"\n\n## Articles connexes\n{bullets}\n"


def build_faq(keyword: str) -> (str, str):
    """Generate a two-question FAQ (markdown + JSON-LD)."""
    prompt = (
        "Donne deux questions fréquentes très courtes (max 12 mots) "
        "avec leur réponse concise (1 phrase) au sujet : " + keyword + ". "
        "Format : Q:question puis A:réponse sur la ligne suivante. Répète pour la 2ème question."
    )
    try:
        raw = llm(prompt)
    except Exception as e:
        print(f"  ✗ Erreur génération FAQ pour '{keyword}': {e}")
        return "", ""
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
    faq_md = "\n\n## FAQ\n"
    faq_md += "\n\n".join([f"**{q}**\n: {a}" for q, a in pairs])

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
        "\n\n<script type=\"application/ld+json\">\n"
        + json.dumps(schema, ensure_ascii=False, indent=2)
        + "\n</script>\n"
    )
    return faq_md, faq_json

# --- Core generation -------------------------------------------------------

def generate_article(keyword: str) -> None:
    slug_base = slugify(keyword)[:90]
    slug = slug_base or f"mot-cle-{int(time.time())}"

    # Ensure unique slug (avoid overwriting existing)
    counter = 1
    target_path = PAGES_DIR / f"{slug}.md"
    while target_path.exists():
        slug = f"{slug_base}-{counter}"
        target_path = PAGES_DIR / f"{slug}.md"
        counter += 1

    today = datetime.date.today().isoformat()

    # Prepare frontmatter
    if target_path.exists():
        post = frontmatter.load(target_path)
    else:
        post = frontmatter.loads("")
        post["title"] = keyword.title()
        post["date"] = today
    post["last_updated"] = today

    # Generate main body
    try:
        body_prompt = (
            "Rédige un article de blog de 500 mots en français, structuré (h2/h3), "
            "avec une introduction claire, un tableau si pertinent, "
            "et une conclusion pratique. Sujet : " + keyword
        )
        body = llm(body_prompt)
    except Exception as e:
        print(f"  ✗ Erreur génération du corps pour '{keyword}': {e}")
        body = f"# {keyword}\n\nLe contenu n'a pas pu être généré pour ce mot-clé."

    # Generate FAQ and related sections
    faq_md, faq_json = build_faq(keyword)
    related_md = build_related(slug)

    # Combine content
    post.content = body + faq_md + related_md + faq_json

    # Ensure pages directory exists
    PAGES_DIR.mkdir(exist_ok=True)

    # Write to file
    try:
        frontmatter.dump(post, target_path, sort_keys=False)
        print(f"✅ {slug} mis à jour")
    except Exception as e:
        print(f"  ✗ Erreur écriture fichier pour '{keyword}' (slug='{slug}'): {e}")
        with open(ROOT / "logs" / "erreurs_generation.log", "a", encoding="utf-8") as log_f:
            log_f.write(f"{keyword} : impossible d'écrire {target_path} → {e}\n")


def main() -> None:
    # Prepare logs directory
    (ROOT / "logs").mkdir(exist_ok=True)

    # Read all keywords, skipping empty lines
    keywords = []
    with KEYWORDS_CSV.open(encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not row[0].strip():
                # Skip empty or whitespace-only lines
                continue
            keywords.append(row[0].strip())

    print(f"→ Nombre de mots-clés à traiter : {len(keywords)}")

    # Determine which to generate
    pending = []
    for kw in keywords:
        slug_test = slugify(kw)[:90] or f"mot-cle-{int(time.time())}"
        if not (PAGES_DIR / f"{slug_test}.md").exists():
            pending.append(kw)
    print(f"→ Nombre de mots-clés pendants : {len(pending)}")

    # Generate up to BATCH articles
    for kw in pending[:BATCH]:
        try:
            generate_article(kw)
        except Exception as e:
            # Log and continue on any unexpected failure
            print(f"  ✗ Erreur inattendue pour '{kw}': {e}")
            with open(ROOT / "logs" / "erreurs_generation.log", "a", encoding="utf-8") as log_f:
                log_f.write(f"{kw} : erreur inattendue → {e}\n")


if __name__ == "__main__":
    main()
