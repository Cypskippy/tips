#!/usr/bin/env python3
"""Génère ou met à jour N articles Markdown à partir de keywords.csv
   + ajoute maillage interne
   + crée une section FAQ générée par IA
   + injecte un bloc Schema.org FAQPage en JSON‑LD
   + (stub) met à jour les barèmes MaPrimeRénov' (à brancher sur API ultérieurement).
"""
import csv, os, datetime, json, random, pathlib, frontmatter, requests, openai
from slugify import slugify

# --- Config -----------------------------------------------------------------
ROOT         = pathlib.Path(__file__).resolve().parents[1]
CONTENT_DIR  = ROOT / "content"
KEYWORDS_CSV = ROOT / "keywords.csv"
MODEL        = os.getenv("LLM_MODEL", "gpt-4o-mini")
BATCH        = int(os.getenv("BATCH", 5))
openai.api_key = os.environ["OPENAI_API_KEY"]

# --- Helpers ----------------------------------------------------------------

def llm(prompt: str) -> str:
    """Wrapper pour interroger le LLM."""
    resp = openai.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


def fetch_barèmes_maprimerenov() -> dict:
    """STUB – Renverra les barèmes MaPrimeRénov' depuis l'API officielle.
    Pour l'instant, retourne les montants 2025 codés en dur.
    """
    # TODO: remplacer par un appel JSON depuis data.gouv.fr ou Service‑public
    return {"pompe_a_chaleur": 5000, "isolation": 25}


def build_related(slug: str) -> str:
    """Crée une section maillage interne avec jusqu’à 3 articles aléatoires."""
    others = [p.stem for p in CONTENT_DIR.glob("*.md") if p.stem != slug]
    if not others:
        return ""
    links = random.sample(others, k=min(3, len(others)))
   bullets = "\\n".join(
    f"- [{l.replace('-', ' ').title()}](/{l}/)" for l in links
)
return f"\\n\\n## Articles connexes\\n{bullets}"

## Articles connexes
{bullets}"


def build_faq(keyword: str) -> tuple[str, str]:
    """Demande au LLM deux QA, renvoie (markdown, json‑ld)."""
    qa_raw = llm(
        f"Donne deux questions fréquentes très courtes (max 12 mots) avec leur réponse concise (1 phrase) au sujet : {keyword}. Format : Q:…
A:… sur deux lignes, répète pour la 2ᵉ question."
    )
    qa_lines = [l.strip() for l in qa_raw.splitlines() if l.strip()]
    pairs = [(qa_lines[i][2:].strip(), qa_lines[i+1][2:].strip()) for i in range(0, len(qa_lines), 2)]

    # Markdown
    md = "\\n\\n## FAQ\\n" + "\\n\\n".join(f"**{q}**\\n: {a}" for q, a in pairs)
" + "

".join(f"**{q}**
: {a}" for q, a in pairs)

    # JSON‑LD Schema.org
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
    return md, json_ld

# --- Core generation --------------------------------------------------------

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

    # Corps principal
    outline = llm(
        f"Rédige un article de blog de 500 mots en français, structuré (h2/h3), intro claire, conclusion pratique. Sujet : {keyword}. Insère 1 tableau de données si pertinent."
    )

    # Sections additionnelles
    faq_md, faq_json = build_faq(keyword)
    related_md           = build_related(slug)

    # Construction finale
    post.content = (
        outline
        + faq_md
        + related_md
        + faq_json
    )

    # Dump
    CONTENT_DIR.mkdir(exist_ok=True)
    frontmatter.dump(post, path, sort_keys=False)
    print(f"✅ {slug} mis à jour")


def main():
    with KEYWORDS_CSV.open() as f:
        rows = [r[0].strip() for r in csv.reader(f) if r]

    pending = [kw for kw in rows if not (CONTENT_DIR / f"{slugify(kw)}.md").exists()]
    for kw in pending[:BATCH]:
        generate_article(kw)

if __name__ == "__main__":
    main()
```python
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
