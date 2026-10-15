/* blog/blog.js — renders the post list on blog/en/index.html and blog/fa/index.html
 * Usage: <script src="../../blog/blog.js"></script>  (from blog/<lang>/index.html)
 * Add a post: create the HTML file(s) under blog/posts/ and add a record to blog/posts.json.
 */
(function () {
  "use strict";

  // Resolve posts.json relative to this script, so it works from any blog page.
  var scriptSrc = document.currentScript && document.currentScript.src
    ? document.currentScript.src : "";
  var postsUrl = scriptSrc
    ? new URL("../posts.json", scriptSrc).href   // -> <site>/blog/posts.json
    : "../../blog/posts.json";                   // fallback (same file)

  var lang = (document.documentElement.lang || "en").toLowerCase().slice(0, 2);
  var isRTL = lang === "fa";
  var listEl = document.getElementById("posts");
  var statusEl = document.getElementById("postStatus");

  function escapeHTML(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  // Normalize a record URL to a site-relative link that works from blog/<lang>/.
  // "posts/foo.html"            -> ../posts/foo.html
  // "/posts/foo.html" (absolute)-> ../../posts/foo.html
  // full http(s) URL            -> kept as-is
  function toLocalLink(url) {
    if (!url) return "#";
    if (/^https?:\/\//i.test(url)) return url;
    if (url.charAt(0) === "/") {
      // absolute from site root: strip leading slash, walk up from blog/<lang>/
      var depth = 2; // we are two levels below the site root
      var rel = "";
      for (var i = 0; i < depth; i++) rel += "../";
      return rel + url.replace(/^\/+/, "");
    }
    return "../" + url.replace(/^\.\//, "");
  }

  function showStatus(msg) {
    if (statusEl) {
      statusEl.textContent = msg;
      statusEl.setAttribute(!isRTL ? "dir" : "dir", isRTL ? "rtl" : "ltr");
    }
  }

  if (!listEl) return;

  fetch(postsUrl, { headers: { "Accept": "application/json" } })
    .then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    })
    .then(function (data) {
      var recs = (data && (data.posts || data)) || [];
      if (!Array.isArray(recs)) throw new Error("Unexpected posts.json format");

      var items = recs
        .map(function (r) { return r && (r[lang] || r); })
        .filter(function (r) { return r && r.title && r.url; })
        .sort(function (a, b) {
          var da = a.date ? String(a.date) : "";
          var db = b.date ? String(b.date) : "";
          return db.localeCompare(da); // newest first
        });

      if (!items.length) {
        showStatus(isRTL ? "هنوز نوشته‌ای منتشر نشده است." : "No posts published yet.");
        return;
      }

      listEl.innerHTML = items.map(function (r) {
        var href = toLocalLink(r.url);
        var date = escapeHTML(r.date || "");
        return '<a class="post-card" lang="' + escapeHTML(lang) + '" href="' + escapeHTML(href) + '">' +
          '<div class="post-meta">' +
            (date ? '<span class="pill date"><time datetime="' + date + '">' + date + "</time></span>" : "") +
          "</div>" +
          "<h3>" + escapeHTML(r.title) + "</h3>" +
          (r.summary ? "<p>" + escapeHTML(r.summary) + "</p>" : "") +
        "</a>";
      }).join("");
      if (statusEl) statusEl.textContent = "";
    })
    .catch(function (err) {
      console.error("[blog] failed to load posts:", err);
      showStatus(isRTL
        ? "خطا در بارگذاری فهرست نوشته‌ها. لطفاً صفحه را دوباره بارگذاری کنید."
        : "Failed to load the post list. Please reload the page.");
    });
})();
