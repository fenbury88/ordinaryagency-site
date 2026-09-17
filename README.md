# Ordinary Agency — website

A minimal, editorial static site for ordinaryagency.com.au. No build step, no framework — just HTML, CSS and a little vanilla JS.

## Files
- `index.html` — home (long-scroll overview)
- `services.html` — services overview
- `website-development.html` — service detail page
- `lead-generation.html` — service detail page
- `automation-ai.html` — service detail page
- `work.html` — portfolio grid
- `about.html` — story, values, process
- `contact.html` — contact details + form
- `discovery.html` — the **Website brief**: long website-project questionnaire (six steps). Labelled "Website brief" everywhere; the filename stays so links already sent out keep working
- `404.html` — custom not-found page (GitHub Pages serves it automatically)
- `style.css` — all styles (palette + type tokens are CSS variables at the top)
- `main.js` — scroll reveals, sticky-header state, mobile menu, contact form
- `favicon.svg` — brand mark
- `robots.txt` / `sitemap.xml` — SEO
- `journal/` — the Journal. **Generated, don't hand-edit**; see [Journal](#journal)
- `_journal/` — Journal sources: `posts/*.md` and `build.py`. The leading underscore keeps GitHub Pages from publishing it
- `CNAME` — custom domain for GitHub Pages. Don't delete it; the domain breaks.

Header/footer markup is duplicated across pages (kept as static HTML for SEO — no JS-injected partials). If you change a nav link, update it in **all ten pages**, then run `python3 _journal/build.py`. Journal pages copy their header and footer from `about.html` at build time.

## Run locally
```
cd ordinaryagency-site
python3 -m http.server 4388
# open http://localhost:4388
```

## Deploy
Hosted on **GitHub Pages** from the `main` branch of `fenbury88/ordinaryagency-site`, with Cloudflare in front for DNS. Push to `main` and it's live in roughly a minute — there's no build step and nothing to run.

## Contact form
All forms (home page, `contact.html`, the Website brief) POST to the Send It Bro Cloudflare Worker's `/oa-form` route (`https://senditbro-proxy.mike-e40.workers.dev/oa-form`; code in `~/senditbro/worker.js`). It emails the submission to mike@ordinaryagency.com.au via Resend, with reply-to set to the enquirer. They used to go to Formspree, whose reCAPTCHA silently lost submissions.

`main.js` submits in the background so the visitor never leaves the page. If the fetch itself fails, it falls back to a normal browser POST; the worker 303s back to the form's `_next` URL with `?sent=1`, which shows the thank-you note. Without JS the form posts natively from the start.

## Website brief form
`/discovery.html` is the website-project questionnaire — six sections, about thirty questions. It posts to the same worker route as the contact form, told apart by its `_subject` ("Website brief from ordinaryagency.com.au").

How it behaves:
- **No JS**: one long scrolling form with native validation. It submits and works.
- **With JS** (`main.js`, bottom): steps, a progress bar, per-step validation, and a thank-you panel swapped in on success. The stepper sets `form.noValidate` because native validation cannot focus a required field inside a hidden step, which would block submission silently.
- **Draft saving**: answers go to `localStorage` under `oa_discovery_v1` as you type, and are restored on return. Cleared on successful submit. Never leaves the browser until submission.
- **"At least one" rule**: checkbox groups can't express this natively, so `data-require-one="<field name>"` on a group handles it; a filled `"<field name> — other"` text box counts as an answer.

Field `name` attributes are human-readable ("Primary goal", "Budget range") because they become the labels in the notification email.

## Journal
Short weekly posts at `/journal/`, there so the site visibly shows someone is home. Posts are Markdown in `_journal/posts/`; `_journal/build.py` (Python standard library, nothing to install) turns them into plain HTML that gets committed, so GitHub Pages still has nothing to build.

```
python3 _journal/build.py --check   # validate only
python3 _journal/build.py           # validate, then write
```

It writes `journal/<slug>.html`, `journal/index.html`, `journal/feed.xml` (RSS), the "From the Journal" block on the home page (between the `journal:latest` markers) and the Journal URLs in `sitemap.xml` (between the `journal` markers). Rebuilding with nothing changed produces no diff.

**A post** is `_journal/posts/YYYY-MM-DD-slug.md`:
```
---
title: What a tradie's website needs to do on a phone
description: 50–160 characters. Used for the listing, search results and social cards.
date: 2026-09-17
tag: Websites
---
Body in Markdown: paragraphs, ## and ### headings, - and 1. lists, > quotes, **bold**, *italic*, [links](/contact.html).
```
`tag` is one of `Websites`, `Lead gen`, `Automation`; it sets the accent colour and the call to action at the foot of the post. `author` defaults to Mike Fenbury.

- **Queueing:** a post dated in the future is skipped until that day (Perth time), then appears on the next build.
- **Unpublishing:** delete the `.md`, rebuild, push. The build removes the page.
- **Dates are real.** Never backdate a post; the whole point is honest recency.

