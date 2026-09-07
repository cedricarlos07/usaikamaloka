(function () {
  "use strict";

  const burger = document.querySelector(".burger");
  const overlay = document.querySelector(".menu-overlay");
  const mobileMenu = document.getElementById("mobile-menu");
  const mobileLinks = mobileMenu ? mobileMenu.querySelectorAll("a") : [];
  const navLinks = document.querySelectorAll(".nav-link, .mobile-link");
  const sections = document.querySelectorAll("section[id], footer[id]");
  const MOBILE_BREAKPOINT = 900;

  const pageLang = document.documentElement.lang === "en" ? "en" : "fr";

  function isMobile() {
    return window.innerWidth <= MOBILE_BREAKPOINT;
  }

  function openMenu() {
    if (!burger || !overlay || !mobileMenu) return;
    burger.setAttribute("aria-expanded", "true");
    overlay.hidden = false;
    overlay.setAttribute("aria-hidden", "false");
    mobileMenu.hidden = false;
    mobileMenu.classList.remove("is-open");
    void mobileMenu.offsetWidth;
    mobileMenu.classList.add("is-open");
    document.body.classList.add("menu-open");
  }

  function closeMenu() {
    if (!burger || !overlay || !mobileMenu) return;
    burger.setAttribute("aria-expanded", "false");
    overlay.hidden = true;
    overlay.setAttribute("aria-hidden", "true");
    mobileMenu.hidden = true;
    mobileMenu.classList.remove("is-open");
    document.body.classList.remove("menu-open");
  }

  function toggleMenu() {
    const expanded = burger.getAttribute("aria-expanded") === "true";
    if (expanded) closeMenu();
    else openMenu();
  }

  if (burger) burger.addEventListener("click", toggleMenu);
  if (overlay) overlay.addEventListener("click", closeMenu);

  mobileLinks.forEach(function (link) {
    link.addEventListener("click", closeMenu);
  });

  document.querySelectorAll(".mobile-lang-switch").forEach(function (link) {
    link.addEventListener("click", closeMenu);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeMenu();
  });

  window.addEventListener("resize", function () {
    if (!isMobile()) closeMenu();
  });

  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener("click", function (e) {
      const id = anchor.getAttribute("href");
      if (!id || id === "#") return;
      const target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      closeMenu();
    });
  });

  function setActiveNav() {
    let current = "hero";
    const scrollY = window.scrollY + 120;

    sections.forEach(function (section) {
      if (section.offsetTop <= scrollY) {
        current = section.id;
      }
    });

    navLinks.forEach(function (link) {
      const href = link.getAttribute("href");
      if (!href) return;
      const isActive =
        href === "#" + current ||
        (["vision", "valeur", "methode", "equipes", "abidjan", "mission", "closing", "afrique", "studio"].indexOf(current) !== -1 && href === "#vision") ||
        (["technologies", "studio"].indexOf(current) !== -1 && href === "#technologies") ||
        (current === "contact" && href === "#contact");

      link.classList.toggle("active", isActive);
      if (isActive) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  }

  window.addEventListener("scroll", setActiveNav, { passive: true });
  setActiveNav();

  const revealEls = document.querySelectorAll(".reveal-on-scroll");
  if (revealEls.length && "IntersectionObserver" in window) {
    const revealObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );

    revealEls.forEach(function (el) {
      revealObserver.observe(el);
    });
  } else {
    revealEls.forEach(function (el) {
      el.classList.add("is-visible");
    });
  }

  document.documentElement.setAttribute("data-ready-lang", pageLang);
})();
