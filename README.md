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
- `discovery.html` — long website-discovery questionnaire (six steps)
- `404.html` — custom not-found page (GitHub Pages serves it automatically)
- `style.css` — all styles (palette + type tokens are CSS variables at the top)
- `main.js` — scroll reveals, sticky-header state, mobile menu, contact form
- `favicon.svg` — brand mark
- `robots.txt` / `sitemap.xml` — SEO
- `CNAME` — custom domain for GitHub Pages. Don't delete it; the domain breaks.

Header/footer markup is duplicated across pages (kept as static HTML for SEO — no JS-injected partials). If you change a nav link, update it in **all ten pages**.

## Run locally
```
cd ordinaryagency-site
python3 -m http.server 4388
# open http://localhost:4388
```

## Deploy
Hosted on **GitHub Pages** from the `main` branch of `fenbury88/ordinaryagency-site`, with Cloudflare in front for DNS. Push to `main` and it's live in roughly a minute — there's no build step and nothing to run.

## Contact form
Both forms (home page and `contact.html`) POST to **Formspree** (`https://formspree.io/f/meebroln`). Submissions land at mike@ordinaryagency.com.au.

`main.js` submits in the background so the visitor never leaves the page. If Formspree refuses that — it rejects background submissions whenever reCAPTCHA is enabled on the form — the code falls back to a normal browser POST. Formspree then serves the challenge itself and sends the visitor back via the `_next` field, landing on `?sent=1`, which shows the thank-you note. Either way the enquiry gets through.

Switching reCAPTCHA off in the Formspree dashboard keeps everything on the fast inline path.

## Discovery form
`/discovery.html` is the website-project questionnaire — six sections, about thirty questions. It posts to the **same Formspree form** as the contact page, told apart by its `_subject` ("Website discovery brief…"). Give it its own Formspree form when volume justifies it: change `action` on `#dsc-form` and the matching `_next`.

How it behaves:
- **No JS**: one long scrolling form with native validation. It submits and works.
- **With JS** (`main.js`, bottom): steps, a progress bar, per-step validation, and a thank-you panel swapped in on success. The stepper sets `form.noValidate` because native validation cannot focus a required field inside a hidden step, which would block submission silently.
- **Draft saving**: answers go to `localStorage` under `oa_discovery_v1` as you type, and are restored on return. Cleared on successful submit. Never leaves the browser until submission.
- **"At least one" rule**: checkbox groups can't express this natively, so `data-require-one="<field name>"` on a group handles it; a filled `"<field name> — other"` text box counts as an answer.

Field `name` attributes are human-readable ("Primary goal", "Budget range") because Formspree uses them as labels in the notification email.

## Brand
- **Type:** Fraunces (wordmark) + Space Grotesk (display) + Inter (body)
- **Palette:** paper `#FAFAF7`, ink `#15150F`, green accent `#2C7A57` — all in `:root` in `style.css`

## Cache busting
`style.css` and `main.js` are linked with a `?v=YYYYMMDD` stamp in all ten pages. **Bump it whenever either file changes** — they're served with a 4-hour cache, so without a bump returning visitors keep the old copy:
```
perl -pi -e 's/\?v=[0-9a-z]+/?v=20260807/g' *.html
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

### Blog + automated post routines — the big one
**Why:** the site currently reads as a shell. Nothing on it is dated, nothing changes between visits, and a prospect comparing agencies can't tell whether anyone is home. Fixing that is the point; a blog is the vehicle.

Not started. Three parts, roughly in order:

1. **A blog section that exists** — `blog/index.html` listing posts, plus a post template. Needs a visible date on every post and a "latest from the blog" block on the home page, since the point is proving recency. Also `Article` schema, and posts in `sitemap.xml`.
2. **A routine that writes them** — a scheduled Claude Code agent: draft a post on a chosen topic, render it into the post template, commit and push. GitHub Pages deploys on push, so no build step is needed and nothing else has to change. Model it on the Send It Bro agents already running on the Mac mini.
3. **A topic backlog** — the routine needs a queue to draw from, not a blank prompt each run. Sensible seed: the questions Mike actually gets asked, and the trades already represented in `work.html`.

Decisions still open: how often posts go out, whether Mike reviews before publish or the routine pushes unattended (Send It Bro settled on review-first for proposals — same call to make here), and whether posts are per-file HTML or need a generator once there are enough of them.

Other ways to make the site feel alive, if the blog alone isn't enough: dates on the work items, a "recently shipped" strip, or client logos with the month each went live.

### Smaller
- Add the exact **Claremont street address + postcode** — currently set to "Claremont, Western Australia" in the contact section/page and all footers. Also unblocks a full `PostalAddress` in the home page schema, which currently stops at suburb level.
- Confirm the social proof / testimonial is current.
- **Security headers** (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) aren't being served. GitHub Pages can't set custom headers, so add them as a Cloudflare Transform Rule if wanted. They were previously declared in a `netlify.toml` left over from an earlier host, which never applied on Pages.
