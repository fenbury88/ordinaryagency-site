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
- **Type:** Fraunces (display serif) + Inter (sans)
- **Palette:** warm paper `#F7F4EF`, ink `#1B1A17`, clay accent `#C2552F` — all editable in `:root` in `style.css`

## To do
- Add the exact **Claremont street address + postcode** — currently set to "Claremont, Western Australia" in the contact section/page and all footers.
- Confirm the social proof / testimonial is current.
- **Security headers** (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) aren't being served. GitHub Pages can't set custom headers, so add them as a Cloudflare Transform Rule if wanted. They were previously declared in a `netlify.toml` left over from an earlier host, which never applied on Pages.
