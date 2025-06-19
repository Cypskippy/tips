---
layout: page
title: Accueil
permalink: /
---

<!-- redirection temporaire : si tu la veux, garde-la en minuscules -->
<!-- <meta http-equiv="refresh" content="0; url=/tips/"> -->

# Bienvenue sur Cyprien – Programmatic SEO

(Repris 100 % à l’arrache : voici toutes les pages générées automatiquement !)

<input type="text" id="search-input" placeholder="Rechercher une page…">
<ul id="results-container"></ul>

<script>
  /* -- Base de données des pages pour la recherche -- */
  const data = [
    {%- for doc in site.tips -%}
    {
      "title": {{ doc.title       | jsonify }},
      "url":   {{ doc.url         | jsonify }},
      "excerpt": {{ doc.content   | strip_html | strip_newlines | truncate: 100 | jsonify }}
    }{%- unless forloop.last -%},{% endunless -%}
    {%- endfor -%}
  ];

  document.addEventListener("DOMContentLoaded", () => {
    const input   = document.getElementById("search-input");
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

<!-- ---------- Liste complète triée ----------- -->
<ul>
{% assign tips_list = site.tips | where: "date" | sort: "date" %}
{% if pages_tips.size > 0 %}
  {% for doc in pages_tips %}
    <li>
      <a href="{{ doc.url | relative_url }}">
        {{ doc.date | date: "%Y-%m-%d" }} – {{ doc.title }}
      </a>
    </li>
  {% endfor %}
{% else %}
  _Aucun article pour l’instant._
{% endif %}
</ul>

<!-- ------------ Page aléatoire du jour ------------ -->
{% if pages_tips.size > 0 %}
  {% assign random_doc = pages_tips | sample %}
  <p>Page du jour : <a href="{{ random_doc.url | relative_url }}">{{ random_doc.title }}</a></p>
{% endif %}
