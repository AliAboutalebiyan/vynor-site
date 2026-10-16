"""Build the static site; numbered post folders are the only blog source of truth.

No third-party packages or network access are needed. Run from any directory:
    python scripts/build_site.py
"""

from datetime import date
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET


LANGUAGES = ("fa", "en")
POSTS_MARKER = "<!-- BLOG_POSTS -->"
OUTPUT_MARKER = ".vynor-generated"
NAVBAR = re.compile(r'<header class="navbar">.*?</header>', re.S)
LATIN_RUN = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._/@:+#²³%()\-]*")
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


class BuildError(ValueError):
    """Invalid input; do not replace the last successfully built site."""


class PostMetadata(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.language = ""
        self.description = ""
        self.published = ""
        self.titles = []
        self.in_heading = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.language = attrs.get("lang", "")
        elif tag == "meta" and attrs.get("name", "").lower() == "description":
            self.description = attrs.get("content", "").strip()
        elif tag == "h1":
            self.titles.append("")
            self.in_heading = True
        elif tag == "time" and not self.published:
            self.published = attrs.get("datetime", "")

    def handle_endtag(self, tag):
        if tag == "h1":
            self.in_heading = False

    def handle_data(self, text):
        if self.in_heading:
            self.titles[-1] += text


def read(path):
    return path.read_text(encoding="utf-8-sig")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def formatted_text(text, lang):
    """Escape plain metadata, isolating Latin runs once in Persian cards."""
    if lang != "fa":
        return escape(text)
    chunks, position = [], 0
    for match in LATIN_RUN.finditer(text):
        value = match.group().rstrip()
        chunks.append(escape(text[position:match.start()]))
        chunks.append('<bdi class="latin" lang="en">' + escape(value) + '</bdi>')
        position = match.start() + len(value)
    return "".join(chunks) + escape(text[position:])


def discover_posts(root):
    posts, numbers = [], set()
    for folder in sorted((root / "blog/posts").iterdir()):
        if not folder.is_dir() or not re.fullmatch(r"[0-9]{3,}", folder.name):
            continue
        if (folder / ".draft").exists():
            continue
        number = int(folder.name)
        if number in numbers:
            raise BuildError(f"Duplicate post number: {folder.name}")
        numbers.add(number)
        post = {"id": folder.name, "folder": folder}
        for lang in LANGUAGES:
            file = folder / f"{lang}.html"
            if not file.is_file():
                raise BuildError(f"{file.relative_to(root)} is missing. Upload both languages together, or add .draft.")
            html = read(file)
            metadata = PostMetadata(html)
            if metadata.language != lang:
                raise BuildError(f"{file.relative_to(root)}: html lang must be {lang}.")
            if len(metadata.titles) != 1 or not metadata.titles[0].strip():
                raise BuildError(f"{file.relative_to(root)}: exactly one non-empty h1 is required.")
            if not metadata.description:
                raise BuildError(f"{file.relative_to(root)}: meta description is required.")
            try:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", metadata.published):
                    raise ValueError()
                date.fromisoformat(metadata.published)
            except ValueError:
                raise BuildError(f"{file.relative_to(root)}: time datetime must be a valid YYYY-MM-DD date.") from None
            if not NAVBAR.search(html) or 'class="post-body"' not in html:
                raise BuildError(f"{file.relative_to(root)}: use the post-template HTML structure.")
            post[lang] = {
                "html": html,
                "title": " ".join(metadata.titles[0].split()),
                "summary": metadata.description,
                "date": metadata.published,
                "url": f"posts/{folder.name}/{lang}.html",
            }
        posts.append(post)
    return posts


def post_header(root, lang):
    match = NAVBAR.search(read(root / lang / "index.html"))
    if not match:
        raise BuildError(f"{lang}/index.html has no shared navbar.")
    header = match.group()
    # Read the shared structure from the home page so future header edits propagate.
    other = "en" if lang == "fa" else "fa"
    targets = {
        "#hero": f"../../../{lang}/",
        "#skills": f"../../../{lang}/#skills",
        "#projects": f"../../../{lang}/#projects",
        "#experience": f"../../../{lang}/#experience",
        "#contact": f"../../../{lang}/contact/",
        "contact/": f"../../../{lang}/contact/",
        f"../blog/{lang}/": f"../../../blog/{lang}/",
        f"../{other}/": f"{other}.html",
    }
    header = re.sub(r'href="([^"]+)"', lambda m: f'href="{targets.get(m[1], m[1])}"', header)
    return header.replace(f'href="../../../blog/{lang}/"', f'href="../../../blog/{lang}/" aria-current="location"')


def prepare_article(root, post, lang, base_url):
    record = post[lang]
    html = record["html"]
    title = record["title"] + (" — وبلاگ واینور" if lang == "fa" else " — vynor Blog")
    html, count = re.subn(r'<title>.*?</title>', lambda _: f'<title>{escape(title)}</title>', html, count=1, flags=re.S)
    if not count:
        raise BuildError(f"{record['url']}: title element is missing.")

    def remove_old_links(match):
        tag = match.group()
        parser = HTMLParser()
        attrs = {}
        parser.handle_starttag = lambda _tag, pairs: attrs.update(pairs)
        parser.feed(tag)
        if attrs.get("rel") == "canonical" or (attrs.get("rel") == "alternate" and "hreflang" in attrs):
            return ""
        return tag

    html = re.sub(r'<link\b[^>]*>', remove_old_links, html)
    links = [f'<link rel="canonical" href="{base_url}/blog/{record["url"]}">']
    for alternate in LANGUAGES:
        links.append(f'<link rel="alternate" hreflang="{alternate}" href="{base_url}/blog/{post[alternate]["url"]}">')
    html = html.replace('</head>', '\n'.join(links) + '\n</head>', 1)
    html = NAVBAR.sub(lambda _: post_header(root, lang), html, count=1)
    # Authors edit the machine-readable date once; the visible date follows it.
    html = re.sub(r'(<time\b[^>]*>).*?(</time>)', lambda m: m[1] + formatted_text(record["date"], lang) + m[2], html, count=1, flags=re.S)
    return html


def render_cards(posts, lang):
    ordered = sorted(posts, key=lambda p: (p[lang]["date"], int(p["id"])), reverse=True)
    if not ordered:
        return '<p class="post-status">' + ("هنوز نوشته‌ای منتشر نشده است." if lang == "fa" else "No posts published yet.") + '</p>'
    cards = []
    for post in ordered:
        record = post[lang]
        cards.append(
            f'<a class="post-card" lang="{lang}" href="../{record["url"]}">'
            f'<div class="post-meta"><span class="pill date"><time datetime="{record["date"]}">'
            f'{formatted_text(record["date"], lang)}</time></span></div>'
            f'<h3>{formatted_text(record["title"], lang)}</h3>'
            f'<p>{formatted_text(record["summary"], lang)}</p></a>'
        )
    return '\n'.join(cards)


def write_sitemap(root, output, posts, base_url):
    ET.register_namespace("", SITEMAP_NS)
    tree = ET.parse(root / "sitemap.xml")
    urls = tree.getroot()
    for entry in list(urls):
        location = entry.find(f"{{{SITEMAP_NS}}}loc")
        if location is not None and "/blog/posts/" in (location.text or ""):
            urls.remove(entry)
    for post in posts:
        for lang in LANGUAGES:
            entry = ET.SubElement(urls, f"{{{SITEMAP_NS}}}url")
            ET.SubElement(entry, f"{{{SITEMAP_NS}}}loc").text = f"{base_url}/blog/{post[lang]['url']}"
            ET.SubElement(entry, f"{{{SITEMAP_NS}}}changefreq").text = "monthly"
            ET.SubElement(entry, f"{{{SITEMAP_NS}}}priority").text = "0.6"
    ET.indent(tree, space="  ")
    tree.write(output / "sitemap.xml", encoding="utf-8", xml_declaration=True)


def build(root):
    root = root.resolve()
    output = root / "_site"
    if output.resolve() != output or output.is_symlink() or (output.exists() and not (output / OUTPUT_MARKER).is_file()):
        raise BuildError("_site exists but is not a generated output folder; leaving it untouched.")
    domain = read(root / "CNAME").strip()
    if not re.fullmatch(r"[A-Za-z0-9.-]+", domain):
        raise BuildError("CNAME must contain one domain name.")
    base_url = "https://" + domain
    posts = discover_posts(root)
    # Prepare everything first: a broken article never replaces the previous build.
    with tempfile.TemporaryDirectory(prefix=".site-build-", dir=root) as temporary:
        stage = Path(temporary)
        for folder in ("assets", "en", "fa"):
            shutil.copytree(root / folder, stage / folder)
        for file in ("index.html", "robots.txt", "CNAME"):
            shutil.copy2(root / file, stage / file)
        (stage / "blog").mkdir()
        shutil.copy2(root / "blog/blog.css", stage / "blog/blog.css")
        for lang in LANGUAGES:
            html = read(root / f"blog/{lang}/index.html")
            if html.count(POSTS_MARKER) != 1:
                raise BuildError(f"blog/{lang}/index.html must contain exactly one {POSTS_MARKER}.")
            write(stage / f"blog/{lang}/index.html", html.replace(POSTS_MARKER, render_cards(posts, lang)))
        for post in posts:
            target = stage / "blog/posts" / post["id"]
            shutil.copytree(post["folder"], target)
            for lang in LANGUAGES:
                write(target / f"{lang}.html", prepare_article(root, post, lang, base_url))
        write_sitemap(root, stage, posts, base_url)
        write(stage / ".nojekyll", "")
        write(stage / OUTPUT_MARKER, "Generated by scripts/build_site.py\n")
        # Only the verified, generated directory inside this project may be replaced.
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(stage, output)
    return posts


if __name__ == "__main__":
    try:
        result = build(Path(__file__).resolve().parents[1])
    except (BuildError, OSError, ET.ParseError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        sys.exit(1)
    print(f"Built {len(result)} bilingual posts in _site: " + ", ".join(p["id"] for p in result))
