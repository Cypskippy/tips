#!/usr/bin/env python3
"""Génère ou met à jour  N articles Markdown à partir de keywords.csv."""
import csv, os, datetime, frontmatter, openai, pathlib
from slugify import slugify

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
openai.api_key = OPENAI_API_KEY
ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
KEYWORDS = ROOT / "keywords.csv"
BATCH = int(os.environ.get("BATCH", 5))
MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

def llm(prompt):
    resp = openai.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()

def generate_article(keyword: str):
    slug = slugify(keyword)[:90]
    path = CONTENT_DIR / f"{slug}.md"
    today = datetime.date.today().isoformat()
    if path.exists():
        post = frontmatter.load(path)
    else:
        post = frontmatter.loads("")
        post["title"] = keyword.title()
        post["date"] = today
    post["last_updated"] = today
    outline = llm(
        f"""Rédige un article de blog de 500 mots en français sur le sujet suivant, structuré en h2/h3, avec une intro claire et une conclusion pratique.
        Sujet : {keyword}
        """
    )
    post.content = outline
    frontmatter.dump(post, path, sort_keys=False)
    print(f"✅ {slug} mis à jour")


def main():
    CONTENT_DIR.mkdir(exist_ok=True)
    with KEYWORDS.open() as f:
        reader = csv.reader(f)
        rows = [r[0].strip() for r in reader if r]
    unoriented = [kw for kw in rows if not (CONTENT_DIR / f"{slugify(kw)}.md").exists()]
    targets = unoriented[:BATCH]
    for kw in targets:
        generate_article(kw)

if __name__ == "__main__":
    main()
