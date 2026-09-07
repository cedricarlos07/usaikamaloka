#!/usr/bin/env python3
"""Generate /fr/ and /en/ localized pages with SEO head tags and inner SEO pages."""
from __future__ import annotations

import html as html_lib
import json
import re
import subprocess
from pathlib import Path

from pages_data import PAGES

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

NAV = {
    "fr": [
        ("Accueil", "/fr/"),
        ("À propos", "/fr/a-propos/"),
        ("Produits", "/fr/produits/"),
        ("Agents IA", "/fr/agents-ia/"),
        ("Ressources", "/fr/ressources/"),
        ("Contact", "/fr/contact/"),
    ],
    "en": [
        ("Home", "/en/"),
        ("About", "/en/about/"),
        ("Products", "/en/products/"),
        ("AI Agents", "/en/ai-agents/"),
        ("Resources", "/en/resources/"),
        ("Contact", "/en/contact/"),
    ],
}


def esc(text: str) -> str:
    return html_lib.escape(text, quote=True)


def rel_root(web_path: str) -> str:
    depth = len([s for s in web_path.strip("/").split("/") if s])
    return "../" * depth if depth else "./"


def get_nested(obj, path: str):
    cur = obj
    for key in path.split("."):
        cur = cur[key]
    return cur


def apply_i18n(html: str, lang: str) -> str:
    t = I18N[lang]

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


def seo_head_home(lang: str, alt_lang: str, page_path: str) -> str:
    t = I18N[lang]["meta"]
    canonical = f"{SITE_URL}{page_path}"
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
                    {"@type": "PostalAddress", "addressLocality": "Abidjan", "addressCountry": "CI"},
                    {"@type": "PostalAddress", "addressLocality": "Albuquerque", "addressRegion": "NM", "addressCountry": "US"},
                ],
                "description": t["description"],
                "knowsAbout": ["Artificial Intelligence", "Cybersecurity", "Software", "Automation", "Technology companies"],
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
  <title>{esc(t['title'])}</title>
  <meta name="description" content="{esc(t['description'])}" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <link rel="canonical" href="{canonical}" />
  <link rel="alternate" hreflang="fr" href="{SITE_URL}/fr/" />
  <link rel="alternate" hreflang="en" href="{SITE_URL}/en/" />
  <link rel="alternate" hreflang="x-default" href="{SITE_URL}/en/" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="Kamaloka AI Technologies" />
  <meta property="og:title" content="{esc(t['title'])}" />
  <meta property="og:description" content="{esc(t['description'])}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:locale" content="{og_locale}" />
  <meta property="og:locale:alternate" content="{og_alt}" />
  <meta property="og:image" content="{SITE_URL}/assets/logo-full.webp" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(t['title'])}" />
  <meta name="twitter:description" content="{esc(t['description'])}" />
  <meta name="twitter:image" content="{SITE_URL}/assets/logo-full.webp" />
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
  <!-- SEO_LANG_SWITCH:{switch_href}:{switch_flag}:{switch_code}:{switch_label} -->"""


def seo_head_inner(lang: str, page_def: dict, content: dict, alt_content: dict) -> str:
    canonical = f"{SITE_URL}{content['path']}"
    alt_url = f"{SITE_URL}{alt_content['path']}"
    og_locale = "fr_FR" if lang == "fr" else "en_US"
    og_alt = "en_US" if lang == "fr" else "fr_FR"
    page_type = page_def.get("type", "WebPage")

    graph = [
        {"@id": f"{SITE_URL}/#organization", "@type": "Organization"},
        {
            "@type": page_type,
            "@id": f"{canonical}#webpage",
            "url": canonical,
            "name": content["title"],
            "description": content["description"],
            "isPartOf": {"@id": f"{SITE_URL}/#website"},
            "about": {"@id": f"{SITE_URL}/#organization"},
            "inLanguage": lang,
        },
    ]

    if page_type == "SoftwareApplication" and page_def.get("product_name"):
        graph.append(
            {
                "@type": "SoftwareApplication",
                "name": page_def["product_name"],
                "applicationCategory": "BusinessApplication",
                "operatingSystem": "Web",
                "url": canonical,
                "provider": {"@id": f"{SITE_URL}/#organization"},
            }
        )

    if page_type == "Article":
        graph[-1]["@type"] = "Article"
        graph[-1]["headline"] = content["h1"]
        graph[-1]["author"] = {"@id": f"{SITE_URL}/#organization"}
        graph[-1]["publisher"] = {"@id": f"{SITE_URL}/#organization"}

    schema = {"@context": "https://schema.org", "@graph": graph}

    return f"""  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(content['title'])}</title>
  <meta name="description" content="{esc(content['description'])}" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <link rel="canonical" href="{canonical}" />
  <link rel="alternate" hreflang="fr" href="{SITE_URL}{page_def['fr']['path']}" />
  <link rel="alternate" hreflang="en" href="{SITE_URL}{page_def['en']['path']}" />
  <link rel="alternate" hreflang="x-default" href="{SITE_URL}{page_def['en']['path']}" />
  <meta property="og:type" content="{'article' if page_type == 'Article' else 'website'}" />
  <meta property="og:site_name" content="Kamaloka AI Technologies" />
  <meta property="og:title" content="{esc(content['title'])}" />
  <meta property="og:description" content="{esc(content['description'])}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:locale" content="{og_locale}" />
  <meta property="og:locale:alternate" content="{og_alt}" />
  <meta property="og:image" content="{SITE_URL}/assets/logo-full.webp" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(content['title'])}" />
  <meta name="twitter:description" content="{esc(content['description'])}" />
  <meta name="twitter:image" content="{SITE_URL}/assets/logo-full.webp" />
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>"""


def render_blocks(blocks: list, lang: str) -> str:
    parts = []
    for block in blocks:
        t = block["t"]
        if t == "p":
            parts.append(f'<p class="seo-p">{esc(block["c"])}</p>')
        elif t == "h2":
            parts.append(f'<h2 class="seo-h2">{esc(block["c"])}</h2>')
        elif t == "ul":
            items = "".join(f"<li>{esc(i)}</li>" for i in block["items"])
            parts.append(f'<ul class="seo-ul">{items}</ul>')
        elif t == "cta":
            parts.append(
                f'<p class="seo-cta-wrap"><a class="cta" href="{esc(block["href"])}">{esc(block["label"])}</a></p>'
            )
        elif t == "cards":
            cards = ""
            for item in block["items"]:
                cards += f"""<article class="seo-card">
  <h3 class="seo-card__title">{esc(item["name"])}</h3>
  <p class="seo-card__desc">{esc(item["desc"])}</p>
  <a class="seo-card__link" href="{esc(item["href"])}">→</a>
