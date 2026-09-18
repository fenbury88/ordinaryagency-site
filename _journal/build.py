#!/usr/bin/env python3
"""Build the Journal from the Markdown posts in _journal/posts/.

    python3 _journal/build.py            # check every post, then write the site
    python3 _journal/build.py --check    # check only, write nothing
    python3 _journal/build.py --today 2026-10-01   # pretend it's another day

Writes (all committed; GitHub Pages still has nothing to build):
  journal/<slug>.html        one page per post
  journal/index.html         the list, newest first
  journal/feed.xml           RSS
  index.html                 "From the Journal" block between the journal:latest markers
  sitemap.xml                Journal URLs between the journal markers

A post dated after today is skipped, so posts can be queued. Deleting a post's
.md file and rebuilding removes its page. Any check failure exits non-zero
before anything is written. That is the only thing standing between the
unattended agent and the live site, so keep the checks strict.

Standard library only.
"""

import argparse
import datetime as dt
import html
import json
import math
import re
import sys
from email.utils import format_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "_journal" / "posts"
OUT_DIR = ROOT / "journal"
SITE = "https://ordinaryagency.com.au"
GENERATOR = "_journal/build.py"
PERTH = ZoneInfo("Australia/Perth")

TAGS = {  # tag -> (theme class, call to action)
    "Websites":   ("theme-web",   ("Planning a new website?", "Fill in the Website Discovery and we'll come back with a proper proposal.", "/discovery.html", "Start Website Discovery")),
    "Lead gen":   ("theme-leads", ("Want more enquiries?", "Tell us where the leads are drying up and we'll tell you honestly what we'd do.", "/contact.html", "Talk to us")),
    "Automation": ("theme-ai",    ("Drowning in admin?", "Tell us the job that eats your week and we'll tell you if it can be automated.", "/contact.html", "Talk to us")),
}
MIN_WORDS, MAX_WORDS = 200, 500
ALLOWED_DOLLARS = {"$797", "$250"}  # Send It Bro's published prices
BANNED_PHRASES = [
    "in today's fast-paced", "in today’s fast-paced", "delve", "game-changer", "game changer",
    "unlock the power", "unleash", "supercharge", "in the digital age", "look no further",
    "elevate your", "seamless", "cutting-edge", "revolutionise", "revolutionize",
    "it's important to note", "it’s important to note", "in conclusion", "whether you're a",
    "navigate the complexities", "ever-evolving", "testament to",
]


# ---------------------------------------------------------------- posts

class PostError(Exception):
    pass


