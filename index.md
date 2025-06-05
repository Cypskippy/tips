---
layout: page
title: Accueil
---

# Bienvenue sur Cyprien – Programmatic SEO  

(Repris 100 % à l’arrache : voici toutes les pages générées automatiquement !)
<input type="text" id="search-input" placeholder="Rechercher une page…">
<ul id="results-container"></ul>

<script>
  const data = [
    {%- for doc in site.collections['pages'].docs -%}
    {
      "title": {{ doc.data.title | jsonify }},
      "url": {{ doc.url | jsonify }},
      "excerpt": {{ doc.content | strip_html | strip_newlines | truncate: 100 | jsonify }}
    }{%- unless forloop.last -%},{% endunless -%}
    {%- endfor -%}
  ];

  document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("search-input");
    const results = document.getElementById("results-container");

    input.addEventListener("input", () => {
      const q = input.value.toLowerCase();
      results.innerHTML = "";

      if (q.length < 2) return;
      data
        .filter(item =>
          item.title.toLowerCase().includes(q) ||
          item.excerpt.toLowerCase().includes(q)
        )
        .forEach(item => {
          const li = document.createElement("li");
          li.innerHTML = `<a href="${item.url}">${item.title}</a>`;
          results.appendChild(li);
        });
    });
  });
</script>
<style>
  #results-container { list-style: none; padding: 0; margin-top: 10px; }
  #results-container li { margin-bottom: 8px; }
</style>

<ul>
  {%- comment -%}
    On récupère la collection “pages” (les .md créés par generate.py dans _pages/).
    Chaque document y a son front-matter avec “title” et “date”.
  {%- endcomment -%}
  {% assign all_pages = site.collections['tips'].docs | sort: 'date' | reverse %}
  {%- for doc in all_pages -%}

{% assign tips_coll = site.collections['tips'] %}
{% if tips_coll %}
  {% assign all_pages = tips_coll.docs | sort: 'date' | reverse %}
  … boucle d’affichage …
{% else %}
  _Aucun article pour l’instant._
{% endif %}


  


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