</article>"""
            parts.append(f'<div class="seo-cards">{cards}</div>')
        elif t == "links":
            links = "".join(
                f'<li><a href="{esc(item["href"])}">{esc(item["label"])}</a></li>' for item in block["items"]
            )
            parts.append(f'<ul class="seo-link-list">{links}</ul>')
        elif t == "contact":
            parts.append("""<div class="seo-contact-grid">
  <a href="mailto:hello@labs-kamaloka-ai.us" class="contact-item"><i class="fa-solid fa-envelope" aria-hidden="true"></i><span>hello@labs-kamaloka-ai.us</span></a>
  <a href="https://wa.me/2250720322691" class="contact-item contact-item--whatsapp" target="_blank" rel="noopener noreferrer"><i class="fa-brands fa-whatsapp" aria-hidden="true"></i><span>+225 07 20 32 26 91</span></a>
  <a href="https://www.facebook.com/kamaitechofficial/" class="contact-item" target="_blank" rel="noopener noreferrer"><i class="fa-brands fa-facebook" aria-hidden="true"></i><span>Facebook</span></a>
  <a href="https://www.linkedin.com/company/kam-aitech/" class="contact-item" target="_blank" rel="noopener noreferrer"><i class="fa-brands fa-linkedin" aria-hidden="true"></i><span>LinkedIn</span></a>