def parse_post(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        raise PostError("missing front matter (--- block at the top)")
    meta = {}
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise PostError(f"bad front matter line: {line!r}")
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip().strip('"')
    for key in ("title", "description", "date", "tag"):
        if not meta.get(key):
            raise PostError(f"front matter needs '{key}'")
    try:
        date = dt.date.fromisoformat(meta["date"])
    except ValueError:
        raise PostError(f"date must be YYYY-MM-DD, got {meta['date']!r}")
    slug = meta.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
    return {
        "file": path,
        "title": meta["title"],
        "description": meta["description"],
        "date": date,
        "tag": meta["tag"],
        "slug": slug,
        "author": meta.get("author", "Mike Fenbury"),
        "body": m.group(2).strip() + "\n",
    }


def client_names():
    """Client names from the work page. Posts may not name them unattended."""
    text = (ROOT / "work.html").read_text(encoding="utf-8")
    names = re.findall(r'<div class="work-card__meta"><h3>(.*?)</h3>', text)
    return sorted({html.unescape(n) for n in names})


def check_post(post, clients):
    problems = []
    title, desc, body, tag, slug = post["title"], post["description"], post["body"], post["tag"], post["slug"]

    if tag not in TAGS:
        problems.append(f"tag must be one of {', '.join(TAGS)}; got {tag!r}")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        problems.append(f"slug must be lowercase-with-hyphens, got {slug!r}")
    if len(title) > 70:
        problems.append(f"title is {len(title)} chars; keep it to 70")
    if not 50 <= len(desc) <= 160:
        problems.append(f"description is {len(desc)} chars; needs 50-160")

    words = word_count(body)
    if not MIN_WORDS <= words <= MAX_WORDS:
        problems.append(f"body is {words} words; needs {MIN_WORDS}-{MAX_WORDS}")

    for n, line in enumerate(body.splitlines(), 1):
        s = line.strip()
        if re.match(r"^#(?!#)", s):
            problems.append(f"line {n}: no single-# headings; the title is the H1")
        if re.match(r"^#{4,}", s):
            problems.append(f"line {n}: only ## and ### headings")
        if s.startswith("```") or s.startswith("|") or "![" in s:
            problems.append(f"line {n}: code blocks, tables and images aren't supported")
        if re.search(r"<[a-zA-Z/!]", s):
            problems.append(f"line {n}: no raw HTML")

    everything = f"{title}\n{desc}\n{body}"
    lower = everything.lower()
    if re.search(r"\d\s*%|per ?cent", lower):
        problems.append("contains a percentage; no statistics (they can't be verified)")
    for amount in re.findall(r"\$\s?\d[\d,]*(?:\.\d+)?k?", everything):
        if amount.replace(" ", "") not in ALLOWED_DOLLARS:
            problems.append(f"price {amount!r}; only Send It Bro's published $797 / $250 may appear")
    for phrase in BANNED_PHRASES:
        if phrase in lower:
            problems.append(f"banned phrase {phrase!r}")
    for name in clients:
        if name.lower() in lower:
            problems.append(f"names a client ({name}); clients can't be named without Mike's okay")

    for url in re.findall(r"\]\(([^)\s]+)\)", body):
        if url.startswith("http://"):
            problems.append(f"link {url} must be https")
        elif url.startswith("https://") or url.startswith("mailto:") or url.startswith("tel:"):
            pass
        elif url.startswith("/"):
            target = ROOT / url.lstrip("/").split("#")[0]
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                problems.append(f"link {url} points at a page that doesn't exist")
        else:
            problems.append(f"link {url} must be https:// or start with /")
    return problems


def word_count(markdown):
    text = re.sub(r"\]\([^)]*\)", "]", markdown)
    return len(re.findall(r"[A-Za-z0-9’']+", text))


# ---------------------------------------------------------------- markdown

def smart(text):
    """Curly quotes and dashes on already-escaped text."""
    text = re.sub(r"(^|[\s(\[—–-])&quot;", r"\1“", text)
    text = text.replace("&quot;", "”")
    text = re.sub(r"(^|[\s(\[—–-])&#x27;", r"\1‘", text)
    text = text.replace("&#x27;", "’")
    text = text.replace(" -- ", " – ").replace("--", "–")
    return text


def inline(text):
    links = []

    def stash(m):
        links.append((m.group(1), m.group(2)))
        return f"\x00{len(links) - 1}\x00"

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", stash, text)
    text = smart(html.escape(text))
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", r"<em>\1</em>", text)

    def unstash(m):
        label, url = links[int(m.group(1))]
        attrs = ' target="_blank" rel="noopener"' if url.startswith("http") else ""
        return f'<a href="{html.escape(url)}"{attrs}>{inline(label)}</a>'

    return re.sub(r"\x00(\d+)\x00", unstash, text)


def render_markdown(md):
    out = []
    for block in re.split(r"\n\s*\n", md.strip()):
        lines = [l.rstrip() for l in block.splitlines()]
        first = lines[0].lstrip()
        if first.startswith("### "):
            out.append(f"<h3>{inline(' '.join(lines)[4:].strip())}</h3>")
        elif first.startswith("## "):
            out.append(f"<h2>{inline(' '.join(lines)[3:].strip())}</h2>")
        elif all(re.match(r"^\s*[-*] ", l) or (i and l.startswith("  ")) for i, l in enumerate(lines)):
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in join_items(lines, r"^\s*[-*] ")) + "</ul>")
        elif all(re.match(r"^\s*\d+[.)] ", l) or (i and l.startswith("  ")) for i, l in enumerate(lines)):
            out.append("<ol>" + "".join(f"<li>{inline(i)}</li>" for i in join_items(lines, r"^\s*\d+[.)] ")) + "</ol>")
        elif all(l.lstrip().startswith(">") for l in lines):
            quote = " ".join(re.sub(r"^\s*>\s?", "", l) for l in lines)
            out.append(f"<blockquote><p>{inline(quote)}</p></blockquote>")
        else:
            out.append(f"<p>{inline(' '.join(l.strip() for l in lines))}</p>")
    return "\n".join(out)


def join_items(lines, marker):
    items = []
    for line in lines:
        if re.match(marker, line):
            items.append(re.sub(marker, "", line).strip())
        else:
            items[-1] += " " + line.strip()
    return items


# ---------------------------------------------------------------- page chrome

