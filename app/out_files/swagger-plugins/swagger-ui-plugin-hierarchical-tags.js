// hierarchical-tags.js
// Robust hierarchical tags plugin — exhaustive extraction + index + MutationObserver
// "All Tags" now rendered as a normal tag item (hier-leaf) with a subtle hover tint.
(function () {
  const accordion = false;

  function info(...args) { if (window.console) console.info("[HierTags]", ...args); }
  function warn(...args) { if (window.console) console.warn("[HierTags]", ...args); }

  function decodeIfNeeded(s) {
    if (s === null || s === undefined) return "";
    try { return decodeURIComponent(String(s)); } catch (e) { return String(s); }
  }

  function normalize(s) {
    return String(decodeIfNeeded(s || "") || "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function getTagNameFromAnchor(a) {
    try {
      const href = a.getAttribute("href") || "";
      const m = href.match(/#\/tag[\/%2F](.+)$/i);
      if (m && m[1]) {
        try { return decodeURIComponent(m[1]); } catch (e) { return (a.textContent || "").trim(); }
      }
    } catch (e) {}
    return (a.textContent || "").trim();
  }

  // -------------------------
  // Find operation containers (inclusive)
  // -------------------------
  function findAllOpContainers() {
    // Primary op containers across multiple swagger versions
    const selectors = [
      '.opblock',            // main swagger opblock
      '.opblock-row',        // variants
      '.opblock-sub',        // sub ops
      '.opblock-tag > .opblock', // opblocks inside grouped containers
      '.opblock-tag .opblock',
      '.opblock-tag-section .opblock'
    ];
    const set = new Set();
    const result = [];
    selectors.forEach(sel => {
      Array.from(document.querySelectorAll(sel)).forEach(el => {
        if (!set.has(el)) { set.add(el); result.push(el); }
      });
    });
    // Also include any .opblock-summary parents if they exist and not captured
    Array.from(document.querySelectorAll('.opblock-summary')).forEach(s => {
      const op = s.closest && s.closest('.opblock');
      if (op && !set.has(op)) { set.add(op); result.push(op); }
    });
    return result;
  }

  // -------------------------
  // Extract many candidate tag strings for a given op container
  // -------------------------
  function extractCandidates(opEl) {
    const cands = new Set();
    if (!opEl) return [];

    // 1) data-tag on element or ancestors (up to N levels)
    let n = opEl;
    for (let i = 0; i < 6 && n; i++) {
      try {
        if (n.getAttribute) {
          const dt = n.getAttribute('data-tag');
          if (dt) cands.add(dt);
        }
      } catch (e) {}
      n = n.parentElement;
    }

    // 2) any [data-tag] inside
    try {
      const dtEls = opEl.querySelectorAll && opEl.querySelectorAll('[data-tag]');
      if (dtEls && dtEls.length) {
        Array.from(dtEls).forEach(x => {
          try { const v = x.getAttribute && x.getAttribute('data-tag'); if (v) cands.add(v); } catch (e) {}
        });
      }
    } catch (e) {}

    // 3) common inner selectors (summary/tag elements)
    const selectors = [
      '.opblock-summary .opblock-tag',
      '.opblock-summary .tag',
      '.opblock-summary .opblock-title',
      '.opblock-summary .opblock-tag__name',
      '.opblock-tag__name',
      '.tag .tag-name',
      '.opblock-tag .opblock-tag-name',
      '.opblock-heading .ops-title',
      '.opblock-summary .opblock-tag .tag-name'
    ];
    selectors.forEach(sel => {
      try {
        const q = opEl.querySelector && opEl.querySelector(sel);
        if (q && q.textContent) cands.add(q.textContent.trim());
      } catch (e) {}
    });

    // 4) nearest parent group header (e.g., .opblock-tag, .opblock-tag-section or an h3)
    try {
      const grp = opEl.closest && (opEl.closest('.opblock-tag') || opEl.closest('.opblock-tag-section') || opEl.closest('.tag'));
      if (grp) {
        // prefer heading inside group
        const h = grp.querySelector && (grp.querySelector('h3') || grp.querySelector('.opblock-summary') || grp.querySelector('.tag-name'));
        if (h && h.textContent) cands.add(h.textContent.trim());
        else if (grp.textContent) cands.add(grp.textContent.trim());
      }
    } catch (e) {}

    // 5) preceding siblings heuristic: walk backwards up to a few nodes to find a header
    try {
      let prev = opEl.previousElementSibling;
      let hops = 0;
      while (prev && hops < 10) {
        try {
          if (prev.matches && (prev.matches('.opblock-tag-section') || prev.matches('.opblock-tag') || prev.matches('.tag') || prev.querySelector && prev.querySelector('h3'))) {
            const h3 = prev.querySelector && (prev.querySelector('h3') || prev.querySelector('.tag-name') || prev.querySelector('.opblock-summary'));
            if (h3 && h3.textContent) { cands.add(h3.textContent.trim()); break; }
            if (prev.textContent) { cands.add(prev.textContent.trim()); break; }
          }
        } catch (e) {}
        prev = prev.previousElementSibling;
        hops++;
      }
    } catch (e) {}

    // 6) fallback: id or first non-empty text
    try {
      if (opEl.id) cands.add(opEl.id);
      const txt = (opEl.textContent || "").split(/\n/).map(x => x.trim()).filter(Boolean)[0] || "";
      if (txt) cands.add(txt);
    } catch (e) {}

    // normalize & dedupe
    const normalized = Array.from(cands).map(x => normalize(x)).filter(Boolean);
    return Array.from(new Set(normalized));
  }

  // -------------------------
  // Index: map tag variants -> Set of op elements
  // -------------------------
  let tagIndex = new Map();
  let opsList = []; // list of all op elements discovered
  let lastPrefix = "";

  function addToIndex(key, op) {
    if (!key) return;
    const k = normalize(key);
    if (!k) return;
    let s = tagIndex.get(k);
    if (!s) { s = new Set(); tagIndex.set(k, s); }
    s.add(op);
  }

  function addVariants(raw, op) {
    const tag = normalize(raw || "");
    if (!tag) return;
    addToIndex(tag, op);

    const parts = tag.split('|').map(p => p.trim()).filter(Boolean);
    // single segments
    parts.forEach(p => addToIndex(p, op));
    // prefixes and suffixes
    for (let i = 1; i <= parts.length; i++) {
      const prefix = parts.slice(0, i).join('|');
      addToIndex(prefix, op);
    }
    for (let i = 0; i < parts.length; i++) {
      const suffix = parts.slice(i).join('|');
      addToIndex(suffix, op);
    }
  }

  function buildIndex() {
    tagIndex = new Map();
    opsList = findAllOpContainers();
    opsList.forEach(op => {
      const candidates = extractCandidates(op);
      candidates.forEach(c => addVariants(c, op));
    });
    info("Index built:", tagIndex.size, "tags → ops:", opsList.length);
  }

  // -------------------------
  // Apply matching: mark matched ops 'hier-match' and others 'hier-dim'
  // -------------------------
  function applyMatch(prefixRaw) {
    const prefix = normalize(prefixRaw || "");
    if (!prefix) {
      clearAll();
      lastPrefix = "";
      return;
    }
    lastPrefix = prefix;

    // ensure index present
    if (!tagIndex || !tagIndex.size) buildIndex();

    // find matching keys in index using same heuristics
    const prefLast = prefix.split('|').pop().trim();
    const matchedOps = new Set();

    for (const key of tagIndex.keys()) {
      if (!key) continue;
      if (key === prefix) {
        tagIndex.get(key).forEach(o => matchedOps.add(o)); continue;
      }
      if (key.startsWith(prefix)) {
        tagIndex.get(key).forEach(o => matchedOps.add(o)); continue;
      }
      const keyLast = key.split('|').pop().trim();
      if (keyLast && prefLast && keyLast === prefLast) {
        tagIndex.get(key).forEach(o => matchedOps.add(o)); continue;
      }
      if (key.includes(prefix)) {
        tagIndex.get(key).forEach(o => matchedOps.add(o)); continue;
      }
    }

    if (!matchedOps.size) {
      // nothing matched — clear dims to avoid shading everything
      clearAll();
      return;
    }

    // Apply classes to every discovered op
    opsList.forEach(op => {
      if (matchedOps.has(op)) applyMatchClass(op);
      else applyDimClass(op);
    });

    // Mark parent grouping headers: if any op inside a group matched, mark group match
    Array.from(document.querySelectorAll('.opblock-tag, .opblock-tag-section, .tag')).forEach(group => {
      try {
        let groupMatched = false;
        const gdt = (group.getAttribute && group.getAttribute('data-tag')) ? normalize(group.getAttribute('data-tag')) : "";
        if (gdt && (gdt === prefix || gdt.startsWith(prefix) || gdt.split('|').pop().trim() === prefix.split('|').pop().trim())) groupMatched = true;
        Array.from(group.querySelectorAll('.opblock, .opblock-row, .opblock-sub')).forEach(child => {
          if (matchedOps.has(child)) groupMatched = true;
        });
        if (groupMatched) {
          group.classList.add('hier-match'); group.classList.remove('hier-dim');
        } else {
          group.classList.add('hier-dim'); group.classList.remove('hier-match');
        }
      } catch (e) {}
    });

    // highlight right-side anchors
    highlightRightSide(prefix);
  }

  function clearAll() {
    document.querySelectorAll('.opblock, .opblock-row, .opblock-sub, .opblock-tag, .opblock-tag-section, .tag').forEach(el => {
      el.classList.remove('hier-dim', 'hier-match');
    });
    document.querySelectorAll('a.hier-right-selected').forEach(a => a.classList.remove('hier-right-selected'));
  }

  function applyMatchClass(el) {
    try {
      el.classList.remove('hier-dim'); el.classList.add('hier-match');
      const op = el.closest && el.closest('.opblock');
      if (op) { op.classList.remove('hier-dim'); op.classList.add('hier-match'); }
    } catch (e) {}
  }

  function applyDimClass(el) {
    try {
      el.classList.remove('hier-match'); el.classList.add('hier-dim');
      const op = el.closest && el.closest('.opblock');
      if (op) { op.classList.remove('hier-match'); op.classList.add('hier-dim'); }
    } catch (e) {}
  }

  // -------------------------
  // Right-side anchors highlight
  // -------------------------
  function highlightRightSide(prefixRaw) {
    const prefix = normalize(prefixRaw || "");
    const anchors = Array.from(document.querySelectorAll("a[href*='#/tag/'], a[href*='#/tag%2F']"));
    if (!anchors.length) {
      document.querySelectorAll('.opblock-summary .opblock-tag, .tag, .tag-name').forEach(el => el.classList.remove('hier-right-selected'));
      return;
    }
    let any = false;
    anchors.forEach(a => {
      const name = normalize(getTagNameFromAnchor(a));
      let matched = false;
      if (!name) matched = false;
      else {
        if (name === prefix) matched = true;
        else if (name.startsWith(prefix)) matched = true;
        else {
          const nameLast = name.split('|').pop().trim();
          const prefLast = prefix.split('|').pop().trim();
          if (nameLast && prefLast && nameLast === prefLast) matched = true;
          else if (name.includes(prefix)) matched = true;
        }
      }
      if (matched) { a.classList.add('hier-right-selected'); any = true; }
      else a.classList.remove('hier-right-selected');
    });
    if (!any) anchors.forEach(a => a.classList.remove('hier-right-selected'));
  }

  // -------------------------
  // Sidebar render code (with "All Tags" rendered as a normal tag item)
  // -------------------------
  function renderNode(node, name, fullPath = name) {
    const li = document.createElement("li");
    li.className = "hier-tag-node";

    if (node.children && Object.keys(node.children).length) {
      const toggle = document.createElement("button");
      toggle.className = "hier-toggle";
      toggle.type = "button";
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", `Toggle ${name}`);
      toggle.tabIndex = 0;

      const label = document.createElement("span");
      label.className = "hier-toggle-label";
      label.textContent = name;

      const caret = document.createElement("span");
      caret.className = "hier-caret";
      caret.setAttribute("aria-hidden", "true");
      caret.textContent = "▸";

      toggle.appendChild(caret);
      toggle.appendChild(label);
      li.appendChild(toggle);

      const ul = document.createElement("ul");
      ul.className = "hier-tag-children";
      ul.style.display = "none";

      Object.keys(node.children).sort().forEach((childName) => {
        ul.appendChild(renderNode(node.children[childName], childName, `${fullPath}|${childName}`));
      });

      li.appendChild(ul);

      toggle.addEventListener("click", (ev) => {
        ev.preventDefault(); ev.stopPropagation();
        const expanded = toggle.getAttribute("aria-expanded") === "true";
        if (expanded) {
          collapseNode(toggle, ul);
          applyMatch(''); // clear
          try { location.hash = "#/"; } catch (e) { history.pushState(null, '', '#/'); }
        } else {
          if (accordion) closeSiblings(li);
          expandNode(toggle, ul);
          applyMatch(fullPath);
          try {
            location.hash = '#/tag/' + encodeURIComponent(fullPath);
          } catch (e) {
            history.pushState(null, '', '#/tag/' + encodeURIComponent(fullPath));
            window.dispatchEvent(new HashChangeEvent('hashchange'));
          }
        }
        setActive(toggle);
        expandVisibleSections(fullPath);
      });

      toggle.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); toggle.click(); }
      });

    } else {
      const a = document.createElement("a");
      a.className = "hier-leaf";
      a.textContent = name;
      a.href = "#/tag/" + encodeURIComponent(fullPath);
      li.appendChild(a);

      a.addEventListener("click", (ev) => {
        ev.preventDefault(); ev.stopPropagation();
        const rawHash = (a.href.split('#')[1] || '');
        try { location.hash = rawHash; } catch (e) { history.pushState(null, '', '#' + rawHash); window.dispatchEvent(new HashChangeEvent('hashchange')); }
        applyMatch(fullPath);
        setTimeout(() => {
          const target = document.getElementById(rawHash) ||
            document.querySelector(`[data-tag="${fullPath}"]`) ||
            document.querySelector(`.opblock-tag[data-tag="${fullPath}"]`);
          if (target) { try { target.scrollIntoView({ behavior: 'smooth' }); } catch (e) { target.scrollIntoView(); } }
        }, 300);
        setActive(a);
        expandVisibleSections(fullPath);
      });
    }

    return li;
  }

  function expandNode(toggle, ul) { toggle.setAttribute("aria-expanded", "true"); const caret = toggle.querySelector(".hier-caret"); if (caret) caret.textContent = "▾"; ul.style.display = ""; }
  function collapseNode(toggle, ul) { toggle.setAttribute("aria-expanded", "false"); const caret = toggle.querySelector(".hier-caret"); if (caret) caret.textContent = "▸"; ul.style.display = "none"; }
  function closeSiblings(li) { const parent = li.parentElement; if (!parent) return; Array.from(parent.children).forEach((sibling) => { if (sibling === li) return; const btn = sibling.querySelector(".hier-toggle"); const ul = sibling.querySelector(".hier-tag-children"); if (btn && ul) collapseNode(btn, ul); }); }
  function setActive(element) { document.querySelectorAll('.hier-toggle.active, .hier-leaf.active').forEach(el => el.classList.remove('active')); element.classList.add('active'); }

  function expandVisibleSections(prefix) {
    // open ops/groups that relate to prefix
    opsList.forEach(el => {
      const candidates = extractCandidates(el);
      const shouldOpen = !prefix || candidates.some(c => {
        if (!c) return false;
        if (c === prefix) return true;
        if (c.startsWith(prefix)) return true;
        const cLast = c.split('|').pop().trim();
        const pLast = prefix.split('|').pop().trim();
        if (cLast && pLast && cLast === pLast) return true;
        if (c.includes(prefix)) return true;
        return false;
      });
      if (shouldOpen) {
        try {
          const header = el.querySelector('.opblock-summary') || el.querySelector('.opblock-tag__summary') || el.querySelector('.opblock-title');
          if (header && el.getAttribute('data-is-open') !== 'true') header.click();
        } catch (e) {}
      }
    });
  }

  // build tree / sidebar
  function buildTree(items) {
    const root = { children: {}, href: null };
    items.forEach((it) => {
      const parts = (it.text || "").split("|").map(p => p.trim()).filter(Boolean);
      if (!parts.length) return;
      let cur = root;
      parts.forEach((p, idx) => {
        if (!cur.children[p]) cur.children[p] = { children: {}, href: null };
        if (idx === parts.length - 1 && it.href) cur.children[p].href = it.href;
        cur = cur.children[p];
      });
    });
    return root;
  }

  function createWrapper(tree) {
    const wrapper = document.createElement("div");
    wrapper.className = "hierarchical-tags-wrapper";

    // --- NEW: create top "All Tags" as a normal tag-like item ---
    const topUlWrapper = document.createElement("ul");
    topUlWrapper.className = "hier-top-wrap";
    const allLi = document.createElement("li");
    allLi.className = "hier-tag-node";
    const allA = document.createElement("a");
    allA.className = "hier-leaf hier-all";
    allA.href = "#/";
    allA.textContent = "All Tags";
    allA.addEventListener("click", (ev) => {
      ev.preventDefault(); ev.stopPropagation();
      clearAll();
      try { location.hash = "#/"; } catch (e) { history.pushState(null, '', '#/'); }
      // remove active class from other sidebar items
      document.querySelectorAll('.hier-toggle.active, .hier-leaf.active').forEach(el => el.classList.remove('active'));
      allA.classList.add('active');
    });
    allLi.appendChild(allA);
    topUlWrapper.appendChild(allLi);
    wrapper.appendChild(topUlWrapper);
    // --- end All Tags insertion ---

    const topUl = document.createElement("ul");
    topUl.className = "hier-tag-root";
    Object.keys(tree.children).sort().forEach(name => { topUl.appendChild(renderNode(tree.children[name], name)); });
    wrapper.appendChild(topUl);
    injectStyles();
    return wrapper;
  }

  function injectStyles() {
    if (document.getElementById("hier-tags-styles")) return;
    const style = document.createElement("style");
    style.id = "hier-tags-styles";
    style.textContent = `
.hierarchical-tags-wrapper { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 12px; background: #f8f9fa; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.06); }

/* make "All Tags" visually identical to normal tag items, with a slightly lighter hover tint */
.hier-top-wrap { list-style: none; margin: 0 0 8px 0; padding-left: 12px; }
.hier-top-wrap .hier-tag-node { margin: 0 0 6px 0; }
.hier-leaf.hier-all { display:block; text-decoration:none; padding:6px 12px; border-radius:6px; background: #d8dde1ff; color: #373839ff; transition: background 0.2s; }
.hier-leaf.hier-all:hover { background: #9ac1e8ff; color: #537597ff; }

/* existing styles */
.hierarchical-tags-wrapper ul { list-style: none; margin: 0; padding-left: 12px; }
.hier-tag-root > li { margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 4px; }
.hier-tag-node { margin: 0 0 6px 0; line-height: 1.4; }
.hier-toggle { display:flex; align-items:center; gap:10px; border: none; background: #fff; padding: 8px 12px; cursor: pointer; font-weight: 500; width:100%; text-align: left; border-radius: 6px; transition: background 0.2s; }
.hier-toggle:hover, .hier-toggle.active { background: #e9ecef; }
.hier-toggle:focus { outline: none; box-shadow: 0 0 0 2px rgba(25,118,210,0.14); }
.hier-caret { font-size: 0.9em; display:inline-block; width: 16px; transition: transform 0.2s; }
.hier-toggle[aria-expanded="true"] .hier-caret { transform: rotate(90deg); }
.hier-toggle-label { flex:1; color: #333; }
.hier-tag-children { margin-left: 8px; padding: 4px 0; border-left: 2px solid #ddd; }
.hier-leaf { display:block; text-decoration:none; padding:6px 12px; border-radius:6px; color:#495057; transition: background 0.2s; }
.hier-leaf:hover, .hier-leaf.active { background: #e9ecef; text-decoration: none; color: #212529; }
.hier-sidebar { box-sizing:border-box; position:fixed; left:0; top:0; bottom:0; width:300px; overflow:auto; padding:16px; background:#fff; border-right:1px solid #dee2e6; z-index:9999; box-shadow: 2px 0 5px rgba(0,0,0,0.05); }
.hier-adjusted-main { margin-left: 320px !important; transition: margin-left 0.3s; }

.opblock-tag.hier-dim, .opblock.hier-dim, .opblock-row.hier-dim, .opblock-sub.hier-dim { opacity: 0.35 !important; transition: opacity 0.15s ease-in-out; pointer-events: auto; }
.opblock-tag.hier-match, .opblock.hier-match, .opblock-row.hier-match, .opblock-sub.hier-match { outline: 2px solid rgba(25,118,210,0.12); box-shadow: 0 1px 0 rgba(25,118,210,0.06) inset; transition: box-shadow 0.15s; }

a.hier-right-selected,
a.hier-right-selected .tag-name,
a.hier-right-selected .opblock-tag {
  background: #e6f0ff !important;
  border-radius: 6px;
  padding: 4px 8px;
  box-shadow: 0 1px 0 rgba(0,0,0,0.04) inset;
  color: #0b66d0 !important;
  text-decoration: none !important;
}
`;
    document.head.appendChild(style);
  }

  function injectSidebar(wrapper) {
    if (document.getElementById("hier-sidebar")) {
      const ex = document.getElementById("hier-sidebar");
      ex.innerHTML = "";
      ex.appendChild(wrapper);
      info("Updated existing injected sidebar");
      return true;
    }

    const root = document.querySelector("#swagger-ui") || document.body;
    if (!root) { warn("No root (#swagger-ui) found to inject sidebar"); return false; }

    const sidebar = document.createElement("div");
    sidebar.id = "hier-sidebar";
    sidebar.className = "hier-sidebar";
    sidebar.appendChild(wrapper);

    if (root.firstChild) root.insertBefore(sidebar, root.firstChild);
    else root.appendChild(sidebar);

    const mainCandidates = [
      "#swagger-ui .swagger-ui", "#swagger-ui .wrapper", "#swagger-ui .swagger-container",
      ".swagger-ui", ".swagger-container", ".container", "#swagger-ui"
    ];
    let shifted = false;
    for (const sel of mainCandidates) {
      const el = document.querySelector(sel);
      if (el && el !== sidebar) {
        el.classList.add("hier-adjusted-main");
        info("Shifted main content using selector:", sel);
        shifted = true;
        break;
      }
    }
    if (!shifted) warn("No main content found to shift for sidebar");
    info("Injected sidebar for hierarchical tags");
    return true;
  }

  function transformTagsOnce() {
    const anchors = Array.from(document.querySelectorAll("a[href*='#/tag/'], a[href*='#/tag%2F']"));
    let items = [];

    if (anchors.length) {
      anchors.forEach(a => {
        const name = getTagNameFromAnchor(a);
        const href = a.getAttribute("href");
        if (name) items.push({ text: name, href: href });
      });
      info("Found", items.length, "tag anchors (href-based).");
    } else {
      const blocks = Array.from(document.querySelectorAll(".opblock-tag, .opblock-tag-section h3, .tag, .tag-name, .opblock-summary .opblock-tag"));
      blocks.forEach(b => {
        const t = (b.textContent || "").trim();
        if (t) items.push({ text: t, href: "#/" + encodeURIComponent(t) });
      });
      info("Fallback found", items.length, "tags from opblock structures");
    }

    if (!items.length) { warn("No tag items found on page to transform"); return false; }

    const tree = buildTree(items);
    const wrapper = createWrapper(tree);

    injectSidebar(wrapper);
    buildIndex(); // build index after injecting sidebar

    return true;
  }

  function waitAndTransform(maxWaitMs) {
    const start = Date.now();
    let done = false;
    function attempt() {
      if (done) return;
      try {
        const ok = transformTagsOnce();
        if (ok) { done = true; return; }
      } catch (e) { warn("transform attempt error", e); }
      if (Date.now() - start < (maxWaitMs || 6000)) setTimeout(attempt, 300);
      else warn("Timed out waiting for tags to appear");
    }
    attempt();
  }

  window.transformHierarchicalTags = function (maxMs) { waitAndTransform(maxMs || 6000); };
  window.hierarchicalTagsPlugin = function (opts) { return {}; };
  window.HierarchicalTagsPlugin = window.hierarchicalTagsPlugin;

  // -------------------------
  // Observe DOM and rebuild index + reapply last selection
  // -------------------------
  let rebuildTimer = null;
  const observer = new MutationObserver(() => {
    if (rebuildTimer) clearTimeout(rebuildTimer);
    rebuildTimer = setTimeout(() => {
      try {
        buildIndex();
        if (lastPrefix) applyMatch(lastPrefix);
      } catch (e) { warn("rebuild index err", e); }
    }, 180);
  });

  function startObserving() {
    try {
      const root = document.querySelector("#swagger-ui") || document.body;
      observer.observe(root, { childList: true, subtree: true, attributes: false });
    } catch (e) { warn("Could not start observer", e); }
  }

  // react to user clicking right-side tags (hash change)
  window.addEventListener('hashchange', () => {
    const m = location.hash.match(/#\/tag\/(.+)$/);
    const tag = m ? decodeURIComponent(m[1]) : "";
    if (tag) {
      buildIndex(); // ensure fresh index
      applyMatch(tag);
    } else {
      clearAll();
    }
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      window.transformHierarchicalTags(6000);
      startObserving();
    });
  } else {
    window.transformHierarchicalTags(6000);
    startObserving();
  }

  info("hierarchical-tags (exhaustive-op) loaded (All Tags as normal tag item)");
})();
