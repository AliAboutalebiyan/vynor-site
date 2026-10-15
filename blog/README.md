# Blog — how it works

This blog is **file-based and bilingual** (English + Persian). Posts live in
**numbered folders** so each story (in both languages) is managed by one number:

```
blog/
├── blog.js                  # renders the post list from posts.json
├── blog.css                 # shared styles (RTL + LTR)
├── posts.json               # the post index (single source of truth)
├── en/index.html            # English blog listing
├── fa/index.html            # Persian blog listing
└── posts/
    └── 001/
        ├── en.html          # English version of post 001
        └── fa.html          # Persian version of post 001
```

Each numbered folder (`001`, `002`, …) contains both language versions of one
story. To manage posts later, work by number: `001` is the first post, and both
`en.html` and `fa.html` inside it must stay in sync.

## Adding a new post (3 steps)

1. **Create the next numbered folder**, e.g. `blog/posts/003/`, and copy the
   body/content of an existing post into `003/en.html` and `003/fa.html`.

2. **Edit the content and metadata** in each file:
   - `<title>`, `<meta name="description">`, `<h1>` and the body.
   - `<time datetime="YYYY-MM-DD">` and the visible date.
   - The language toggle (`.blog-lang-toggle`) already points to the sibling
     file (`/blog/posts/003/fa.html` ↔ `/blog/posts/003/en.html`).

3. **Register it in `blog/posts.json`** with a matching `id`:

```json
{
  "id": "003",
  "slug": "my-new-post",
  "en": { "title": "...", "summary": "...", "date": "2026-03-01",
          "url": "posts/003/en.html" },
  "fa": { "title": "...", "summary": "...", "date": "2026-03-01",
          "url": "posts/003/fa.html" }
}
```

The listing pages (`blog/en/`, `blog/fa/`) pick it up automatically via
`blog.js`. Paths are depth-dependent: pages in `blog/posts/NNN/` use
`../../../assets/style.css` and `../../../blog/blog.css`.