def absolutise(fragment):
    fragment = re.sub(r'(href|src)="(?!https?:|mailto:|tel:|#|/)([^"]*)"', r'\1="/\2"', fragment)
    return fragment.replace('href="/index.html"', 'href="/"')


def chrome():
    """Header, footer and asset stamps, lifted from about.html so the Journal
    never drifts from the rest of the site when the nav changes."""
    src = (ROOT / "about.html").read_text(encoding="utf-8")
    header = re.search(r'  <header class="site-header".*?</header>', src, re.S).group(0)
    footer = re.search(r'  <footer class="site-footer">.*?</footer>', src, re.S).group(0)
    css_v = re.search(r'style\.css\?v=([0-9a-z]+)', src).group(1)
    js_v = re.search(r'main\.js\?v=([0-9a-z]+)', src).group(1)
    header, footer = (absolutise(x.replace(' aria-current="page"', "")) for x in (header, footer))
    header = header.replace('<a href="/journal/">', '<a href="/journal/" aria-current="page">')
    footer = footer.replace('<a href="/journal/">', '<a href="/journal/" aria-current="page">')
    return header, footer, css_v, js_v


def page(*, title, description, canonical, og_type, head_extra, body, chrome_parts):
    header, footer, css_v, js_v = chrome_parts
    t, d = html.escape(title), html.escape(description)
    return f"""<!DOCTYPE html>
<html lang="en-AU">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{t}</title>
  <meta name="description" content="{d}" />
  <meta name="generator" content="{GENERATOR}" />
  <meta name="theme-color" content="#F7F4EF" />
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..600&family=Inter:wght@400;500;600&family=Space+Grotesk:wght@300..700&display=swap" />
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..600&family=Inter:wght@400;500;600&family=Space+Grotesk:wght@300..700&display=swap" media="print" onload="this.media='all'" />
  <noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..600&family=Inter:wght@400;500;600&family=Space+Grotesk:wght@300..700&display=swap" /></noscript>
  <link rel="stylesheet" href="/style.css?v={css_v}" />
  <link rel="alternate" type="application/rss+xml" title="Ordinary Agency Journal" href="{SITE}/journal/feed.xml" />

  <link rel="canonical" href="{canonical}" />

  <!-- Open Graph -->
  <meta property="og:site_name" content="Ordinary Agency" />
  <meta property="og:title" content="{t}" />
  <meta property="og:description" content="{d}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:type" content="{og_type}" />
  <meta property="og:locale" content="en_AU" />
  <meta property="og:image" content="{SITE}/og-image.png" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:image:alt" content="Ordinary Agency — elevating the ordinary. Digital marketing, Perth." />

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{t}" />
  <meta name="twitter:description" content="{d}" />
  <meta name="twitter:image" content="{SITE}/og-image.png" />
{head_extra}</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>

{header}

{body}

{footer}

  <script src="/main.js?v={js_v}" defer></script>
</body>
</html>
"""


def text(s):
    """Escape for HTML and curl the quotes, for visible titles and descriptions."""
    return smart(html.escape(s))


def nice_date(d):
    return f"{d.day} {d.strftime('%B %Y')}"


def short_date(d):
    return f"{d.day} {d.strftime('%b %Y')}"


def minutes(post):
    return max(1, math.ceil(word_count(post["body"]) / 220))


def post_url(post):
    return f"/journal/{post['slug']}.html"


def row(post, level="h2"):
    """One post in a list: the Journal index and 'more from the Journal'."""
    theme = TAGS[post["tag"]][0]
    return f"""          <li class="journal-row reveal {theme}">
            <a class="journal-row__link" href="{post_url(post)}">
              <time class="journal-row__date" datetime="{post['date'].isoformat()}">{short_date(post['date'])}</time>
              <div class="journal-row__main">
                <{level}>{text(post['title'])}</{level}>
                <p>{text(post['description'])}</p>
              </div>
              <span class="journal-row__tag">{html.escape(post['tag'])}</span>
            </a>
          </li>"""


# ---------------------------------------------------------------- outputs

