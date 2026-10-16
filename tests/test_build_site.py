"""Exercise the upload-only publishing contract with isolated project copies."""

from pathlib import Path
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

from scripts.build_site import BuildError, build, formatted_text, read, write


PROJECT = Path(__file__).resolve().parents[1]


class BlogBuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix=".test-build-", dir=PROJECT)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "assets").mkdir()
        (self.root / "blog/posts").mkdir(parents=True)
        for relative in ("index.html", "robots.txt", "CNAME", "sitemap.xml", "blog/blog.css",
                         "en/index.html", "fa/index.html", "blog/en/index.html", "blog/fa/index.html"):
            write(self.root / relative, read(PROJECT / relative))

    def add_post(self, number, published="2026-10-16"):
        folder = self.root / "blog/posts" / number
        source = PROJECT / "blog/post-template"
        for lang in ("fa", "en"):
            html = read(source / f"{lang}.html")
            html = html.replace("YYYY-MM-DD", published)
            write(folder / f"{lang}.html", html)
        return folder

    def test_upload_folder_alone_updates_both_lists_metadata_and_sitemap(self):
        folder = self.add_post("007")
        # Simulate copying an old article without manually fixing its canonical URL.
        original = read(folder / "fa.html").replace('</head>', '<link rel="canonical" href="https://vynor.ir/blog/posts/002/fa.html">\n</head>')
        write(folder / "fa.html", original)
        write(folder / "images/example.svg", '<svg xmlns="http://www.w3.org/2000/svg"/>')
        posts = build(self.root)
        self.assertEqual([p["id"] for p in posts], ["007"])
        for lang in ("fa", "en"):
            listing = read(self.root / f"_site/blog/{lang}/index.html")
            self.assertIn(f'href="../posts/007/{lang}.html"', listing)
            self.assertNotIn("blog.js", listing)
            self.assertNotIn("BLOG_POSTS", listing)
            html = read(self.root / f"_site/blog/posts/007/{lang}.html")
            self.assertIn(f'rel="canonical" href="https://vynor.ir/blog/posts/007/{lang}.html"', html)
            self.assertIn('href="fa.html"' if lang == "en" else 'href="en.html"', html)
            self.assertNotIn("/posts/002/", html)
        locations = [e.text for e in ET.parse(self.root / "_site/sitemap.xml").iter() if e.tag.endswith("}loc")]
        self.assertEqual(len([u for u in locations if "/blog/posts/" in u]), 2)
        self.assertIn("https://vynor.ir/fa/", locations)
        self.assertTrue((self.root / "_site/blog/posts/007/images/example.svg").is_file())
        self.assertFalse((self.root / "_site/blog/post-template").exists())
        self.assertFalse((self.root / "_site/scripts").exists())
        self.assertEqual(read(folder / "fa.html"), original)

    def test_date_then_numeric_id_sorting_with_gaps_and_large_numbers(self):
        self.add_post("007", "2025-01-01")
        self.add_post("020", "2026-02-01")
        self.add_post("1000", "2026-02-01")
        build(self.root)
        listing = read(self.root / "_site/blog/fa/index.html")
        self.assertLess(listing.index("posts/1000/"), listing.index("posts/020/"))
        self.assertLess(listing.index("posts/020/"), listing.index("posts/007/"))

    def test_drafts_are_not_copied_or_indexed_even_if_incomplete(self):
        write(self.root / "blog/posts/004/.draft", "")
        write(self.root / "blog/posts/004/fa.html", "unfinished")
        self.add_post("005")
        build(self.root)
        self.assertFalse((self.root / "_site/blog/posts/004").exists())
        self.assertNotIn("/004/", read(self.root / "_site/sitemap.xml"))

    def test_missing_translation_does_not_replace_previous_output(self):
        self.add_post("001")
        build(self.root)
        previous = read(self.root / "_site/blog/fa/index.html")
        write(self.root / "blog/posts/003/fa.html", read(self.root / "blog/posts/001/fa.html"))
        with self.assertRaisesRegex(BuildError, "en.html is missing"):
            build(self.root)
        self.assertEqual(read(self.root / "_site/blog/fa/index.html"), previous)

    def test_bad_date_title_and_summary_stop_publication(self):
        folder = self.add_post("001")
        original = read(folder / "en.html")
        for broken, message in (
            (original.replace('datetime="2026-10-16"', 'datetime="2026-02-30"'), "valid YYYY-MM-DD"),
            (original.replace("<h1>", "<h1></h1><h1>"), "one non-empty h1"),
            (original.replace('name="description"', 'name="unused"'), "description is required"),
        ):
            with self.subTest(message=message):
                write(folder / "en.html", broken)
                with self.assertRaisesRegex(BuildError, message):
                    build(self.root)

    def test_removed_post_disappears_from_output_and_sitemap(self):
        self.add_post("001")
        second = self.add_post("002")
        build(self.root)
        # All paths here belong to the isolated temporary test project.
        shutil.rmtree(second)
        build(self.root)
        self.assertFalse((self.root / "_site/blog/posts/002").exists())
        self.assertNotIn("posts/002/", read(self.root / "_site/blog/en/index.html"))
        self.assertNotIn("posts/002/", read(self.root / "_site/sitemap.xml"))

    def test_template_needs_only_date_and_content_edits(self):
        self.add_post("004")
        build(self.root)
        html = read(self.root / "_site/blog/posts/004/fa.html")
        self.assertIn('href="en.html"', html)
        self.assertIn('href="https://vynor.ir/blog/posts/004/fa.html"', html)
        self.assertNotIn("YYYY-MM-DD", html)
        self.assertIn('id="navToggle"', html)

    def test_header_is_inherited_from_home_page(self):
        self.add_post("001")
        home = self.root / "en/index.html"
        write(home, read(home).replace('>Skills</a>', '>Capabilities</a>'))
        build(self.root)
        article = read(self.root / "_site/blog/posts/001/en.html")
        self.assertIn('href="../../../en/#skills">Capabilities</a>', article)

    def test_empty_blog_and_output_directory_guard(self):
        build(self.root)
        self.assertIn("No posts published yet.", read(self.root / "_site/blog/en/index.html"))
        (self.root / "_site/.vynor-generated").unlink()
        with self.assertRaisesRegex(BuildError, "leaving it untouched"):
            build(self.root)

    def test_generated_cards_escape_html_and_wrap_latin_once(self):
        result = formatted_text('آموزش Python و C++ <script>alert(1)</script>', 'fa')
        self.assertIn('<bdi class="latin" lang="en">Python</bdi>', result)
        self.assertIn('<bdi class="latin" lang="en">C++</bdi>', result)
        self.assertNotIn('<script>', result)
        self.assertNotIn('<bdi class="latin" lang="en"><bdi', result)
        self.assertEqual(formatted_text('A & B', 'en'), 'A &amp; B')


if __name__ == "__main__":
    unittest.main()