</div>""")
    return "\n".join(parts)


def render_seo_page(lang: str, page_def: dict) -> str:
    alt = "en" if lang == "fr" else "fr"
    content = page_def[lang]
    alt_content = page_def[alt]
    prefix = rel_root(content["path"])
    home = f"/{lang}/"
    alt_href = alt_content["path"]

    nav_links = ""
    for label, href in NAV[lang]:
        is_active = href.rstrip("/") == content["path"].rstrip("/")
        cls = "nav-link active" if is_active else "nav-link"
        current = ' aria-current="page"' if is_active else ""
        nav_links += f'<a href="{href}" class="{cls}"{current}>{esc(label)}</a>\n          '

    switch_label = get_nested(I18N[lang], "nav.switchEn" if alt == "en" else "nav.switchFr")
    switch_flag = "https://flagcdn.com/w40/gb.png" if alt == "en" else "https://flagcdn.com/w40/fr.png"

    breadcrumb_home = "Accueil" if lang == "fr" else "Home"
    body = render_blocks(content["blocks"], lang)
    head = seo_head_inner(lang, page_def, content, alt_content)

    footer_scope = "Abidjan, Côte d'Ivoire → Monde" if lang == "fr" else "Abidjan, Côte d'Ivoire → World"
    footer_motto = "Nous construisons ce qui vient après." if lang == "fr" else "We build what comes next."
    footer_tags = "Intelligence artificielle · Logiciels · Cybersécurité" if lang == "fr" else "Artificial intelligence · Software · Cybersecurity"

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
{head}
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet" />
  <link href="https://db.onlinewebfonts.com/c/8cb707a9b8a73f8a7403336b861c3074?family=BubbledotICG-FinePos" rel="stylesheet" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css" integrity="sha512-SnH5WK+bZxgPHs44uWIX+LLJAJ9/2PkPKZ5QiAj6Ta86w+fsb2TkcmfRyVX3pBnMFcV7oQPJkl9QevSCWr3W6A==" crossorigin="anonymous" referrerpolicy="no-referrer" />
  <link rel="stylesheet" href="{prefix}styles.css" />
</head>
<body class="seo-body">
  <div class="bg bg--subtle" aria-hidden="true"></div>
  <div class="page seo-page">
    <header class="header">
      <div class="header-inner">
        <a href="{home}" class="logo-brand" aria-label="Kamaloka AI Technologies">
          <img src="{prefix}assets/logo-nav.webp" alt="" width="44" height="44" class="logo-nav" />
        </a>
        <nav class="nav-pill" aria-label="{'Navigation principale' if lang == 'fr' else 'Main navigation'}">
          {nav_links}
        </nav>
        <div class="header-actions">
          <a class="lang-switch" href="{alt_href}" aria-label="{esc(switch_label)}">
            <img src="{switch_flag}" alt="" width="20" height="15" class="lang-flag" />
            <span class="lang-code">{alt.upper()}</span>
          </a>
          <a href="https://wa.me/2250720322691" class="sign-in sign-in-desktop" target="_blank" rel="noopener noreferrer">
            <i class="fa-brands fa-whatsapp" aria-hidden="true"></i> <span>WhatsApp</span>
          </a>
        </div>
        <button class="burger" type="button" aria-label="{'Menu' if lang == 'fr' else 'Menu'}" aria-expanded="false" aria-controls="mobile-menu">
          <span class="burger-bar"></span>
          <span class="burger-bar"></span>
          <span class="burger-bar"></span>
        </button>
      </div>
    </header>

    <main class="seo-main">
      <nav class="seo-breadcrumb" aria-label="Breadcrumb">
        <a href="{home}">{breadcrumb_home}</a>
        <span aria-hidden="true"> / </span>
        <span>{esc(content['h1'])}</span>
      </nav>
      <header class="seo-hero">
        <p class="section-eyebrow">KAMALOKA AI TECHNOLOGIES</p>
        <h1 class="seo-h1">{esc(content['h1'])}</h1>
        <p class="seo-lead">{esc(content['lead'])}</p>
      </header>
      <article class="seo-content">
        {body}
      </article>
    </main>

    <footer class="site-footer">
      <div class="footer-inner">
        <img src="{prefix}assets/logo-full.webp" alt="Kamaloka AI Technologies" width="220" height="44" class="footer-logo-full" />
        <p class="footer-brand">KAMALOKA AI TECHNOLOGIES LLC</p>
        <p class="footer-tags">{footer_tags}</p>
        <p class="footer-location"><strong>{footer_scope}</strong></p>
        <p class="footer-motto">{footer_motto}</p>
      </div>
    </footer>
  </div>

  <div class="menu-overlay" hidden aria-hidden="true"></div>
  <nav id="mobile-menu" class="mobile-menu" hidden aria-label="{'Menu mobile' if lang == 'fr' else 'Mobile menu'}">
    {''.join(f'<a href="{href}" class="mobile-link">{esc(label)}</a>' for label, href in NAV[lang])}
    <a href="{alt_href}" class="mobile-lang-switch">
      <img src="{switch_flag}" alt="" width="20" height="15" class="lang-flag" />
      <span>{alt.upper()}</span>
    </a>
    <a href="https://wa.me/2250720322691" class="mobile-sign-in" target="_blank" rel="noopener noreferrer">
      <i class="fa-brands fa-whatsapp" aria-hidden="true"></i> <span>WhatsApp</span>
    </a>
  </nav>

  <script src="{prefix}main.js"></script>
</body>
</html>"""