def render_post(post, posts, chrome_parts):
    theme, (cta_h, cta_p, cta_href, cta_btn) = TAGS[post["tag"]]
    canonical = SITE + post_url(post)
    ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post["title"],
        "description": post["description"],
        "datePublished": post["date"].isoformat(),
        "dateModified": post["date"].isoformat(),
        "author": {"@type": "Person", "name": post["author"], "url": f"{SITE}/about.html"},
        "publisher": {"@id": f"{SITE}/#organisation"},
        "image": f"{SITE}/og-image.png",
        "mainEntityOfPage": canonical,
        "articleSection": post["tag"],
        "inLanguage": "en-AU",
    }
    head_extra = (
        f'  <meta property="article:published_time" content="{post["date"].isoformat()}" />\n'
        f'  <meta property="article:section" content="{html.escape(post["tag"])}" />\n\n'
        f'  <script type="application/ld+json">\n{json.dumps(ld, indent=2, ensure_ascii=False)}\n  </script>\n'
    )
    others = [p for p in posts if p is not post][:3]
    more = ""
    if others:
        more = f"""
    <section class="section section--tint">
      <div class="container">
        <div class="section-head reveal">
          <p class="section-label">More from the Journal</p>
        </div>
        <ol class="journal-list">
{chr(10).join(row(p, "h3") for p in others)}
        </ol>
        <p class="section-more reveal"><a href="/journal/" class="link-arrow">All posts <span aria-hidden="true">&rarr;</span></a></p>
      </div>
    </section>"""
    body = f"""  <main id="main">
    <article class="post {theme}">
      <header class="page-head post-head">
        <div class="container">
          <p class="eyebrow reveal"><a href="/journal/">Journal</a><span aria-hidden="true">·</span><span>{html.escape(post['tag'])}</span></p>
          <h1 class="post-head__title reveal">{text(post['title'])}</h1>
          <p class="post-head__meta reveal">
            <time datetime="{post['date'].isoformat()}">{nice_date(post['date'])}</time>
            <span aria-hidden="true">·</span> {minutes(post)} min read
            <span aria-hidden="true">·</span> {html.escape(post['author'])}
          </p>
        </div>
      </header>

      <div class="section">
        <div class="container">
          <div class="post-body reveal">
{render_markdown(post['body'])}
          </div>

          <aside class="post-cta reveal">
            <h2>{cta_h}</h2>
            <p>{text(cta_p)}</p>
            <a href="{cta_href}" class="btn">{cta_btn}</a>
          </aside>
        </div>
      </div>
    </article>
{more}
  </main>"""
    return page(
        title=f"{post['title']} — Ordinary Agency",
        description=post["description"],
        canonical=canonical,
        og_type="article",
        head_extra=head_extra,
        body=body,
        chrome_parts=chrome_parts,
    )


def render_index(posts, chrome_parts):
    if posts:
        listing = f"""        <ol class="journal-list">
{chr(10).join(row(p) for p in posts)}
        </ol>"""
    else:
        listing = '        <p class="journal-empty">The first post lands soon.</p>'
    body = f"""  <main id="main">
    <section class="page-head">
      <div class="container">
        <p class="eyebrow reveal">Journal</p>
        <h1 class="page-head__title reveal">Notes from the <em>studio</em>.</h1>
        <p class="page-head__lead reveal">Short, practical posts on websites, getting found and taking the busywork off your plate. A new one every week.</p>
      </div>
    </section>

    <section class="section">
      <div class="container">
{listing}
      </div>
    </section>

    <section class="cta-band">
      <div class="container">
        <h2 class="reveal">Rather just ask us?</h2>
        <p class="reveal">Tell us about your business and what you need. We usually reply within a day.</p>
        <a href="/contact.html" class="btn reveal">Get in touch</a>
      </div>
    </section>
  </main>"""
    return page(
        title="Journal — Ordinary Agency",
        description="Short, practical posts from a Perth digital agency on websites, getting found on Google and automating small-business admin.",
        canonical=f"{SITE}/journal/",
        og_type="website",
        head_extra="",
        body=body,
        chrome_parts=chrome_parts,
    )


def render_feed(posts):
    items = []
    for p in posts[:20]:
        when = dt.datetime.combine(p["date"], dt.time(9, 0), PERTH)
        items.append(f"""    <item>
      <title>{html.escape(p['title'])}</title>
      <link>{SITE}{post_url(p)}</link>
      <guid isPermaLink="true">{SITE}{post_url(p)}</guid>
      <pubDate>{format_datetime(when)}</pubDate>
      <category>{html.escape(p['tag'])}</category>
      <description>{html.escape(p['description'])}</description>
    </item>""")
    built = format_datetime(dt.datetime.combine(posts[0]["date"], dt.time(9, 0), PERTH)) if posts else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Ordinary Agency Journal</title>
    <link>{SITE}/journal/</link>
    <atom:link href="{SITE}/journal/feed.xml" rel="self" type="application/rss+xml" />
    <description>Short, practical posts from a Perth digital agency.</description>
    <language>en-au</language>
    <lastBuildDate>{built}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
