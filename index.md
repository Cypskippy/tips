---
layout: page
title: Accueil
---

# Bienvenue sur Cyprien – Programmatic SEO  

(Repris 100 % à l’arrache : voici toutes les pages générées automatiquement !)

<ul>
  {%- comment -%}
    On récupère la collection “pages” (les .md créés par generate.py dans _pages/).
    Chaque document y a son front-matter avec “title” et “date”.
  {%- endcomment -%}

  {%- assign all_pages = site.collections['pages'].docs | sort: 'date' | reverse -%}
  {%- for doc in all_pages -%}
    <li>
      <a href="{{ doc.url | relative_url }}">
        {{ doc.data.date | date: "%Y-%m-%d" }} – {{ doc.data.title }}
      </a>
    </li>
  {%- endfor -%}
</ul>

<p>
  Si vous voulez piocher un peu au hasard, voici le <strong>« Page du jour » »</strong> :
  {%- assign random_doc = all_pages | sample -%}
  <a href="{{ random_doc.url | relative_url }}">
    {{ random_doc.data.title }} ({{ random_doc.data.date | date: "%d %B %Y" }})
  </a>
</p>
