/**
 * FSOT connective visual — Obsidian graph × neural growth.
 * Force-directed layout with ring bias by D_eff; axon pulse animation.
 */
(() => {
  const canvas = document.getElementById("graph");
  const ctx = canvas.getContext("2d");
  const $ = (id) => document.getElementById(id);

  let W = 0, H = 0, dpr = 1;
  let nodes = [];
  let edges = [];
  let meta = {};
  let selected = null;
  let hover = null;
  let sim = true;
  let t0 = performance.now();

  // camera
  let cam = { x: 0, y: 0, scale: 1 };
  let drag = null; // { mode: 'pan'|'node', id, ox, oy, nx, ny }

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
    return 40 + r * 72;
  }

  function initPositions() {
    const cx = 0, cy = 0;
    for (const n of nodes) {
      const R = ringRadius(n.ring);
      const a = n.angle != null ? n.angle : Math.random() * Math.PI * 2;
      // slight noise so force can settle
      n.x = cx + Math.cos(a) * R + (Math.random() - 0.5) * 20;
      n.y = cy + Math.sin(a) * R + (Math.random() - 0.5) * 20;
      n.vx = 0;
      n.vy = 0;
    }
  }

  function stepPhysics() {
    if (!sim) return;
    const N = nodes.length;
    if (!N) return;
    const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));

    // repulsion
    for (let i = 0; i < N; i++) {
      for (let j = i + 1; j < N; j++) {
        const a = nodes[i], b = nodes[j];
        let dx = b.x - a.x, dy = b.y - a.y;
        let d2 = dx * dx + dy * dy + 0.01;
        let d = Math.sqrt(d2);
        const minD = (a.size || 8) + (b.size || 8) + 18;
        if (d < minD * 3) {
          const f = 420 / d2;
          const fx = (dx / d) * f, fy = (dy / d) * f;
          a.vx -= fx; a.vy -= fy;
          b.vx += fx; b.vy += fy;
        }
      }
    }

    // springs
    for (const e of edges) {
      const a = byId[e.source], b = byId[e.target];
      if (!a || !b) continue;
      let dx = b.x - a.x, dy = b.y - a.y;
      let d = Math.sqrt(dx * dx + dy * dy) + 0.01;
      const ideal = e.kind === "law_to_domain" ? 160 : e.kind === "long_range" ? 220 : 90;
      const k = 0.012 * (e.strength || 0.5);
      const f = k * (d - ideal);
      const fx = (dx / d) * f, fy = (dy / d) * f;
      a.vx += fx; a.vy += fy;
      b.vx -= fx; b.vy -= fy;
    }

    // ring gravity (neural shells by D_eff)
    for (const n of nodes) {
      const R = ringRadius(n.ring);
      const dist = Math.sqrt(n.x * n.x + n.y * n.y) + 0.01;
      const pull = 0.02 * (R - dist);
      n.vx += (n.x / dist) * pull;
      n.vy += (n.y / dist) * pull;
      // center seed/law slightly
      if (n.kind === "seed" || n.kind === "law") {
        n.vx -= n.x * 0.04;
        n.vy -= n.y * 0.04;
      }
    }

    // integrate
    for (const n of nodes) {
      if (drag && drag.mode === "node" && drag.id === n.id) continue;
      n.vx *= 0.82;
      n.vy *= 0.82;
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

    // edges = neural axons
    for (const e of edges) {
      const a = byId[e.source], b = byId[e.target];
      if (!a || !b) continue;
      const sa = worldToScreen(a.x, a.y);
      const sb = worldToScreen(b.x, b.y);
      const midX = (sa.x + sb.x) / 2;
      const midY = (sa.y + sb.y) / 2;
      // slight curve
      const dx = sb.x - sa.x, dy = sb.y - sa.y;
      const nx = -dy * 0.08, ny = dx * 0.08;

      ctx.beginPath();
      ctx.moveTo(sa.x, sa.y);
      ctx.quadraticCurveTo(midX + nx, midY + ny, sb.x, sb.y);
      const alpha = e.kind === "law_to_domain" ? 0.12 : 0.35 + 0.25 * (e.strength || 0.5);
      ctx.strokeStyle = e.color || `rgba(103,232,249,${alpha})`;
      if (e.kind === "law_to_domain") {
        ctx.strokeStyle = `rgba(196,181,253,${0.08 + 0.1 * (e.strength || 0.2)})`;
      }
      ctx.lineWidth = e.kind === "long_range" ? 1.8 : e.kind === "ladder" ? 1.2 : 0.9;
      ctx.globalAlpha = 1;
      ctx.stroke();

      // pulse along axon (neural growth vibe)
      if (e.animated !== false && e.kind !== "law_to_domain") {
        const phase = (t * 0.35 + (e.strength || 0.5)) % 1;
        const px = (1 - phase) * (1 - phase) * sa.x + 2 * (1 - phase) * phase * (midX + nx) + phase * phase * sb.x;
        const py = (1 - phase) * (1 - phase) * sa.y + 2 * (1 - phase) * phase * (midY + ny) + phase * phase * sb.y;
        const g = ctx.createRadialGradient(px, py, 0, px, py, 6);
        g.addColorStop(0, "rgba(200, 240, 255, 0.95)");
        g.addColorStop(1, "rgba(103, 232, 249, 0)");
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(px, py, 6, 0, Math.PI * 2);
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

      // labels for important / selected / zoomed
      const showLabel =
        isSel || isHov ||
        n.kind === "seed" || n.kind === "law" ||
        (cam.scale > 0.85 && (n.kind === "domain" || n.kind === "prediction")) ||
        (n.kind === "domain" && Math.abs(n.S || 0) > 0.5);
      if (showLabel) {
        ctx.font = `${n.kind === "seed" || n.kind === "law" ? 12 : 10}px Segoe UI, system-ui`;
        ctx.fillStyle = "rgba(230,236,244,0.9)";
        ctx.textAlign = "center";
        ctx.fillText(n.label || n.id, s.x, s.y + r + 12);
      }
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
      }
    }
  });
  window.addEventListener("mouseup", () => { drag = null; });
  canvas.addEventListener("wheel", (ev) => {
    ev.preventDefault();
    const factor = ev.deltaY > 0 ? 0.92 : 1.08;
    cam.scale = Math.min(3.5, Math.max(0.25, cam.scale * factor));
  }, { passive: false });

  function renderSelection(n) {
    const el = $("sel-out");
    if (!n) {
      el.className = "panel scroll empty";
      el.textContent = "Click a seed, fold, memory, or prediction";
      return;
    }
    el.className = "panel scroll";
    const rows = [
      `<div class="answer-block"><span class="label">Node</span><div><strong>${esc(n.label)}</strong> <span class="chip">${esc(n.kind)}</span></div></div>`,
      n.domain ? `<div>Domain: <code>${esc(n.domain)}</code></div>` : "",
      n.cluster ? `<div>Cluster: <span class="chip">${esc(n.cluster)}</span></div>` : "",
      n.D_eff != null ? `<div>D<sub>eff</sub> = ${n.D_eff} · ring ${n.ring}</div>` : "",
      n.S != null ? `<div>S = ${Number(n.S).toFixed(4)} · ${esc(n.regime || "")}</div>` : "",
      n.value != null ? `<div>value = ${n.value}</div>` : "",
      n.role ? `<div class="muted">${esc(n.role)}</div>` : "",
      n.formula ? `<div><code>${esc(n.formula)}</code></div>` : "",
      n.full_text ? `<div style="margin-top:0.4rem">${esc(n.full_text)}</div>` : "",
      n.name ? `<div>${esc(n.name)}</div>` : "",
      n.fsot_predicted != null ? `<div class="chip gold">FSOT ${n.fsot_predicted} ${esc(n.unit || "")}</div>` : "",
      n.flip_rate != null ? `<div>flip_rate = ${n.flip_rate}</div>` : "",
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

  async function loadGraph() {
    $("hud-status").textContent = "building multipath graph…";
    try {
      const g = await api("/api/graph?n_paths=40&seed=0");
      nodes = g.nodes || [];
      edges = g.edges || [];
      meta = g.meta || {};
      initPositions();
      cam = { x: 0, y: 0, scale: 0.85 };
      $("hud-nodes").innerHTML = `nodes <strong>${g.n_nodes}</strong>`;
      $("hud-edges").innerHTML = `axons <strong>${g.n_edges}</strong>`;
      const ef = meta.map_emergence_mean;
      $("hud-emerge").innerHTML = ef != null
        ? `map emerge <strong>${(100 * ef).toFixed(1)}%</strong>`
        : "map emerge —";
      $("hud-status").textContent = "live · seeds→K→folds→bridges";
      renderLegend(g);
      renderRings(meta);
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
  $("btn-ask").onclick = async () => {
    const q = $("ask-input").value.trim();
    if (!q) return;
    $("ask-out").textContent = "thinking (multipath)…";
    try {
      const r = await api("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: q,
          n_paths: 28,
          chew: $("ask-chew").checked ? true : null,
        }),
      });
      const th = r.thinking || {};
      const domains = (th.routed_domains || []).map((d) => `<span class="chip">${esc(d)}</span>`).join(" ");
      $("ask-out").innerHTML = `
        <div class="answer-block"><span class="label">Answer</span>
        <div>${esc((r.answer || "").slice(0, 1200))}${(r.answer || "").length > 1200 ? "…" : ""}</div></div>
        <div class="answer-block"><span class="label">Folds</span><div>${domains}</div></div>
        <div class="chip pink">paths ${th.n_paths || "—"}</div>
      `;
      loadMemory();
    } catch (e) {
      $("ask-out").textContent = "error: " + e.message;
    }
  };

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
