// ┌─────────────────────────────────────────────────────────────────────────┐
// │           FICHIER: assets/js/main.js                                    │
// └─────────────────────────────────────────────────────────────────────────┘

document.addEventListener("DOMContentLoaded", function() {
  // 1. Smooth scrolling pour la TOC
  document.querySelectorAll(".table-of-contents a").forEach(function(anchor) {
    anchor.addEventListener("click", function(e) {
      e.preventDefault();
      const targetId = this.getAttribute("href").substring(1);
      const targetEl = document.getElementById(targetId);
      if (targetEl) {
        window.scrollTo({
          top: targetEl.offsetTop - 20, // offset pour ne pas cacher par le header
          behavior: "smooth"
        });
      }
    });
  });

  // 2. (Optionnel) Toggle pour le menu mobile
  const navToggle = document.querySelector(".nav-toggle");
  const navMenu = document.querySelector(".site-nav ul");
  if (navToggle && navMenu) {
    navToggle.addEventListener("click", function() {
      navMenu.classList.toggle("visible");
    });
  }
});
