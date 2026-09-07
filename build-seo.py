#!/usr/bin/env python3
"""Generate /fr/ and /en/ localized pages with SEO head tags."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE_URL = "https://labs-kamaloka-ai.us"

i18n_json = subprocess.check_output(
    [
        "node",
        "-e",
        "const fs=require('fs');"
        "global.window=global;"
        "eval(fs.readFileSync('i18n.js','utf8'));"
        "process.stdout.write(JSON.stringify(global.KAMALOKA_I18N));",
    ],
    cwd=ROOT,
)
I18N = json.loads(i18n_json.decode("utf-8"))

template = (ROOT / "index.source.html").read_text(encoding="utf-8")


def get_nested(obj, path: str):
    cur = obj
    for key in path.split("."):
        cur = cur[key]
    return cur


def apply_i18n(html: str, lang: str) -> str:
    t = I18N[lang]

    def repl_text(m):
        key = m.group(1)
        val = get_nested(t, key)
        return m.group(0).replace(m.group(2), val)

    def repl_html(m):
        key = m.group(1)
        val = get_nested(t, key)
        return re.sub(r">[^<]*<", f">{val}<", m.group(0), count=1)

    for el in re.finditer(r'data-i18n="([^"]+)"[^>]*>([^<]*)</', html):
        key = el.group(1)
        val = get_nested(t, key)
        html = html.replace(el.group(0), el.group(0).replace(el.group(2), val))

    for el in re.finditer(r'data-i18n-html="([^"]+)"[^>]*>(.*?)</', html, re.DOTALL):
        key = el.group(1)
        val = get_nested(t, key)
        html = html.replace(el.group(0), re.sub(r">.*?</", f">{val}</", el.group(0), count=1, flags=re.DOTALL))

    for el in re.finditer(r'data-i18n-attr="([^"]+)"', html):
        pairs = el.group(1).split(";")
        attrs = el.group(0)
        for pair in pairs:
            attr, key = [p.strip() for p in pair.split(":")]
            val = get_nested(t, key)
            attrs = re.sub(rf'{attr}="[^"]*"', f'{attr}="{val}"', attrs)
        html = html.replace(el.group(0), attrs)

    return html


def seo_head(lang: str, alt_lang: str, page_path: str) -> str:
    t = I18N[lang]["meta"]
    canonical = f"{SITE_URL}{page_path}"
    alt_path = I18N[alt_lang] and f"/{alt_lang}/"
    alt_url = f"{SITE_URL}/{alt_lang}/"
    og_locale = "fr_FR" if lang == "fr" else "en_US"
    og_alt = "en_US" if lang == "fr" else "fr_FR"

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": f"{SITE_URL}/#organization",
                "name": "Kamaloka AI Technologies LLC",
                "alternateName": "Kamaloka AI Technologies",
                "url": SITE_URL,
                "logo": f"{SITE_URL}/assets/logo-full.webp",
                "email": "hello@labs-kamaloka-ai.us",
                "telephone": "+2250720322691",
                "sameAs": [
                    "https://www.facebook.com/kamaitechofficial/",
                    "https://www.linkedin.com/company/kam-aitech/",
                ],
                "address": [
                    {
                        "@type": "PostalAddress",
                        "addressLocality": "Abidjan",
                        "addressCountry": "CI",
                    },
                    {
                        "@type": "PostalAddress",
                        "addressLocality": "Albuquerque",
                        "addressRegion": "NM",
                        "addressCountry": "US",
                    },
                ],
                "description": t["description"],
                "knowsAbout": [
                    "Artificial Intelligence",
                    "Cybersecurity",
                    "Software",
                    "Automation",
                    "Technology companies",
                ],
            },
            {
                "@type": "WebSite",
                "@id": f"{SITE_URL}/#website",
                "url": SITE_URL,
                "name": "Kamaloka AI Technologies",
                "publisher": {"@id": f"{SITE_URL}/#organization"},
                "inLanguage": [lang],
            },
            {
                "@type": "WebPage",
                "@id": f"{canonical}#webpage",
                "url": canonical,
                "name": t["title"],
                "description": t["description"],
                "isPartOf": {"@id": f"{SITE_URL}/#website"},
                "about": {"@id": f"{SITE_URL}/#organization"},
                "inLanguage": lang,
            },
        ],
    }

    switch_href = f"/{alt_lang}/"
    switch_flag = "https://flagcdn.com/w40/gb.png" if alt_lang == "en" else "https://flagcdn.com/w40/fr.png"
    switch_code = alt_lang.upper()
    switch_label = get_nested(I18N[lang], "nav.switchEn" if alt_lang == "en" else "nav.switchFr")

    return f"""  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{t['title']}</title>
  <meta name="description" content="{t['description']}" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <link rel="canonical" href="{canonical}" />
  <link rel="alternate" hreflang="fr" href="{SITE_URL}/fr/" />
  <link rel="alternate" hreflang="en" href="{SITE_URL}/en/" />
  <link rel="alternate" hreflang="x-default" href="{SITE_URL}/en/" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="Kamaloka AI Technologies" />
  <meta property="og:title" content="{t['title']}" />
  <meta property="og:description" content="{t['description']}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:locale" content="{og_locale}" />
  <meta property="og:locale:alternate" content="{og_alt}" />
  <meta property="og:image" content="{SITE_URL}/assets/logo-full.webp" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{t['title']}" />
  <meta name="twitter:description" content="{t['description']}" />
  <meta name="twitter:image" content="{SITE_URL}/assets/logo-full.webp" />
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
  <!-- SEO_LANG_SWITCH:{switch_href}:{switch_flag}:{switch_code}:{switch_label} -->"""


def build_lang_page(lang: str):
    alt = "en" if lang == "fr" else "fr"
    html = template

    # Strip old head content between <head> and </head> - we'll replace
    html = re.sub(r"<head>.*?</head>", "<head>\nPLACEHOLDER_HEAD\n</head>", html, flags=re.DOTALL)

    # Asset paths
    html = html.replace('href="styles.css"', 'href="../styles.css"')
    html = html.replace('src="assets/', 'src="../assets/')
    html = html.replace('src="i18n.js"', 'src="../i18n.js"')
    html = html.replace('src="main.js"', 'src="../main.js"')
    html = html.replace('src="seo-config.js"', 'src="../seo-config.js"')
    html = html.replace('url("fonts/', 'url("../fonts/')

    html = html.replace("<html lang=\"fr\">", f'<html lang="{lang}">')
    html = html.replace('data-page-lang=""', f'data-page-lang="{lang}"')

    html = html.replace(
        '<button type="button" class="lang-switch" id="lang-switch" aria-label="Passer en anglais">',
        f'<a class="lang-switch" id="lang-switch" href="/{alt}/" aria-label="{get_nested(I18N[lang], "nav.switchEn" if alt == "en" else "nav.switchFr")}">',
    )
    html = html.replace(
        '<button type="button" class="lang-switch" id="lang-switch" aria-label="Switch to English">',
        f'<a class="lang-switch" id="lang-switch" href="/{alt}/" aria-label="{get_nested(I18N[lang], "nav.switchEn" if alt == "en" else "nav.switchFr")}">',
    )
    # fallback generic replace
    html = html.replace(
        '<button type="button" class="lang-switch" id="lang-switch"',
        f'<a class="lang-switch" id="lang-switch" href="/{alt}/"',
    )
    html = html.replace(
        '<button type="button" class="mobile-lang-switch" id="mobile-lang-switch">',
        f'<a class="mobile-lang-switch" id="mobile-lang-switch" href="/{alt}/">',
    )
    html = html.replace("</button>\n          <a href=\"https://wa.me", "</a>\n          <a href=\"https://wa.me")
    html = html.replace(
        '<span id="mobile-lang-code">EN</span>\n    </button>',
        f'<span id="mobile-lang-code">{alt.upper()}</span>\n    </a>',
    )

    html = apply_i18n(html, lang)
    head = seo_head(lang, alt, f"/{lang}/")
    html = html.replace("PLACEHOLDER_HEAD", head + """
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet" />
  <link href="https://db.onlinewebfonts.com/c/8cb707a9b8a73f8a7403336b861c3074?family=BubbledotICG-FinePos" rel="stylesheet" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css" integrity="sha512-SnH5WK+bZxgPHs44uWIX+LLJAJ9/2PkPKZ5QiAj6Ta86w+fsb2TkcmfRyVX3pBnMFcV7oQPJkl9QevSCWr3W6A==" crossorigin="anonymous" referrerpolicy="no-referrer" />
  <link rel="stylesheet" href="../styles.css" />""")
    html = html.replace('  <script src="../i18n.js"></script>\n', "")
    html = html.replace('  <script src="i18n.js"></script>\n', "")

    html = html.replace(
        f'id="lang-switch" href="/{alt}/"',
        f'id="lang-switch" href="/{alt}/" aria-label="{get_nested(I18N[lang], "nav.switchEn" if alt == "en" else "nav.switchFr")}"',
    )
    html = re.sub(r'\saria-label="[^"]*"\saria-label="[^"]*"', lambda m: m.group(0).split('aria-label="')[0] + 'aria-label="' + get_nested(I18N[lang], "nav.switchEn" if alt == "en" else "nav.switchFr") + '"', html, count=1)

    out_dir = ROOT / lang
    out_dir.mkdir(exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"Built {lang}/index.html")


def build_root_hub():
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Kamaloka AI Technologies LLC",
        "url": SITE_URL,
        "logo": f"{SITE_URL}/assets/logo-full.webp",
        "sameAs": [
            "https://www.facebook.com/kamaitechofficial/",
            "https://www.linkedin.com/company/kam-aitech/",
        ],
    }
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Kamaloka AI Technologies — Choose your language</title>
  <meta name="description" content="Kamaloka AI Technologies — Technology lab and venture studio. Born in Africa. Built for the world." />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="{SITE_URL}/" />
  <link rel="alternate" hreflang="fr" href="{SITE_URL}/fr/" />
  <link rel="alternate" hreflang="en" href="{SITE_URL}/en/" />
  <link rel="alternate" hreflang="x-default" href="{SITE_URL}/en/" />
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
  <link rel="stylesheet" href="styles.css" />
  <style>
    .lang-hub {{
      min-height: 100dvh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 24px;
      padding: 24px;
      text-align: center;
      background: #000;
      color: #fff;
    }}
    .lang-hub img {{ width: min(200px, 60vw); height: auto; }}
    .lang-hub h1 {{
      font-family: "BubbledotICG-FinePos", monospace;
      font-size: clamp(22px, 5vw, 36px);
      letter-spacing: -0.03em;
    }}
    .lang-hub p {{ color: #bdbdbd; max-width: 520px; line-height: 1.6; }}
    .lang-hub__actions {{ display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; }}
    .lang-hub__actions a {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 12px 22px;
      border-radius: 999px;
      background: #fff;
      color: #000;
      font-weight: 600;
    }}
    .lang-hub__actions a.secondary {{
      background: transparent;
      color: #fff;
      border: 1px solid rgba(255,255,255,.35);
    }}
  </style>
</head>
<body>
  <main class="lang-hub">
    <img src="assets/logo-full.webp" alt="Kamaloka AI Technologies" width="220" height="44" />
    <h1>KAMALOKA AI TECHNOLOGIES</h1>
    <p>Technology lab and venture studio — artificial intelligence, cybersecurity, software and automation. Based in Abidjan, Côte d'Ivoire.</p>
    <div class="lang-hub__actions">
      <a href="/fr/">🇫🇷 Français</a>
      <a href="/en/" class="secondary">🇬🇧 English</a>
    </div>
  </main>
</body>
</html>"""
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    print("Built root index.html (language hub)")


def build_sitemap():
    urls = [
        ("", "monthly", "1.0"),
        ("/fr/", "weekly", "1.0"),
        ("/en/", "weekly", "1.0"),
    ]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">')
    for path, freq, priority in urls:
        loc = f"{SITE_URL}{path}"
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append(f"    <changefreq>{freq}</changefreq>")
        lines.append(f"    <priority>{priority}</priority>")
        if path in ("/fr/", "/en/", ""):
            lines.append(f'    <xhtml:link rel="alternate" hreflang="fr" href="{SITE_URL}/fr/" />')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="en" href="{SITE_URL}/en/" />')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE_URL}/en/" />')
        lines.append("  </url>")
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")
    print("Built sitemap.xml")


def build_robots():
    content = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""
    (ROOT / "robots.txt").write_text(content, encoding="utf-8")
    print("Built robots.txt")


if __name__ == "__main__":
    # Save template from current index if needed
    src = ROOT / "index.html"
    if not (ROOT / "index.source.html").exists():
        # Only save source once from original - user may have overwritten
        pass
    build_lang_page("fr")
    build_lang_page("en")
    build_root_hub()
    build_sitemap()
    build_robots()