**The checks** are the only gate between the unattended agent and the live site, so any failure stops the build before it writes anything:
- the tag is valid, the slug is lowercase-with-hyphens and unique, the title is 70 characters or fewer, the description is 50–160 characters, and the body is 200–500 words
- only the Markdown listed above: no single-# headings, raw HTML, images, tables or code blocks
- no percentages (statistics can't be verified), and no dollar amounts except Send It Bro's published $797 / $250
- no client from `work.html` named without Mike's okay
- none of a list of AI-sounding stock phrases ("delve", "seamless", "game-changer"…)
- internal links must point at pages that exist, and external links must be https

## Homepage blueprint
`website-development.html#homepage-blueprint` is a wireframe of a trade homepage, block by block, with a leader line from each block to the job it does. It's adapted from the Send It Bro homepage but recoloured into Ordinary's ink and green, since lime is reserved for Send It Bro. Each callout is a `<details>` that's open in the markup, so it reads fine without JS. On phones `main.js` closes all but the first, because nine open rows in a narrow column get long.

## Brand
- **Type:** Fraunces (wordmark) + Space Grotesk (display) + Inter (body)
- **Palette:** paper `#FAFAF7`, ink `#15150F`, green accent `#2C7A57` — all in `:root` in `style.css`

## Cache busting
`style.css` and `main.js` are linked with a `?v=YYYYMMDD` stamp in all ten pages (Journal pages pick the stamp up from `about.html` on the next build). **Bump it whenever either file changes** — they're served with a 4-hour cache, so without a bump returning visitors keep the old copy:
```
perl -pi -e 's/\?v=[0-9a-z]+/?v=20260807/g' *.html
python3 _journal/build.py
```

## Social share card
`og-image.png` (1200×630) is generated from `og-image-source.html`, which mirrors the hero. Regenerate after a brand change:
```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
  --virtual-time-budget=6000 --screenshot=og-image.png \
  --window-size=1200,630 og-image-source.html
```

## Send It Bro
`index.html` carries a dedicated Send It Bro section (`#send-it-bro`) that pitches the product and links to senditbro.com.au. It is **not** a portfolio piece — deliberately kept out of both work grids, and it uses Send It Bro's own lime `#BDFF30` on ink so it reads as a separate brand.

## To do

### Make the site look active — the big one
**Why:** the site currently reads as a shell. Nothing on it is dated, nothing changes between visits, and a prospect comparing agencies can't tell whether anyone is home.

**Decided (2026-09-17):** the blog is called **Journal**; posts are short and go out **weekly**; the agent **publishes unattended** (commits straight to `main`); the header "Discovery" pill becomes **Website brief**.

1. ✅ **Rename Discovery → Website brief.** *(done 2026-09-17)* Header pill and mobile nav on all pages, page title/H1. Keep the `discovery.html` URL — Pages can't redirect, and it's already been sent to people. Fix this README's Formspree references while there (forms now go via the worker).
2. ✅ **Journal foundation.** *(done 2026-09-17; see [Journal](#journal). Sources ended up as Markdown files in `_journal/posts/` rather than a `posts.json`)*
   - `journal/index.html` (newest first) and a post template: 250–450 words, visible date, reading time, tag (Websites / Lead gen / Automation), author, CTA to Website brief or contact. `Article` schema.
   - `journal/posts.json` is the single source. A small script regenerates the index, a **"Latest from the Journal"** block on the home page (3 newest), `sitemap.xml` and `feed.xml`. Output is committed, so Pages still has no build step.
   - "Journal" in nav + footer on every page.
   - Launch with three real posts, dated the day they go live. No backdating.
3. **The Journal agent.** *(next)* Weekly scheduled Claude Code routine with repo access (cloud, so it doesn't depend on the Mac mini being awake).
   - Pulls the next topic from `journal/topics.md` (seed: questions Mike gets asked, trades in `work.html`, Perth local search, AI/automation for small business).
   - Drafts in Mike's voice, Australian English, humanizer pass; runs the generator; commits and pushes; notifies Mike with the live link.
   - Because nothing is reviewed before publish, the guardrails are hard rules, and a failed check stops the push: no invented client results or statistics, no naming clients, no pricing claims beyond Send It Bro's published prices, word limit, no repeated topic, links and schema validate. Unpublishing = delete the entry from `posts.json`, rerun the generator, push.
4. **Other activity signals.** Month-went-live on work tiles (dates from Mike); an availability line ("Taking on 2 new projects for October") the agent refreshes monthly; newer Google reviews (featured ones are 2023); optionally a LinkedIn draft per post.

### Smaller
- Add the exact **Claremont street address + postcode** — currently set to "Claremont, Western Australia" in the contact section/page and all footers. Also unblocks a full `PostalAddress` in the home page schema, which currently stops at suburb level.
- Confirm the social proof / testimonial is current.
- **Security headers** (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) aren't being served. GitHub Pages can't set custom headers, so add them as a Cloudflare Transform Rule if wanted. They were previously declared in a `netlify.toml` left over from an earlier host, which never applied on Pages.
