# Ordinary Agency — website

A minimal, editorial static site for ordinaryagency.com.au. No build step, no framework — just HTML, CSS and a little vanilla JS.

## Files
- `index.html` — home (long-scroll overview)
- `services.html` — detailed services
- `work.html` — portfolio grid
- `about.html` — story, values, process
- `contact.html` — contact details + form
- `404.html` — custom not-found page (Netlify serves it automatically)
- `style.css` — all styles (palette + type tokens are CSS variables at the top)
- `main.js` — scroll reveals, sticky-header state, mobile menu
- `favicon.svg` — brand mark
- `robots.txt` / `sitemap.xml` — SEO
- `netlify.toml` — deploy config

Header/footer markup is duplicated across pages (kept as static HTML for SEO — no JS-injected partials). If you change a nav link, update it in all five pages.

## Run locally
```
cd ordinaryagency-site
python3 -m http.server 4388
# open http://localhost:4388
```

## Deploy (Netlify)
Drag this folder onto app.netlify.com, or connect the repo. No build command needed — publish directory is the project root. The contact form uses Netlify Forms (`data-netlify="true"`), so submissions appear in the Netlify dashboard automatically once deployed.

## Brand
- **Type:** Fraunces (display serif) + Inter (sans)
- **Palette:** warm paper `#F7F4EF`, ink `#1B1A17`, clay accent `#C2552F` — all editable in `:root` in `style.css`

## To do
- Add the exact **Claremont street address + postcode** — currently set to "Claremont, Western Australia" in the contact section/page and all footers.
- Swap the placeholder cards in **Work** (and the home Work section) for real project images + names (replace the `data-placeholder` divs with `<img>`).
- Confirm the social proof / testimonial is current.
