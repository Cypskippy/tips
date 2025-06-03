// ┌─────────────────────────────────────────────────────────────────────────┐
// │           FICHIER: /_layouts/ads-inject.js                              │
// └─────────────────────────────────────────────────────────────────────────┘
document.addEventListener("DOMContentLoaded", function() {
  const article = document.querySelector("article");
  if (!article) return;

  const paragraphs = article.querySelectorAll("p");
  if (paragraphs.length < 3) return;  // on a moins de 3 paragraphes : rien à faire

  // Créer le conteneur publicitaire
  const adWrapper = document.createElement("div");
  adWrapper.className = "injected-ad";
  adWrapper.style.textAlign = "center";
  adWrapper.style.margin = "20px 0";

  // Remplace CA-PUB et AD-SLOT par tes valeurs
  adWrapper.innerHTML = `
    <ins class="adsbygoogle"
         style="display:block"
         data-ad-client="ca-pub-9402824549128224"
         data-ad-slot="5651044206"
         data-ad-format="auto"
         data-full-width-responsive="true"></ins>
    <script>
      (adsbygoogle = window.adsbygoogle || []).push({});
    </script>
  `;

  // On insère le bloc juste après le 3ᵉ paragraphe
  paragraphs[2].parentNode.insertBefore(adWrapper, paragraphs[2].nextSibling);
});