"""


def render_home_block(posts):
    if not posts:
        return ""
    cards = []
    for p in posts[:3]:
        theme = TAGS[p["tag"]][0]
        cards.append(f"""          <li class="journal-card reveal {theme}">
            <a href="journal/{p['slug']}.html">
              <p class="journal-card__meta"><time datetime="{p['date'].isoformat()}">{short_date(p['date'])}</time> · {html.escape(p['tag'])}</p>
              <h3>{text(p['title'])}</h3>
              <p>{text(p['description'])}</p>
              <span class="journal-card__more">Read <span aria-hidden="true">&rarr;</span></span>
            </a>
          </li>""")
    return f"""    <section class="journal-latest" id="journal">
      <div class="container">
        <div class="section-head reveal">
          <p class="section-label">From the Journal</p>
          <h2 class="section-title">Latest notes.</h2>
        </div>
        <ol class="journal-cards">
{chr(10).join(cards)}
        </ol>
        <p class="section-more reveal"><a href="journal/" class="link-arrow">All posts <span aria-hidden="true">&rarr;</span></a></p>
      </div>
    </section>
"""


def splice(text, start, end, content, where):
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        sys.exit(f"build: markers {start} … {end} not found in {where}")
    return pattern.sub(lambda _: f"{start}\n{content}{end}", text, count=1)


def render_sitemap(posts):
    if not posts:
        return ""
    urls = [("/journal/", posts[0]["date"], "0.7")] + [(post_url(p), p["date"], "0.6") for p in posts]
    return "".join(
        f"  <url>\n    <loc>{SITE}{u}</loc>\n    <lastmod>{d.isoformat()}</lastmod>\n    <priority>{pr}</priority>\n  </url>\n"
        for u, d, pr in urls
    )


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="validate posts, write nothing")
    ap.add_argument("--today", help="YYYY-MM-DD; defaults to today in Perth")
    args = ap.parse_args()
    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(PERTH).date()

    clients = client_names()
    posts, failed = [], False
    for path in sorted(POSTS_DIR.glob("*.md")):
        rel = path.relative_to(ROOT)
        try:
            post = parse_post(path)
            problems = check_post(post, clients)
        except PostError as e:
            problems = [str(e)]
        if problems:
            failed = True
            print(f"FAIL {rel}")
            for p in problems:
                print(f"     - {p}")
            continue
        posts.append(post)

    slugs = [p["slug"] for p in posts]
    for s in {s for s in slugs if slugs.count(s) > 1}:
        failed = True
        print(f"FAIL duplicate slug {s!r}")
    if failed:
        sys.exit(1)

    live = sorted((p for p in posts if p["date"] <= today), key=lambda p: (p["date"], p["slug"]), reverse=True)
    queued = [p for p in posts if p["date"] > today]
    print(f"ok   {len(live)} live, {len(queued)} queued" + (f" (next: {min(p['date'] for p in queued)})" if queued else ""))
    if args.check:
        return

    chrome_parts = chrome()
    OUT_DIR.mkdir(exist_ok=True)
    wanted = {f"{p['slug']}.html" for p in live} | {"index.html"}
    for old in OUT_DIR.glob("*.html"):
        if old.name not in wanted and GENERATOR in old.read_text(encoding="utf-8"):
            old.unlink()
            print(f"removed journal/{old.name}")
    for p in live:
        (OUT_DIR / f"{p['slug']}.html").write_text(render_post(p, live, chrome_parts), encoding="utf-8")
    (OUT_DIR / "index.html").write_text(render_index(live, chrome_parts), encoding="utf-8")
    (OUT_DIR / "feed.xml").write_text(render_feed(live), encoding="utf-8")

    home = ROOT / "index.html"
    home.write_text(splice(home.read_text(encoding="utf-8"), "<!-- journal:latest:start -->",
                           "<!-- journal:latest:end -->", render_home_block(live), "index.html"), encoding="utf-8")
    sitemap = ROOT / "sitemap.xml"
    sitemap.write_text(splice(sitemap.read_text(encoding="utf-8"), "<!-- journal:start -->",
                              "<!-- journal:end -->", render_sitemap(live), "sitemap.xml"), encoding="utf-8")
    print("wrote journal/, index.html, sitemap.xml")


if __name__ == "__main__":
    main()
