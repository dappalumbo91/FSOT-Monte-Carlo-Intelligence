/**
 * FSOT connective visual — Obsidian graph × neural growth.
 *
 * Full archive graphs (~500 nodes / 3k edges) stay chaotic if every edge is a
 * hard spring forever. We:
 *  1) pin multi-scale home positions on D_eff shells (the "solidified" pattern)
 *  2) anneal temperature so motion settles (like the small core graph did)
 *  3) only strong-spring structural axons; dense lean-overlap is visual only
 */
(() => {
  const canvas = document.getElementById("graph");
  const ctx = canvas.getContext("2d");
  const $ = (id) => document.getElementById(id);

  let W = 0, H = 0, dpr = 1;
  let nodes = [];
  let edges = [];
  let structuralEdges = []; // springs that actually move layout
  let structuralIds = new Set();
  let meta = {};
  let selected = null;
  let hover = null;
  let sim = true;
  let t0 = performance.now();
  let temp = 1.0;           // anneal 1 → 0
  let settled = false;
  let frame = 0;
  let ringScale = 1.0;      // grows for dense graphs
  let isFull = false;

  // camera
  let cam = { x: 0, y: 0, scale: 1 };
  let drag = null; // { mode: 'pan'|'node', id, ox, oy, nx, ny }

  // Edge kinds that may tug layout (everything else is display-only axon)
  const STRUCTURAL_KINDS = new Set([
    "seed_to_law",
    "law_to_domain",
    "routes_to_core",
    "problem_route",
    "long_range",
    "ladder",
    "cluster",
    "coupling_crosswalk_module",
    "coupling_magnetosphere_cluster",
    "coupling_fsot_prediction_cross_ratio",
    "coupling_fluidlink_fpc_timing",
    "memory_link",
    "prediction_link",
  ]);

  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = rect.width;
    H = rect.height;
    canvas.width = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
    canvas.style.width = W + "px";
    canvas.style.height = H + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function ringRadius(ring) {
    const r = Number(ring) || 0;
    // wider shells when full atlas so extensions don't crush cores
    const step = isFull ? 95 : 72;
    return (40 + r * step) * ringScale;
  }

  function homeFor(n) {
    const R = ringRadius(n.ring);
    const a = n.angle != null ? n.angle : 0;
    // seeds/law near origin with small fixed constellation
    if (n.kind === "law") return { x: 0, y: 0 };
    if (n.kind === "seed") {
      const i = ["seed_pi", "seed_e", "seed_phi", "seed_gamma", "seed_catalan"].indexOf(n.id);
      const ang = (i >= 0 ? i : 0) * (Math.PI * 2 / 5) - Math.PI / 2;
      return { x: Math.cos(ang) * 28 * ringScale, y: Math.sin(ang) * 28 * ringScale };
    }
    return { x: Math.cos(a) * R, y: Math.sin(a) * R };
  }

  function classifyEdges() {
    structuralEdges = [];
    structuralIds = new Set();
    const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
    for (const e of edges) {
      const k = e.kind || "";
      let take = false;
      if (k === "law_to_domain") {
        const tgt = byId[e.target];
        // only law → core (not every extension) so full graph can solidify
        take = !!(tgt && (tgt.is_core || (tgt.kind === "domain" && tgt.kind !== "extension" && tgt.atlas_kind !== "extension_panel")));
        if (tgt && tgt.kind === "extension") take = false;
      } else if (
        STRUCTURAL_KINDS.has(k) ||
        k.startsWith("coupling_crosswalk") ||
        k.startsWith("coupling_magnetosphere") ||
        k.startsWith("coupling_fsot_prediction") ||
        k.startsWith("coupling_fluidlink") ||
        k === "routes_to_core" ||
        k === "problem_route"
      ) {
        take = true;
      }
      // never structural: dense lean overlap / membership spam
      if (k === "coupling_lean_overlap" || k === "by_core_membership") take = false;
      if (take) structuralEdges.push(e);
    }
    // cap structural springs for stability
    if (structuralEdges.length > 900) {
      structuralEdges = structuralEdges
        .slice()
        .sort((a, b) => (b.strength || 0) - (a.strength || 0))
        .slice(0, 900);
    }
    for (const e of structuralEdges) structuralIds.add(e.id || `${e.source}->${e.target}`);
  }

  function initPositions() {
    const N = nodes.length;
    isFull = N > 80;
    ringScale = isFull ? Math.max(1.15, Math.sqrt(N / 120)) : 1.0;
    temp = 1.0;
    settled = false;
    frame = 0;
    sim = true;

    // Classic D_eff shells. Prefer server angles (already S-ordered on each ring).
    // Only re-space when angle missing — keep seed hub + S organization intact.
    const byRing = {};
    for (const n of nodes) {
      if (n.kind === "seed" || n.kind === "law") continue;
      const r = Number(n.ring) || 0;
      (byRing[r] || (byRing[r] = [])).push(n);
    }
    for (const r of Object.keys(byRing)) {
      const g = byRing[r].slice();
      const needRespace = g.some((n) => n.angle == null);
      if (!needRespace) continue;
      // fallback: same shell look, ordered by signed S (dispersal → emergence)
      g.sort((a, b) => {
        const coreA = a.is_core || a.atlas_kind === "core" ? 0 : 1;
        const coreB = b.is_core || b.atlas_kind === "core" ? 0 : 1;
        if (coreA !== coreB) return coreA - coreB;
        const sa = a.S != null ? Number(a.S) : 0;
        const sb = b.S != null ? Number(b.S) : 0;
        if (sa !== sb) return sa - sb;
        return String(a.domain || a.label || a.id).localeCompare(String(b.domain || b.label || b.id));
      });
      g.forEach((n, i) => {
        n.angle = (2 * Math.PI * i) / Math.max(g.length, 1) + Number(r) * 0.07;
      });
    }

    for (const n of nodes) {
      const h = homeFor(n);
      n.homeX = h.x;
      n.homeY = h.y;
      // tiny jitter only while hot — pattern is the home shell
      const j = isFull ? 4 : 12;
      n.x = h.x + (Math.random() - 0.5) * j;
      n.y = h.y + (Math.random() - 0.5) * j;
      n.vx = 0;
      n.vy = 0;
      // pin strength by role: cores/seeds firmer; extensions softer local wiggle
      if (n.kind === "seed" || n.kind === "law") n.pin = 0.95;
      else if (n.is_core || (n.kind === "domain" && n.atlas_kind !== "extension_panel")) n.pin = 0.72;
      else if (n.kind === "problem_route") n.pin = 0.8;
      else if (n.kind === "extension") n.pin = 0.88; // keep shells clean
      else n.pin = 0.75;
    }
    classifyEdges();
  }

  function stepPhysics() {
    if (!sim || settled) return;
    const N = nodes.length;
    if (!N) return;
    frame++;

    // anneal: hotter early "growth", then solidify
    const coolFrames = isFull ? 220 : 140;
    temp = Math.max(0, 1 - frame / coolFrames);
    if (temp <= 0.02) {
      // snap home and freeze — pattern solidified
      for (const n of nodes) {
        n.x = n.homeX;
        n.y = n.homeY;
        n.vx = 0;
        n.vy = 0;
      }
      settled = true;
      sim = false;
      if ($("hud-status")) {
        const prev = $("hud-status").textContent || "";
        if (!prev.includes("solidified")) {
          $("hud-status").textContent = prev.replace(/ · solidifying…$/, "") + " · pattern solidified";
        }
      }
      return;
    }

    const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
    const T = temp; // scale forces

    // local repulsion only (grid bins) — full O(N^2) thrashes large graphs
    const cell = (isFull ? 55 : 70) * ringScale;
    const grid = new Map();
    for (let i = 0; i < N; i++) {
      const n = nodes[i];
      const cx = Math.floor(n.x / cell);
      const cy = Math.floor(n.y / cell);
      const key = cx + "," + cy;
      if (!grid.has(key)) grid.set(key, []);
      grid.get(key).push(i);
    }
    const repulse = (isFull ? 180 : 420) * T;
    for (let i = 0; i < N; i++) {
      const a = nodes[i];
      const cx = Math.floor(a.x / cell);
      const cy = Math.floor(a.y / cell);
      for (let ox = -1; ox <= 1; ox++) {
        for (let oy = -1; oy <= 1; oy++) {
          const bucket = grid.get((cx + ox) + "," + (cy + oy));
          if (!bucket) continue;
          for (const j of bucket) {
            if (j <= i) continue;
            const b = nodes[j];
            let dx = b.x - a.x, dy = b.y - a.y;
            let d2 = dx * dx + dy * dy + 0.01;
            let d = Math.sqrt(d2);
            const minD = ((a.size || 8) + (b.size || 8)) * 0.7 + (isFull ? 10 : 16);
            if (d < minD * 2.2) {
              const f = repulse / d2;
              const fx = (dx / d) * f, fy = (dy / d) * f;
              a.vx -= fx; a.vy -= fy;
              b.vx += fx; b.vy += fy;
            }
          }
        }
      }
    }

    // structural springs only (not the 2k lean-overlap spaghetti)
    for (const e of structuralEdges) {
      const a = byId[e.source], b = byId[e.target];
      if (!a || !b) continue;
      let dx = b.x - a.x, dy = b.y - a.y;
      let d = Math.sqrt(dx * dx + dy * dy) + 0.01;
      let ideal = 90 * ringScale;
      const knd = e.kind || "";
      if (knd === "seed_to_law") ideal = 36 * ringScale;
      else if (knd === "law_to_domain") ideal = Math.abs(ringRadius(b.ring || 2) - 10);
      else if (knd === "routes_to_core") ideal = 70 * ringScale;
      else if (knd === "long_range") ideal = 160 * ringScale;
      else if (knd === "problem_route") ideal = 55 * ringScale;
      else if (knd.startsWith("coupling_")) ideal = 100 * ringScale;
      const k = (isFull ? 0.006 : 0.014) * (e.strength || 0.5) * T;
      const f = k * (d - ideal);
      const fx = (dx / d) * f, fy = (dy / d) * f;
      a.vx += fx; a.vy += fy;
      b.vx -= fx; b.vy -= fy;
    }

    // HOME PIN — this is what solidifies the multi-scale shell pattern
    for (const n of nodes) {
      const pin = (n.pin || 0.7) * (0.35 + 0.65 * (1 - T)); // stronger as we cool
      n.vx += (n.homeX - n.x) * pin * 0.18;
      n.vy += (n.homeY - n.y) * pin * 0.18;
    }

    // integrate
    const damp = isFull ? 0.78 : 0.82;
    const maxV = 8 * T + 0.4;
    for (const n of nodes) {
      if (drag && drag.mode === "node" && drag.id === n.id) continue;
      n.vx *= damp;
      n.vy *= damp;
      // velocity clamp prevents explosions on dense graphs
      const sp = Math.sqrt(n.vx * n.vx + n.vy * n.vy);
      if (sp > maxV) {
        n.vx = (n.vx / sp) * maxV;
        n.vy = (n.vy / sp) * maxV;
      }
      n.x += n.vx;
      n.y += n.vy;
    }
  }

  function worldToScreen(x, y) {
    return {
      x: W / 2 + cam.x + x * cam.scale,
      y: H / 2 + cam.y + y * cam.scale,
    };
  }

  function screenToWorld(sx, sy) {
    return {
      x: (sx - W / 2 - cam.x) / cam.scale,
      y: (sy - H / 2 - cam.y) / cam.scale,
    };
  }

  function draw() {
    const now = performance.now();
    const t = (now - t0) / 1000;
    ctx.clearRect(0, 0, W, H);

    // faint scale rings
    ctx.save();
    ctx.translate(W / 2 + cam.x, H / 2 + cam.y);
    ctx.scale(cam.scale, cam.scale);
    for (let r = 1; r <= 8; r++) {
      ctx.beginPath();
      ctx.arc(0, 0, ringRadius(r), 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(100, 120, 160, ${0.04 + (r === 1 ? 0.04 : 0)})`;
      ctx.lineWidth = 1 / cam.scale;
      ctx.stroke();
    }
    ctx.restore();

    const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));

    // LOD: zoom densifies lean-overlap + membership mesh
    // cam.scale ~0.4 default full; ≥0.7 early dense; ≥1.2 ultra mesh
    const lodDense = cam.scale >= 0.7;
    const lodUltra = cam.scale >= 1.2;
    const drawEdges = edges.filter((e) => {
      const k = e.kind || "";
      const tier = e.density_tier || (k === "coupling_lean_overlap" || k === "by_core_membership" ? "dense" : "base");
      if (tier === "base") return true;
      if (tier === "dense") return lodDense;
      return lodUltra;
    });

    for (const e of drawEdges) {
      const a = byId[e.source], b = byId[e.target];
      if (!a || !b) continue;
      const sa = worldToScreen(a.x, a.y);
      const sb = worldToScreen(b.x, b.y);
      // skip offscreen for speed
      if ((sa.x < -80 && sb.x < -80) || (sa.x > W + 80 && sb.x > W + 80)) continue;
      if ((sa.y < -80 && sb.y < -80) || (sa.y > H + 80 && sb.y > H + 80)) continue;

      const midX = (sa.x + sb.x) / 2;
      const midY = (sa.y + sb.y) / 2;
      const dx = sb.x - sa.x, dy = sb.y - sa.y;
      const nx = -dy * 0.06, ny = dx * 0.06;
      const knd = e.kind || "";
      const isDense = knd === "coupling_lean_overlap" || knd === "by_core_membership" || e.density_tier === "dense";
      const isStruct = structuralIds.has(e.id || `${e.source}->${e.target}`) || knd === "seed_to_law" || knd === "routes_to_core" || knd === "long_range" || knd === "problem_route";

      ctx.beginPath();
      ctx.moveTo(sa.x, sa.y);
      ctx.quadraticCurveTo(midX + nx, midY + ny, sb.x, sb.y);
      if (knd === "law_to_domain") {
        ctx.strokeStyle = `rgba(196,181,253,${isFull ? 0.06 : 0.12})`;
        ctx.lineWidth = 0.7;
      } else if (isDense) {
        // denser mesh when zoomed — still faint so structure reads
        const a0 = lodUltra ? 0.12 : (lodDense ? 0.08 : 0.04);
        ctx.strokeStyle = `rgba(34,211,238,${settled ? a0 : a0 * 0.7})`;
        ctx.lineWidth = lodUltra ? 0.7 : 0.5;
      } else if (knd === "routes_to_core") {
        ctx.strokeStyle = `rgba(163,230,53,${settled ? 0.45 : 0.3})`;
        ctx.lineWidth = 1.1;
      } else {
        ctx.strokeStyle = e.color || `rgba(103,232,249,${0.25 + 0.25 * (e.strength || 0.5)})`;
        ctx.lineWidth = knd === "long_range" ? 1.6 : 0.9;
      }
      ctx.globalAlpha = 1;
      ctx.stroke();

      // pulses only on structural axons (readable signal, not chaos)
      const pulse = !isDense && e.animated !== false && knd !== "law_to_domain" && (isStruct || knd === "seed_to_law" || knd === "routes_to_core" || knd === "long_range" || knd === "problem_route");
      if (pulse) {
        const phase = (t * (settled ? 0.22 : 0.4) + (e.strength || 0.5) * 1.7) % 1;
        const px = (1 - phase) * (1 - phase) * sa.x + 2 * (1 - phase) * phase * (midX + nx) + phase * phase * sb.x;
        const py = (1 - phase) * (1 - phase) * sa.y + 2 * (1 - phase) * phase * (midY + ny) + phase * phase * sb.y;
        const g = ctx.createRadialGradient(px, py, 0, px, py, settled ? 5 : 7);
        g.addColorStop(0, "rgba(200, 240, 255, 0.95)");
        g.addColorStop(1, "rgba(103, 232, 249, 0)");
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(px, py, settled ? 4.5 : 6, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // nodes = neurons / seeds
    for (const n of nodes) {
      const s = worldToScreen(n.x, n.y);
      const r = Math.max(3, (n.size || 8) * 0.55 * Math.sqrt(cam.scale));
      const isSel = selected && selected.id === n.id;
      const isHov = hover && hover.id === n.id;

      // glow
      const glow = ctx.createRadialGradient(s.x, s.y, 0, s.x, s.y, r * 3.5);
      const col = n.color || "#8892a4";
      glow.addColorStop(0, col + (n.kind === "seed" || n.kind === "law" ? "aa" : "55"));
      glow.addColorStop(1, "transparent");
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(s.x, s.y, r * 3.5, 0, Math.PI * 2);
      ctx.fill();

      ctx.beginPath();
      ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
      ctx.fillStyle = col;
      ctx.fill();
      if (isSel || isHov) {
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 2;
        ctx.stroke();
      } else if (n.regime === "dispersal") {
        ctx.strokeStyle = "rgba(255,100,100,0.5)";
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // labels: seeds/law always; cores when zoomed; extensions only on hover/select
      const showLabel =
        isSel || isHov ||
        n.kind === "seed" || n.kind === "law" ||
        n.kind === "problem_route" ||
        (cam.scale > (isFull ? 1.1 : 0.85) && (n.is_core || n.kind === "domain") && n.kind !== "extension") ||
        (n.is_core && Math.abs(n.S || 0) > 0.45);
      if (showLabel) {
        ctx.font = `${n.kind === "seed" || n.kind === "law" ? 12 : 10}px Segoe UI, system-ui`;
        ctx.fillStyle = "rgba(230,236,244,0.9)";
        ctx.textAlign = "center";
        ctx.fillText(n.label || n.id, s.x, s.y + r + 12);
      }
    }

    // settle progress ring
    if (!settled && temp < 1) {
      ctx.fillStyle = "rgba(167,139,250,0.85)";
      ctx.font = "11px Segoe UI, system-ui";
      ctx.textAlign = "left";
      ctx.fillText(`solidifying pattern… ${Math.round((1 - temp) * 100)}%`, 12, H - 14);
    }
  }

  function loop() {
    stepPhysics();
    draw();
    requestAnimationFrame(loop);
  }

  function pick(sx, sy) {
    const w = screenToWorld(sx, sy);
    let best = null, bestD = 1e9;
    for (const n of nodes) {
      const dx = n.x - w.x, dy = n.y - w.y;
      const d = Math.sqrt(dx * dx + dy * dy);
      const hit = (n.size || 8) * 0.9 + 8 / cam.scale;
      if (d < hit && d < bestD) {
        bestD = d;
        best = n;
      }
    }
    return best;
  }

  canvas.addEventListener("mousedown", (ev) => {
    const rect = canvas.getBoundingClientRect();
    const sx = ev.clientX - rect.left, sy = ev.clientY - rect.top;
    const n = pick(sx, sy);
    if (n) {
      selected = n;
      renderSelection(n);
      drag = { mode: "node", id: n.id, ox: sx, oy: sy, nx: n.x, ny: n.y };
    } else {
      drag = { mode: "pan", ox: sx, oy: sy, cx: cam.x, cy: cam.y };
    }
  });
  window.addEventListener("mousemove", (ev) => {
    const rect = canvas.getBoundingClientRect();
    const sx = ev.clientX - rect.left, sy = ev.clientY - rect.top;
    if (!drag) {
      hover = pick(sx, sy);
      return;
    }
    if (drag.mode === "pan") {
      cam.x = drag.cx + (sx - drag.ox);
      cam.y = drag.cy + (sy - drag.oy);
    } else if (drag.mode === "node") {
      const n = nodes.find((x) => x.id === drag.id);
      if (n) {
        const w = screenToWorld(sx, sy);
        n.x = w.x; n.y = w.y; n.vx = 0; n.vy = 0;
        // dragging updates home so pattern re-solidifies around user move
        n.homeX = w.x; n.homeY = w.y;
        if (settled) { sim = true; settled = false; temp = 0.25; frame = Math.floor(0.75 * (isFull ? 220 : 140)); }
      }
    }
  });
  window.addEventListener("mouseup", () => { drag = null; });
  canvas.addEventListener("wheel", (ev) => {
    ev.preventDefault();
    const factor = ev.deltaY > 0 ? 0.92 : 1.08;
    cam.scale = Math.min(3.5, Math.max(0.25, cam.scale * factor));
  }, { passive: false });

  function simpleMarkdown(md) {
    // Lightweight thesis renderer — keep regexes simple (must not break the graph script).
    const lines = String(md || "").split(/\r?\n/);
    const out = [];
    let inTable = false;
    let tableRows = [];

    function flushTable() {
      if (!tableRows.length) return;
      let html = "<table>";
      let headerDone = false;
      for (const row of tableRows) {
        if (/^\s*\|?[\s:-]+\|/.test(row)) continue; // alignment row
        const cells = row.replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());
        if (!cells.length) continue;
        const tag = headerDone ? "td" : "th";
        html += "<tr>" + cells.map((c) => `<${tag}>${inlineFmt(c)}</${tag}>`).join("") + "</tr>";
        headerDone = true;
      }
      html += "</table>";
      out.push(html);
      tableRows = [];
      inTable = false;
    }

    function inlineFmt(s) {
      return esc(s)
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/`([^`]+)`/g, "<code>$1</code>");
    }

    for (const line of lines) {
      if (line.trim().startsWith("|")) {
        inTable = true;
        tableRows.push(line);
        continue;
      }
      if (inTable) flushTable();

      if (/^### /.test(line)) out.push("<h3>" + inlineFmt(line.slice(4)) + "</h3>");
      else if (/^## /.test(line)) out.push("<h2>" + inlineFmt(line.slice(3)) + "</h2>");
      else if (/^# /.test(line)) out.push("<h1>" + inlineFmt(line.slice(2)) + "</h1>");
      else if (/^> /.test(line)) out.push("<blockquote>" + inlineFmt(line.slice(2)) + "</blockquote>");
      else if (/^---+$/.test(line.trim())) out.push("<hr/>");
      else if (line.trim() === "") out.push("");
      else out.push("<p>" + inlineFmt(line) + "</p>");
    }
    if (inTable) flushTable();
    return out.join("\n");
  }

  async function loadThesis(nodeId) {
    const el = $("thesis-out");
    if (!el) return;
    if (!nodeId) {
      el.className = "panel scroll empty thesis";
      el.textContent = "Select a node, then open its research markdown";
      return;
    }
    el.className = "panel scroll thesis";
    el.textContent = "loading scientific tissue thesis…";
    try {
      // Prefer query form — more reliable than path segments across servers
      const r = await api("/api/tissue?id=" + encodeURIComponent(nodeId));
      if (!r.ok) {
        el.innerHTML = `<div class="chip pink">no thesis yet for <code>${esc(nodeId)}</code></div>
          <div>${esc(r.error || "not_found")}</div>
          <div>Run <code>python -m fsot_mc tissue-docs</code> then restart <code>python -m fsot_mc serve</code>.</div>`;
        return;
      }
      el.innerHTML = `<div class="chip gold">${esc(r.path || "")}</div>` + simpleMarkdown(r.markdown || "");
    } catch (e) {
      el.textContent = "error: " + e.message;
    }
  }

  function renderSelection(n) {
    const el = $("sel-out");
    if (!n) {
      el.className = "panel scroll empty";
      el.textContent = "Click a seed, fold, memory, or prediction";
      return;
    }
    el.className = "panel scroll";
    // auto-load thesis on select
    loadThesis(n.id);
    const rows = [
      `<div class="answer-block"><span class="label">Node</span><div><strong>${esc(n.label)}</strong> <span class="chip">${esc(n.kind)}</span></div></div>`,
      n.domain ? `<div>Domain: <code>${esc(n.domain)}</code></div>` : "",
      n.cluster ? `<div>Cluster: <span class="chip">${esc(n.cluster)}</span></div>` : "",
      n.D_eff != null ? `<div>D<sub>eff</sub> = ${n.D_eff} · ring ${n.ring}</div>` : "",
      n.S != null ? `<div>S = ${Number(n.S).toFixed(4)} · ${esc(n.regime || "")} <span style="opacity:.65">(canonical)</span></div>` : "",
      n.S_path_mean != null ? `<div>S<sub>path</sub> = ${Number(n.S_path_mean).toFixed(4)} <span style="opacity:.65">(multipath)</span></div>` : "",
      n.median_error_pct != null ? `<div class="chip gold">median_error ${Number(n.median_error_pct).toFixed(4)}% ${Number(n.median_error_pct) <= 0.5 ? "✓ green" : ""}</div>` : "",
      n.coverage_tier ? `<div>coverage: ${esc(n.coverage_tier)}</div>` : "",
      n.record_count != null ? `<div>records: ${n.record_count}</div>` : "",
      n.routes_to_core ? `<div>routes_to_core → <code>${esc(n.routes_to_core)}</code></div>` : "",
      n.lean_module ? `<div class="chip">Lean: ${esc(n.lean_module)}</div>` : "",
      (n.maps_to_lean && n.maps_to_lean.length) ? `<div>maps_to_lean: ${esc((n.maps_to_lean || []).join(", "))}</div>` : "",
      n.value != null ? `<div>value = ${n.value}</div>` : "",
      n.role ? `<div class="muted">${esc(n.role)}</div>` : "",
      n.formula ? `<div><code>${esc(n.formula)}</code></div>` : "",
      n.full_text ? `<div style="margin-top:0.4rem">${esc(n.full_text)}</div>` : "",
      n.name ? `<div>${esc(n.name)}</div>` : "",
      n.fsot_predicted != null ? `<div class="chip gold">FSOT ${n.fsot_predicted} ${esc(n.unit || "")}</div>` : "",
      n.flip_rate != null ? `<div>flip_rate = ${n.flip_rate}</div>` : "",
      n.is_core ? `<div class="chip pink">core NeuroLab fold</div>` : "",
      n.kind === "extension" ? `<div class="chip">extension panel</div>` : "",
      n.kind === "problem_route" ? `<div class="chip pink">problem route intent</div>` : "",
    ].filter(Boolean);
    el.innerHTML = rows.join("");
  }

  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[c]);
  }

  async function api(path, opts) {
    const r = await fetch(path, opts);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }

  async function loadGraph(opts = {}) {
    const scope = ($("scope-select") && $("scope-select").value) || "full";
    const rebuild = opts.rebuild ? "&rebuild=1" : "";
    $("hud-status").textContent = scope === "full"
      ? "loading full archive connective tissue…"
      : "building core multipath graph…";
    try {
      const g = await api(`/api/graph?n_paths=32&seed=0&scope=${encodeURIComponent(scope)}${rebuild}`);
      nodes = g.nodes || [];
      edges = g.edges || [];
      meta = g.meta || {};
      initPositions();
      cam = { x: 0, y: 0, scale: scope === "full" ? 0.42 : 0.85 };
      $("hud-nodes").innerHTML = `nodes <strong>${g.n_nodes}</strong>`;
      $("hud-edges").innerHTML = `axons <strong>${g.n_edges}</strong>`;
      const ef = meta.map_emergence_mean;
      $("hud-emerge").innerHTML = ef != null
        ? `map emerge <strong>${(100 * ef).toFixed(1)}%</strong>`
        : "map emerge —";
      const ac = meta.archive_connective || {};
      const green = ac.n_green_gate != null ? ` · green ${ac.n_green_gate}/${ac.n_with_error || "?"}≤0.5%` : "";
      const raw = ac.coupling_raw_edge_count != null
        ? ` · archive raw couples ${ac.coupling_raw_edge_count}`
        : "";
      $("hud-status").textContent =
        `${scope} · core ${meta.n_core_folds || "—"} · ext ${meta.n_extension_panels || 0}${green}${raw} · solidifying…`;
      renderLegend(g);
      renderRings(meta);
      // show archive connective summary in side panel
      if (ac && Object.keys(ac).length) {
        $("side-out").innerHTML = `
          <div class="answer-block"><span class="label">Archive connective tissue</span>
          <div>nodes ${ac.n_archive_nodes} · edges ${ac.n_archive_edges}</div>
          <div>core ${ac.n_core} · extension ${ac.n_extension} · intents ${ac.n_problem_routes}</div>
          <div class="chip gold">green gate ${ac.n_green_gate}/${ac.n_with_error}</div>
          <div class="chip">raw coupling ${ac.coupling_raw_edge_count} edges / ${ac.coupling_raw_node_count} nodes</div>
          <pre>${esc(JSON.stringify(ac.edge_type_counts || {}, null, 0))}</pre>
          <div style="font-size:0.7rem;color:#8b95a8">Synced from Physical Archive domain coupling + navigator + expansion map</div>
          </div>`;
      }
      loadMemory();
    } catch (e) {
      $("hud-status").textContent = "error: " + e.message;
    }
  }

  function renderLegend(g) {
    const ul = $("legend-list");
    const items = (g.meta && g.meta.legend) || [];
    const colors = (g.meta && g.meta.cluster_colors) || {};
    ul.innerHTML = items.map((t) => `<li><span class="swatch" style="background:${colors.seed || '#fff'};color:${colors.seed || '#fff'}"></span>${esc(t)}</li>`).join("");
    // cluster swatches
    const clusters = Object.keys(colors).filter((k) => !["seed", "law", "memory", "prediction", "bridge"].includes(k));
    ul.innerHTML += clusters.map((c) =>
      `<li><span class="swatch" style="background:${colors[c]};color:${colors[c]}"></span>${esc(c)}</li>`
    ).join("");
  }

  function renderRings(m) {
    const el = $("rings-out");
    const rings = (m && m.rings) || {};
    el.innerHTML = Object.entries(rings).map(([k, v]) =>
      `<div><span class="chip">${esc(k)}</span> ${esc(v)}</div>`
    ).join("") || "—";
  }

  async function loadMemory() {
    try {
      const m = await api("/api/memory");
      const s = m.summary || {};
      $("mem-out").innerHTML = `
        <div>STM ${s.stm_size}/${s.stm_capacity} · LTM ${s.ltm_size} · solid <strong>${s.n_solidified}</strong></div>
        <div class="chip">${esc(s.doctrine || "")}</div>
      `;
    } catch (_) {
      $("mem-out").textContent = "memory offline";
    }
  }

  $("btn-reload").onclick = () => loadGraph();
  if ($("btn-rebuild")) $("btn-rebuild").onclick = () => loadGraph({ rebuild: true });
  if ($("scope-select")) $("scope-select").onchange = () => loadGraph();
  if ($("btn-thesis")) {
    $("btn-thesis").onclick = () => {
      if (selected) loadThesis(selected.id);
      else if ($("thesis-out")) {
        $("thesis-out").className = "panel scroll empty thesis";
        $("thesis-out").textContent = "Click a node first";
      }
    };
  }
  const chatHistory = []; // {role, content} for multi-turn
  const CHAT_SESSION = "ui";

  function appendChat(role, text, meta) {
    const log = $("chat-log");
    if (!log) return;
    const div = document.createElement("div");
    div.className = "answer-block";
    div.style.marginBottom = "0.55rem";
    const label = role === "user" ? "You" : "Qwen · docs";
    const color = role === "user" ? "chip" : "chip gold";
    let metaHtml = "";
    if (meta && meta.docs && meta.docs.length) {
      metaHtml = `<div style="font-size:0.7rem;opacity:0.75;margin-top:0.25rem">Read: ${meta.docs.map((d) => esc(d)).join(" · ")}</div>`;
    }
    div.innerHTML = `<span class="${color}">${label}</span>
      <div style="white-space:pre-wrap;margin-top:0.25rem">${esc(text)}</div>${metaHtml}`;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
  }

  async function refreshQwenStatus() {
    const el = $("qwen-status");
    if (!el) return;
    try {
      const h = await api("/api/health");
      const q = (h && h.qwen) || {};
      if (q.ready) {
        el.className = "chip gold";
        el.textContent = "Qwen: ready · reads tissue + docs (conversation)";
      } else {
        el.className = "chip pink";
        el.textContent = "Qwen: weights missing — run download_qwen25_instruct.py";
      }
    } catch (_) {
      el.textContent = "Qwen: status offline";
    }
  }

  async function runDocChat(message) {
    const log = $("chat-log");
    if (log && !log.dataset.booted) {
      log.dataset.booted = "1";
      log.innerHTML = "";
      appendChat(
        "assistant",
        "I can discuss this project's documentation: every domain tissue thesis, methodology, claims, PREDs, audit notes. Ask me anything about the work.",
        null
      );
    }
    appendChat("user", message, null);
    const thinking = document.createElement("div");
    thinking.className = "answer-block";
    thinking.id = "chat-thinking";
    thinking.innerHTML = `<span class="chip pink">reading docs…</span> <span style="opacity:0.8">retrieving theses & generating reply (can take 20–60s)</span>`;
    if (log) {
      log.appendChild(thinking);
      log.scrollTop = log.scrollHeight;
    }

    const body = {
      mode: "chat",
      query: message,
      message,
      session_id: CHAT_SESSION,
      history: chatHistory.slice(-12),
      max_tokens: 450,
    };
    try {
      const r = await api("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const th = $("chat-thinking");
      if (th) th.remove();
      if (!r.ok && r.error) {
        appendChat("assistant", `Error: ${r.error}${r.detail ? " — " + r.detail : ""}${r.hint ? " (" + r.hint + ")" : ""}`, null);
        return r;
      }
      const reply = r.reply || r.answer || "(empty reply)";
      chatHistory.push({ role: "user", content: message });
      chatHistory.push({ role: "assistant", content: reply });
      const docs = (r.docs_used || []).map((d) => d.path || d.title || "").filter(Boolean).slice(0, 6);
      appendChat("assistant", reply, { docs });
      if ($("ask-out")) {
        $("ask-out").style.display = "none";
      }
      return r;
    } catch (e) {
      const th = $("chat-thinking");
      if (th) th.remove();
      appendChat("assistant", "Request failed: " + e.message + " (wait for Qwen warm; reply can take up to a minute)", null);
      throw e;
    }
  }

  $("btn-ask").onclick = async () => {
    const q = $("ask-input").value.trim();
    if (!q) return;
    $("ask-input").value = "";
    try {
      await runDocChat(q);
    } catch (_) { /* shown in chat */ }
  };

  if ($("btn-chat-clear")) {
    $("btn-chat-clear").onclick = async () => {
      chatHistory.length = 0;
      try {
        await api("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ clear: true, session_id: CHAT_SESSION }),
        });
      } catch (_) {}
      const log = $("chat-log");
      if (log) {
        log.innerHTML = "";
        log.dataset.booted = "";
      }
      appendChat("assistant", "Chat cleared. Ask about any tissue thesis, claim, or report.", null);
    };
  }

  // Enter to send (Shift+Enter newline)
  if ($("ask-input")) {
    $("ask-input").addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" && !ev.shiftKey) {
        ev.preventDefault();
        $("btn-ask").click();
      }
    });
  }

  if ($("btn-explain")) {
    $("btn-explain").onclick = async () => {
      if (!selected) {
        appendChat("assistant", "Select a graph node first, then ask me about it.", null);
        return;
      }
      const dom = selected.domain || selected.label || selected.id;
      const q = `Using the tissue thesis and live scalars, explain the FSOT node "${dom}" to me in clear conversation. What is S, D_eff, regime, and why does it matter in this project?`;
      if ($("ask-input")) $("ask-input").value = "";
      try {
        await runDocChat(q);
      } catch (_) {}
    };
  }

  refreshQwenStatus();
  // index docs on load (async, non-blocking)
  api("/api/docs/index?rebuild=0").catch(() => {});

  $("btn-readings").onclick = async () => {
    $("side-out").textContent = "loading accuracy…";
    try {
      const r = await api("/api/readings?n_paths=24");
      const h = r.headline || {};
      const a = r.archive_margin_audit || {};
      const c = r.contested_panel || {};
      $("side-out").innerHTML = `
        <div class="chip gold">integrity ${esc(r.integrity_score)}</div>
        <div>Green gate: ${esc(h.archive_domains_green)}</div>
        <div>Pooled median-of-medians: ${a.pooled_median_of_domain_medians_pct}%</div>
        <div>Contested FSOT: ${c.fsot_pooled_median_error_pct}% vs baseline ${c.current_model_baseline_pct}%</div>
        <div>Map emerge: ${((r.multipath_exploratory || {}).map_emergence_mean * 100 || 0).toFixed?.(1) ?? "—"}%</div>
        <pre>${esc(h.paradigm || "")}</pre>
      `;
    } catch (e) {
      $("side-out").textContent = e.message;
    }
  };

  $("btn-solidify").onclick = async () => {
    $("side-out").textContent = "solidifying chew corpus into LTM…";
    try {
      const r = await api("/api/solidify?n_paths=12");
      const s = r.memory_summary || {};
      $("side-out").innerHTML = `
        <div class="chip pink">topics ${r.n_topics}</div>
        <div>LTM ${s.ltm_size} · solidified ${s.n_solidified}</div>
        <div>${esc(r.note || "")}</div>
      `;
      loadMemory();
      loadGraph();
    } catch (e) {
      $("side-out").textContent = e.message;
    }
  };

  $("btn-protocols").onclick = async () => {
    $("side-out").textContent = "loading protocols…";
    try {
      const r = await api("/api/protocols?limit=8");
      $("side-out").innerHTML = (r.cards || []).map((c) => `
        <div class="answer-block" style="margin-bottom:0.6rem">
          <span class="label">${esc(c.id)}</span>
          <div><strong>${esc(c.title)}</strong></div>
          <div class="chip gold">${esc(String(c.fsot_predicted))} ${esc(c.unit || "")}</div>
          <div style="font-size:0.72rem;color:#8b95a8">${esc(c.discriminant || "")}</div>
          <div style="font-size:0.72rem">kill: ${esc((c.kill_criteria || [])[0] || "")}</div>
        </div>
      `).join("") || "no cards";
    } catch (e) {
      $("side-out").textContent = e.message;
    }
  };

  window.addEventListener("resize", resize);
  resize();
  loadGraph();
  loop();
})();
