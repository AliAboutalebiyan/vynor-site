# Blog — how it works

This blog is **file-based and bilingual** (English + Persian). You never touch the
index pages to publish a post; you add files and one JSON record.

```
blog/
├── blog.js                  # renders the post list from posts.json
├── blog.css                 # shared styles (RTL + LTR)
├── posts.json               # the post index (single source of truth)
├── en/index.html            # English blog listing
├── fa/index.html            # Persian blog listing
└── posts/
    ├── <slug>.html          # English post
    └── fa/<slug>.html       # Persian post
```

## Adding a new post (3 steps)

1. **Copy an existing pair** in `blog/posts/` — e.g. duplicate
   `first-steps-in-independent-websites.html` to `my-new-post.html` and
   `posts/fa/first-steps-in-independent-websites.html` to `posts/fa/my-new-post.html`.

2. **Edit the content and metadata** in each file:
   - `<title>`, `<meta name="description">`, `<h1>` and the body.
   - `<time datetime="YYYY-MM-DD">` and the visible date in the header.
   - **Do not change** the `<html lang/dir>`, the stylesheet links, or the
     nav/back/language-switch links — paths are depth-dependent:
     - English post (`blog/posts/`, depth 2): stylesheets `../../assets/style.css`
       and `../../blog/blog.css`, listing link `../en/`, Persian version `../fa/`,
       Home `../../en/`.
     - Persian post (`blog/posts/fa/`, depth 3): stylesheets `../../../assets/style.css`
       and `../../../blog/blog.css`, listing link `../../fa/`, English version `../../en/`,
       Home `../../fa/`.

3. **Register the post** in `blog/posts.json`. Keep records relative to `blog/`:
   URLs `posts/<slug>.html` (English) and `posts/fa/<slug>.html` (Persian).
   `blog.js` resolves them from `blog/en/` and `blog/fa/` automatically, sorts the
   list by `date` (newest first), and escapes all text before rendering.

```json
{
  "slug": "my-new-post",
  "en": { "title": "…", "summary": "…", "date": "2026-03-01",
          "url": "posts/my-new-post.html" },
  "fa": { "title": "…", "summary": "…", "date": "2026-03-01",
          "url": "posts/fa/my-new-post.html" }
}
```

> A post only appears in the list once it is in `posts.json`. If you publish only
> one language for now, omit the other language object — the listing shows only
> records that have the current page's language.

## Local testing

The post list is loaded with `fetch`, so the pages must be served over HTTP:

```bash
cd <project-root>
python3 -m http.server 8000
# then open:
#   http://localhost:8000/blog/en/
#   http://localhost:8000/blog/fa/
#   http://localhost:8000/blog/posts/first-steps-in-independent-websites.html
#   http://localhost:8000/blog/posts/fa/first-steps-in-independent-websites.html
```

Opening the files directly with `file://` will block the `fetch` call — use the
local server instead. If `posts.json` cannot be loaded, an error message is shown
in `#postStatus` on the listing pages.
