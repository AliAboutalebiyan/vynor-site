# Project preferences

- Work directly in `D:\Projects\Vynor\vynor-site-bilingual`. Do not update sibling copies, create ZIP archives, or provide download links unless the user asks. The user publishes to GitHub manually.
- In Persian content, every English/Latin text run must be exactly **2 CSS pixels smaller** than its surrounding Persian text. Keep B Mitra for Persian and use the shared `.latin` class for Latin text.
- Mark Latin text with `<bdi class="latin" lang="en">…</bdi>`, including technical names, English labels, email addresses, and domain names. Apply the class directly to an existing `bdi` rather than nesting another `.latin` element. Nested reductions would incorrectly subtract 4 pixels.
- The shared rule is `html[lang="fa"] .latin { font-size: calc(1em - 2px); }`. This rule must remain relative to the surrounding text and must not affect the English version of the site.
- Apply this convention to future Persian content as well. Keep link destinations, image paths, metadata, and other non-visible attributes unchanged when marking up text.
