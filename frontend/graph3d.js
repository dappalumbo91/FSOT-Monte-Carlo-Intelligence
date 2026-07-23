/**
 * FSOT 3D graph — cosmological expansion shells (As Above So Below).
 *
 * Layout (frozen server doctrine — not 2D force soup):
 *   radius  ∝ D_eff ring  → expansion distance from origin
 *   angle   = physics pie sector (same longitude across scales)
 *   height  ∝ D_eff       → dimensional ladder
 *   color   = physics spine hue
 *
 * Communication axons (structural edges) stay bright; dense mesh only when zoomed.
 */
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

function parseColor(hex, fallback = 0x8892a4) {
  if (!hex || typeof hex !== "string") return fallback;
  const h = hex.replace("#", "").trim();
  if (h.length === 6) return parseInt(h, 16);
  if (h.length === 3) {
    const e = h
      .split("")
      .map((c) => c + c)
      .join("");
    return parseInt(e, 16);
  }
  return fallback;
}

function ringRadius(ring, isFull) {
  const r = Number(ring) || 0;
  const step = isFull ? 88 : 70;
  return 36 + r * step;
}

/** Pure polar layout — ignore 2D anneal homes (those caused chaos). */
function nodeWorldPos(n, isFull, scale = 0.048) {
  if (n.kind === "law") return new THREE.Vector3(0, 0, 0);
  if (n.kind === "seed") {
    const ids = ["seed_pi", "seed_e", "seed_phi", "seed_gamma", "seed_catalan"];
    const i = Math.max(0, ids.indexOf(n.id));
    const ang = (i * Math.PI * 2) / 5 - Math.PI / 2;
    const R = 22 * scale * 16;
    return new THREE.Vector3(Math.cos(ang) * R, 2, Math.sin(ang) * R);
  }
  const a = n.angle != null ? Number(n.angle) : 0;
  const d = Number(n.D_eff != null ? n.D_eff : n.ring != null ? Number(n.ring) * 4 : 12);
  // Expansion cone: outer shells + higher D_eff push outward (Big Bang / Hubble layer feel)
  const expand = 0.75 + 0.55 * Math.min(1, Math.max(0, d / 25));
  const R = ringRadius(n.ring, isFull) * scale * expand;
  // Height ladder: micro near mid-plane slightly down, macro up
  const y = ((d - 8) / 20) * 70;
  return new THREE.Vector3(Math.cos(a) * R, y, Math.sin(a) * R);
}

const STRUCT_KINDS = new Set([
  "seed_to_law",
  "law_to_domain",
  "routes_to_core",
  "long_range",
  "ladder",
  "problem_route",
  "cluster",
  "prediction_link",
  "memory_link",
  "coupling_crosswalk_module",
  "coupling_magnetosphere_cluster",
  "coupling_fsot_prediction_cross_ratio",
  "coupling_fluidlink_fpc_timing",
]);

function isStructuralEdge(e) {
  const k = e.kind || "";
  if (STRUCT_KINDS.has(k)) return true;
  if (k.startsWith("coupling_crosswalk")) return true;
  if (k.startsWith("coupling_magnetosphere")) return true;
  if (k.startsWith("coupling_fsot_prediction")) return true;
  if (k.startsWith("coupling_fluidlink")) return true;
  return false;
}

function isDenseMesh(e) {
  const k = e.kind || "";
  return (
    k === "coupling_lean_overlap" ||
    k === "by_core_membership" ||
    e.density_tier === "dense"
  );
}

function edgeAllowed(e, lodDense, lodUltra) {
  if (isDenseMesh(e)) return lodUltra; // only ultra-close shows soup
  if (isStructuralEdge(e)) return true;
  // other base edges when somewhat close
  return lodDense || lodUltra;
}

/**
 * @param {HTMLElement} container
 * @param {{ onSelect?: (n: object|null) => void }} opts
 */
