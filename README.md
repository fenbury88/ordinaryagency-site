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
- `404.html` — custom not-found page (GitHub Pages serves it automatically)
- `style.css` — all styles (palette + type tokens are CSS variables at the top)
- `main.js` — scroll reveals, sticky-header state, mobile menu, contact form
- `favicon.svg` — brand mark
- `robots.txt` / `sitemap.xml` — SEO
- `CNAME` — custom domain for GitHub Pages. Don't delete it; the domain breaks.

Header/footer markup is duplicated across pages (kept as static HTML for SEO — no JS-injected partials). If you change a nav link, update it in **all nine pages**.

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

## Brand
- **Type:** Fraunces (wordmark) + Space Grotesk (display) + Inter (body)
- **Palette:** paper `#FAFAF7`, ink `#15150F`, green accent `#2C7A57` — all in `:root` in `style.css`

### The Haring layer
The bottom section of `style.css` is a self-contained design layer: flat primaries, 3px ink keylines, hard offset shadows, and original figure illustrations drawn in Keith Haring's visual language. (Drawn for this site — Haring's actual works are owned by the Keith Haring Foundation and aren't reproduced here.) It's appended last so it can be lifted out in one piece.

Every hue has **two tokens**, and this matters:
- `--accent` — text-safe, passes WCAG AA on paper
- `--accent-block` — the full-strength primary, for fills only

They are not interchangeable. Yellow `#FFC800` is 1.49:1 against paper — it can never carry text. The three service themes (`.theme-web` blue, `.theme-leads` red, `.theme-ai` yellow) each set both, so changing one variable re-themes a whole service page.

Figures are inline SVG using `data-body` / `data-head` / `data-rays` / `data-fill` attributes, styled entirely from `style.css`. They pick up whatever theme colour is in scope.

## Cache busting
`style.css` and `main.js` are linked with a `?v=YYYYMMDD` stamp in all nine pages. **Bump it whenever either file changes** — they're served with a 4-hour cache, so without a bump returning visitors keep the old copy:
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
- Add the exact **Claremont street address + postcode** — currently set to "Claremont, Western Australia" in the contact section/page and all footers.
- Confirm the social proof / testimonial is current.
- **Security headers** (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) aren't being served. GitHub Pages can't set custom headers, so add them as a Cloudflare Transform Rule if wanted. They were previously declared in a `netlify.toml` left over from an earlier host, which never applied on Pages.
