/* blog/blog.js — renders the post list on blog/en/index.html and blog/fa/index.html */
(function () {
  "use strict";

  var script = document.currentScript;
  var postsUrl = script && script.src ? new URL("posts.json", script.src).href : "posts.json";
  var lang = (document.documentElement.lang || "en").toLowerCase().slice(0, 2) === "fa" ? "fa" : "en";
  var isRTL = lang === "fa";
  var listEl = document.getElementById("posts");
  var statusEl = document.getElementById("postStatus");

  function escapeHTML(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  // Resolve a record URL to a link that works from blog/<lang>/index.html
  function toLocalLink(url) {
    if (!url) return "#";
    if (/^https?:\/\//i.test(url)) return url;
    if (url.charAt(0) === "/") return "../../" + url.replace(/^\/+/, "");
    return "../" + String(url).replace(/^\.\//, ""); // e.g. "posts/x.html" -> "../posts/x.html"
  }

  function showStatus(msg) {
    if (statusEl) {
      statusEl.textContent = msg;
      statusEl.setAttribute("dir", isRTL ? "rtl" : "ltr");
    }
  }

  if (!listEl) return;

  fetch(postsUrl, { headers: { "Accept": "application/json" } })
    .then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    })
    .then(function (data) {
      var recs = data && Array.isArray(data) ? data : (data && Array.isArray(data.posts) ? data.posts : null);
      if (!recs) throw new Error("Unexpected posts.json format");

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