export function createGraph3D(container, opts = {}) {
  const onSelect = opts.onSelect || (() => {});

  let width = 1;
  let height = 1;
  let nodes = [];
  let edges = [];
  let isFull = false;
  let selectedId = null;
  let visible = false;
  let disposed = false;
  let lodDense = false;
  let lodUltra = false;
  let pulseT = 0;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a0c14);
  // lighter fog so structure stays readable
  scene.fog = new THREE.FogExp2(0x0a0c14, 0.0028);

  const camera = new THREE.PerspectiveCamera(48, 1, 0.5, 5000);
  camera.position.set(0, 70, 150);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(1, 1);
  renderer.domElement.style.width = "100%";
  renderer.domElement.style.height = "100%";
  renderer.domElement.style.display = "block";
  renderer.domElement.style.cursor = "grab";
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.07;
  controls.minDistance = 18;
  controls.maxDistance = 480;
  controls.target.set(0, 10, 0);

  // brighter key lighting
  scene.add(new THREE.AmbientLight(0xd0d8e8, 0.72));
  const key = new THREE.DirectionalLight(0xffffff, 1.05);
  key.position.set(50, 90, 40);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xaaccff, 0.4);
  fill.position.set(-60, 30, -50);
  scene.add(fill);
  const rim = new THREE.PointLight(0xc4b5fd, 0.55, 400);
  rim.position.set(0, 20, 0);
  scene.add(rim);

  let shellGroup = new THREE.Group();
  let edgeGroup = new THREE.Group();
  let nodeGroup = new THREE.Group();
  let pulseGroup = new THREE.Group();
  scene.add(shellGroup);
  scene.add(edgeGroup);
  scene.add(nodeGroup);
  scene.add(pulseGroup);

  const nodeMeshes = new Map();
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let labelEl = null;
  let structSegments = []; // for pulse animation [{pa,pb,kind}]

  function ensureLabel() {
    if (labelEl) return labelEl;
    labelEl = document.createElement("div");
    labelEl.className = "graph3d-label";
    labelEl.style.cssText =
      "position:absolute;pointer-events:none;padding:0.25rem 0.5rem;border-radius:6px;" +
      "background:rgba(10,14,22,0.9);border:1px solid rgba(140,160,200,0.35);" +
      "font-size:0.72rem;color:#eef2fa;display:none;z-index:5;white-space:nowrap;" +
      "box-shadow:0 0 12px rgba(103,232,249,0.15);";
    container.style.position = container.style.position || "relative";
    container.appendChild(labelEl);
    return labelEl;
  }

  function clearGroup(g) {
    while (g.children.length) {
      const c = g.children.pop();
      if (c.geometry) c.geometry.dispose();
      if (c.material) {
        if (Array.isArray(c.material)) c.material.forEach((m) => m.dispose());
        else c.material.dispose();
      }
    }
  }

  function buildShells() {
    clearGroup(shellGroup);
    for (let r = 1; r <= 8; r++) {
      const R = ringRadius(r, isFull) * 0.048 * (0.75 + 0.08 * r);
      // translucent disk (expansion shell)
      const disk = new THREE.Mesh(
        new THREE.CircleGeometry(R, 64),
        new THREE.MeshBasicMaterial({
          color: 0x4a5a80,
          transparent: true,
          opacity: 0.045 + r * 0.008,
          side: THREE.DoubleSide,
          depthWrite: false,
        })
      );
      disk.rotation.x = -Math.PI / 2;
      const dMid = (r - 1) * 4 + 4;
      disk.position.y = ((dMid - 8) / 20) * 70;
      shellGroup.add(disk);

      // bright rim
      const rimGeo = new THREE.RingGeometry(R * 0.985, R * 1.015, 96);
      rimGeo.rotateX(-Math.PI / 2);
      const rimMesh = new THREE.Mesh(
        rimGeo,
        new THREE.MeshBasicMaterial({
          color: 0x89a0d0,
          transparent: true,
          opacity: 0.22 + (r === 1 ? 0.1 : 0),
          side: THREE.DoubleSide,
          depthWrite: false,
        })
      );
      rimMesh.position.y = disk.position.y;
      shellGroup.add(rimMesh);
    }
    // origin glow (singularity / law hub)
    const coreGlow = new THREE.Mesh(
      new THREE.SphereGeometry(3.2, 24, 18),
      new THREE.MeshBasicMaterial({
        color: 0xc4b5fd,
        transparent: true,
        opacity: 0.25,
        depthWrite: false,
      })
    );
    shellGroup.add(coreGlow);

    // vertical expansion axis
    const axisGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, -40, 0),
      new THREE.Vector3(0, 95, 0),
    ]);
    shellGroup.add(
      new THREE.Line(
        axisGeo,
        new THREE.LineBasicMaterial({ color: 0xc4b5fd, transparent: true, opacity: 0.5 })
      )
    );
  }

  function buildNodes() {
    clearGroup(nodeGroup);
    nodeMeshes.clear();
    for (const n of nodes) {
      // full graph: de-emphasize tiny extensions so cores/comms read first
      const isCore = !!(
        n.is_core ||
        n.kind === "domain" ||
        n.kind === "seed" ||
        n.kind === "law" ||
        n.kind === "problem_route"
      );
      const isExt = n.kind === "extension" || n.atlas_kind === "extension_panel";
      if (isFull && isExt && !n.is_core && Math.abs(Number(n.S) || 0) < 0.15 && !n.green_gate) {
        // keep most extensions but smaller; skip ultra-weak noise
        // still show — size handles emphasis
      }

      const pos = nodeWorldPos(n, isFull);
      const col = parseColor(n.color);
      const baseR = Math.max(0.55, (n.size || 8) * (isCore ? 0.14 : 0.09));
      const radius = n.kind === "law" ? baseR * 1.8 : isCore ? baseR * 1.2 : baseR * 0.7;
      const geo = new THREE.SphereGeometry(radius, isCore ? 18 : 10, isCore ? 14 : 8);
      const mat = new THREE.MeshStandardMaterial({
        color: col,
        emissive: col,
        emissiveIntensity: n.kind === "seed" || n.kind === "law" ? 0.65 : isCore ? 0.38 : 0.22,
        metalness: 0.12,
        roughness: 0.38,
        transparent: isExt && isFull,
        opacity: isExt && isFull ? 0.82 : 1,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.copy(pos);
      mesh.userData.node = n;
      nodeGroup.add(mesh);
      nodeMeshes.set(n.id, mesh);
    }
    highlightSelection();
  }

  function buildEdges() {
    clearGroup(edgeGroup);
    clearGroup(pulseGroup);
    structSegments = [];
    const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));

    // pass 1: structural communication axons (always prioritized)
    const structList = [];
    const meshList = [];
    for (const e of edges) {
      if (!edgeAllowed(e, lodDense, lodUltra)) continue;
      if (isStructuralEdge(e)) structList.push(e);
      else meshList.push(e);
    }
    // sort structural by strength / kind importance
    const kindPri = {
      seed_to_law: 0,
      law_to_domain: 1,
      routes_to_core: 2,
      long_range: 3,
      ladder: 4,
      problem_route: 5,
    };
    structList.sort(
      (a, b) =>
        (kindPri[a.kind] ?? 9) - (kindPri[b.kind] ?? 9) ||
        (b.strength || 0) - (a.strength || 0)
    );

    const maxStruct = isFull ? 900 : 500;
    const maxMesh = lodUltra ? 2500 : lodDense ? 800 : 0;
    const chosen = structList.slice(0, maxStruct).concat(meshList.slice(0, maxMesh));

    const positions = [];
    const colors = [];

    for (const e of chosen) {
      const a = byId[e.source];
      const b = byId[e.target];
      if (!a || !b) continue;
      // law→extension only for cores when full (keep axons clean)
      if (
        e.kind === "law_to_domain" &&
        isFull &&
        b &&
        !b.is_core &&
        b.kind === "extension"
      ) {
        continue;
      }
      const pa = nodeWorldPos(a, isFull);
      const pb = nodeWorldPos(b, isFull);
      positions.push(pa.x, pa.y, pa.z, pb.x, pb.y, pb.z);

      const k = e.kind || "";
      let c = new THREE.Color(0x7dd3fc);
      let gain = 0.9;
      if (k === "seed_to_law") {
        c = new THREE.Color(0xffffff);
        gain = 1.4;
      } else if (k === "law_to_domain") {
        c = new THREE.Color(0xd8b4fe);
        gain = isFull ? 0.75 : 1.15;
      } else if (k === "routes_to_core") {
        c = new THREE.Color(0xa3e635);
        gain = 1.25;
      } else if (k === "long_range" || k === "ladder") {
        c = new THREE.Color(0x22d3ee);
        gain = 1.2;
      } else if (k === "problem_route") {
        c = new THREE.Color(0xf472b6);
        gain = 1.1;
      } else if (k === "prediction_link") {
        c = new THREE.Color(0xfbbf24);
        gain = 0.95;
      } else if (isDenseMesh(e)) {
        c = new THREE.Color(0x38bdf8);
        gain = 0.25;
      }

      colors.push(c.r * gain, c.g * gain, c.b * gain);
      colors.push(c.r * gain, c.g * gain, c.b * gain);

      if (isStructuralEdge(e) && !isDenseMesh(e)) {
        structSegments.push({ pa: pa.clone(), pb: pb.clone(), kind: k });
      }
    }

    if (positions.length) {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
      geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
      edgeGroup.add(
        new THREE.LineSegments(
          geo,
          new THREE.LineBasicMaterial({
            vertexColors: true,
            transparent: true,
            opacity: 0.95,
            depthWrite: false,
            blending: THREE.AdditiveBlending,
          })
        )
      );
    }

    // communication pulse sprites along top structural axons
    const pulseN = Math.min(structSegments.length, isFull ? 80 : 120);
    for (let i = 0; i < pulseN; i++) {
      const seg = structSegments[i];
      if (!seg) continue;
      const pgeo = new THREE.SphereGeometry(0.55, 8, 6);
      const pmat = new THREE.MeshBasicMaterial({
        color: 0xe0f2fe,
        transparent: true,
        opacity: 0.9,
        depthWrite: false,
      });
      const m = new THREE.Mesh(pgeo, pmat);
      m.userData.seg = seg;
      m.userData.phase = Math.random();
      pulseGroup.add(m);
    }
  }

  function highlightSelection() {
    for (const [id, mesh] of nodeMeshes) {
      const sel = id === selectedId;
      mesh.scale.setScalar(sel ? 1.65 : 1);
      if (mesh.material && mesh.material.emissiveIntensity != null) {
        const n = mesh.userData.node || {};
        const isCore = !!(n.is_core || n.kind === "domain" || n.kind === "seed" || n.kind === "law");
        mesh.material.emissiveIntensity = sel
          ? 0.85
          : n.kind === "seed" || n.kind === "law"
            ? 0.65
            : isCore
              ? 0.38
              : 0.22;
      }
    }
  }

  function setGraph(nextNodes, nextEdges, meta = {}) {
    nodes = nextNodes || [];
    edges = nextEdges || [];
    isFull = nodes.length > 80;
    buildShells();
    buildNodes();
    buildEdges();
    const box = new THREE.Box3().setFromObject(nodeGroup);
    if (!box.isEmpty()) {
      const size = box.getSize(new THREE.Vector3());
      const center = box.getCenter(new THREE.Vector3());
      controls.target.copy(center);
      const dist = Math.max(size.length() * 0.5, 90);
      camera.position.set(center.x + dist * 0.35, center.y + dist * 0.28, center.z + dist * 0.55);
      controls.update();
    }
  }

  function setSelected(nodeOrId) {
    selectedId = nodeOrId && typeof nodeOrId === "object" ? nodeOrId.id : nodeOrId || null;
    highlightSelection();
  }

  function setLodFromDistance() {
    const d = camera.position.distanceTo(controls.target);
    const nextDense = d < 160;
    const nextUltra = d < 85;
    if (nextDense !== lodDense || nextUltra !== lodUltra) {
      lodDense = nextDense;
      lodUltra = nextUltra;
      buildEdges();
    }
  }

  function resize() {
    const rect = container.getBoundingClientRect();
    width = Math.max(1, rect.width);
    height = Math.max(1, rect.height);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
  }

  function setVisible(v) {
    visible = !!v;
    renderer.domElement.style.display = visible ? "block" : "none";
    if (labelEl) labelEl.style.display = "none";
    if (visible) {
      resize();
      controls.update();
    }
  }

  function pick(clientX, clientY) {
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(nodeGroup.children, false);
    if (hits.length) return hits[0].object.userData.node || null;
    return null;
  }

  function showHoverLabel(n, clientX, clientY) {
    const el = ensureLabel();
    if (!n) {
      el.style.display = "none";
      return;
    }
    const rect = container.getBoundingClientRect();
    const bits = [n.label || n.id];
    if (n.physics_spine) bits.push(n.physics_spine);
    if (n.D_eff != null) bits.push("D_eff " + n.D_eff);
    if (n.scale_band) bits.push(n.scale_band);
    el.textContent = bits.join(" · ");
    el.style.display = "block";
    el.style.left = `${clientX - rect.left + 12}px`;
    el.style.top = `${clientY - rect.top + 12}px`;
  }

  renderer.domElement.addEventListener("pointerdown", () => {
    renderer.domElement.style.cursor = "grabbing";
  });
  window.addEventListener("pointerup", () => {
    if (renderer.domElement) renderer.domElement.style.cursor = "grab";
  });

  renderer.domElement.addEventListener("click", (ev) => {
    const n = pick(ev.clientX, ev.clientY);
    if (n) {
      setSelected(n);
      onSelect(n);
    }
  });

  renderer.domElement.addEventListener("pointermove", (ev) => {
    if (!visible) return;
    const n = pick(ev.clientX, ev.clientY);
    showHoverLabel(n, ev.clientX, ev.clientY);
    renderer.domElement.style.cursor = n ? "pointer" : "grab";
  });

  function animate() {
    if (disposed) return;
    requestAnimationFrame(animate);
    if (!visible) return;
    controls.update();
    setLodFromDistance();
    pulseT += 0.016;
    // travel communication pulses along structural axons
    for (const m of pulseGroup.children) {
      const seg = m.userData.seg;
      if (!seg) continue;
      const ph = (m.userData.phase + pulseT * 0.22) % 1;
      m.position.lerpVectors(seg.pa, seg.pb, ph);
      m.material.opacity = 0.35 + 0.55 * Math.sin(ph * Math.PI);
    }
    renderer.render(scene, camera);
  }
  animate();

  resize();
  setVisible(false);

  return {
    setGraph,
    setSelected,
    setVisible,
    resize,
    isVisible: () => visible,
    dispose() {
      disposed = true;
      controls.dispose();
      clearGroup(shellGroup);
      clearGroup(edgeGroup);
      clearGroup(nodeGroup);
      clearGroup(pulseGroup);
      renderer.dispose();
      if (renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
      if (labelEl && labelEl.parentNode) labelEl.parentNode.removeChild(labelEl);
    },
  };
}