def build_lang_page(lang: str):
    alt = "en" if lang == "fr" else "fr"
    html = template

    html = re.sub(r"<head>.*?</head>", "<head>\nPLACEHOLDER_HEAD\n</head>", html, flags=re.DOTALL)

    html = html.replace('href="styles.css"', 'href="../styles.css"')
    html = html.replace('src="assets/', 'src="../assets/')
    html = html.replace('src="i18n.js"', 'src="../i18n.js"')
    html = html.replace('src="main.js"', 'src="../main.js"')
    html = html.replace('src="seo-config.js"', 'src="../seo-config.js"')
    html = html.replace('url("fonts/', 'url("../fonts/')

    html = html.replace('<html lang="fr">', f'<html lang="{lang}">')
    html = html.replace('data-page-lang=""', f'data-page-lang="{lang}"')

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
    head = seo_head_home(lang, alt, f"/{lang}/")
    html = html.replace(
        "PLACEHOLDER_HEAD",
        head
        + """
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet" />
  <link href="https://db.onlinewebfonts.com/c/8cb707a9b8a73f8a7403336b861c3074?family=BubbledotICG-FinePos" rel="stylesheet" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css" integrity="sha512-SnH5WK+bZxgPHs44uWIX+LLJAJ9/2PkPKZ5QiAj6Ta86w+fsb2TkcmfRyVX3pBnMFcV7oQPJkl9QevSCWr3W6A==" crossorigin="anonymous" referrerpolicy="no-referrer" />
  <link rel="stylesheet" href="../styles.css" />""",
    )
    html = html.replace('  <script src="../i18n.js"></script>\n', "")
    html = html.replace('  <script src="i18n.js"></script>\n', "")

    out_dir = ROOT / lang
    out_dir.mkdir(exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"Built {lang}/index.html")


def build_all_seo_pages():
    for page_def in PAGES:
        for lang in ("fr", "en"):
            content = page_def[lang]
            web_path = content["path"].strip("/")
            out_file = ROOT / web_path / "index.html"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(render_seo_page(lang, page_def), encoding="utf-8")
            print(f"Built {web_path}/index.html")


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
        ("", "monthly", "1.0", None),
        ("/fr/", "weekly", "1.0", ("fr", "en")),
        ("/en/", "weekly", "1.0", ("fr", "en")),
    ]
    for page_def in PAGES:
        fr_path = page_def["fr"]["path"]
        en_path = page_def["en"]["path"]
        priority = page_def.get("priority", "0.7")
        urls.append((fr_path, "monthly", priority, ("fr", "en", fr_path, en_path)))
        urls.append((en_path, "monthly", priority, ("fr", "en", fr_path, en_path)))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">')
    seen = set()
    for path, freq, priority, hreflang in urls:
        if path in seen:
            continue
        seen.add(path)
        loc = f"{SITE_URL}{path}"
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append(f"    <changefreq>{freq}</changefreq>")
        lines.append(f"    <priority>{priority}</priority>")
        if hreflang == ("fr", "en"):
            lines.append(f'    <xhtml:link rel="alternate" hreflang="fr" href="{SITE_URL}/fr/" />')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="en" href="{SITE_URL}/en/" />')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE_URL}/en/" />')
        elif hreflang and len(hreflang) == 4:
            fr_p, en_p = hreflang[2], hreflang[3]
            lines.append(f'    <xhtml:link rel="alternate" hreflang="fr" href="{SITE_URL}{fr_p}" />')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="en" href="{SITE_URL}{en_p}" />')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE_URL}{en_p}" />')
        lines.append("  </url>")
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")
    print(f"Built sitemap.xml ({len(seen)} URLs)")


def build_robots():
    content = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""
    (ROOT / "robots.txt").write_text(content, encoding="utf-8")
    print("Built robots.txt")


if __name__ == "__main__":
    build_lang_page("fr")
    build_lang_page("en")
    build_all_seo_pages()
    build_root_hub()
    build_sitemap()
    build_robots()
