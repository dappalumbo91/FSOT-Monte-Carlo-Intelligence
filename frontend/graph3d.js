/**
 * FSOT 3D graph — As Above So Below shells.
 *
 * Layout (frozen from server doctrine):
 *   radius  ∝ D_eff ring (dimensional interface)
 *   angle   = physics spine clumps + S (from server)
 *   height  ∝ D_eff continuous (micro bottom-ish → macro up)
 *   color   = physics spine hue (from server node.color)
 *
 * Three.js ES module — loaded only when 3D mode is active.
 */
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

function parseColor(hex, fallback = 0x8892a4) {
  if (!hex || typeof hex !== "string") return fallback;
  const h = hex.replace("#", "").trim();
  if (h.length === 6) return parseInt(h, 16);
  if (h.length === 3) {
    const e = h.split("").map((c) => c + c).join("");
    return parseInt(e, 16);
  }
  return fallback;
}

function ringRadius(ring, isFull) {
  const r = Number(ring) || 0;
  const step = isFull ? 95 : 72;
  return 40 + r * step;
}

/**
 * Map node → world position (Three.js Y-up).
 * XZ plane = shell disk; Y = dimensional height from D_eff.
 */
function nodeWorldPos(n, isFull, scale = 0.045) {
  if (n.kind === "law") return new THREE.Vector3(0, 0, 0);
  if (n.kind === "seed") {
    const ids = ["seed_pi", "seed_e", "seed_phi", "seed_gamma", "seed_catalan"];
    const i = Math.max(0, ids.indexOf(n.id));
    const ang = (i * Math.PI * 2) / 5 - Math.PI / 2;
    const R = 28 * scale * 18;
    return new THREE.Vector3(Math.cos(ang) * R, 0, Math.sin(ang) * R);
  }
  // Prefer solid 2D home if anneal already ran
  if (n.homeX != null && n.homeY != null) {
    const d = Number(n.D_eff != null ? n.D_eff : 12);
    const y = ((d - 12.5) / 12.5) * 55; // ~ -55 .. +55
    return new THREE.Vector3(n.homeX * scale, y, n.homeY * scale);
  }
  const a = n.angle != null ? Number(n.angle) : 0;
  const R = ringRadius(n.ring, isFull) * scale;
  const d = Number(n.D_eff != null ? n.D_eff : 12);
  const y = ((d - 12.5) / 12.5) * 55;
  return new THREE.Vector3(Math.cos(a) * R, y, Math.sin(a) * R);
}

function edgeAllowed(e, lodDense, lodUltra) {
  const k = e.kind || "";
  const tier =
    e.density_tier ||
    (k === "coupling_lean_overlap" || k === "by_core_membership" ? "dense" : "base");
  if (tier === "base") return true;
  if (tier === "dense") return lodDense;
  return lodUltra;
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

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x07080d);
  scene.fog = new THREE.FogExp2(0x07080d, 0.006);

  const camera = new THREE.PerspectiveCamera(50, 1, 0.5, 5000);
  camera.position.set(0, 90, 160);

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
  controls.dampingFactor = 0.06;
  controls.minDistance = 20;
  controls.maxDistance = 420;
  controls.target.set(0, 0, 0);

  // lights
  scene.add(new THREE.AmbientLight(0xb0b8c8, 0.55));
  const key = new THREE.DirectionalLight(0xffffff, 0.85);
  key.position.set(40, 80, 30);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x88aaff, 0.25);
  fill.position.set(-50, 20, -40);
  scene.add(fill);

  // groups rebuilt on setGraph
  let shellGroup = new THREE.Group();
  let edgeGroup = new THREE.Group();
  let nodeGroup = new THREE.Group();
  scene.add(shellGroup);
  scene.add(edgeGroup);
  scene.add(nodeGroup);

  const nodeMeshes = new Map(); // id -> mesh
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let labelEl = null;

  function ensureLabel() {
    if (labelEl) return labelEl;
    labelEl = document.createElement("div");
    labelEl.className = "graph3d-label";
    labelEl.style.cssText =
      "position:absolute;pointer-events:none;padding:0.2rem 0.45rem;border-radius:6px;" +
      "background:rgba(8,10,16,0.85);border:1px solid rgba(120,140,180,0.25);" +
      "font-size:0.72rem;color:#e8ecf4;display:none;z-index:5;white-space:nowrap;";
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
    const maxRing = 8;
    for (let r = 1; r <= maxRing; r++) {
      const R = ringRadius(r, isFull) * 0.045;
      const geo = new THREE.RingGeometry(R * 0.98, R * 1.02, 64);
      geo.rotateX(-Math.PI / 2);
      const mat = new THREE.MeshBasicMaterial({
        color: 0x3a4560,
        transparent: true,
        opacity: 0.12 + (r === 1 ? 0.06 : 0),
        side: THREE.DoubleSide,
        depthWrite: false,
      });
      const mesh = new THREE.Mesh(geo, mat);
      // place shell at typical D_eff height for that ring band
      const dMid = (r - 1) * 4 + 2;
      mesh.position.y = ((dMid - 12.5) / 12.5) * 55;
      shellGroup.add(mesh);
    }
    // vertical axis (law → scale)
    const axisGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, -70, 0),
      new THREE.Vector3(0, 70, 0),
    ]);
    shellGroup.add(
      new THREE.Line(
        axisGeo,
        new THREE.LineBasicMaterial({ color: 0xc4b5fd, transparent: true, opacity: 0.35 })
      )
    );
  }

  function buildNodes() {
    clearGroup(nodeGroup);
    nodeMeshes.clear();
    for (const n of nodes) {
      const pos = nodeWorldPos(n, isFull);
      const col = parseColor(n.color);
      const isCore = !!(n.is_core || n.kind === "domain" || n.kind === "seed" || n.kind === "law");
      const baseR = Math.max(0.6, (n.size || 8) * 0.12);
      const radius = isCore ? baseR * 1.15 : baseR * 0.75;
      const geo = new THREE.SphereGeometry(radius, isCore ? 16 : 10, isCore ? 12 : 8);
      const mat = new THREE.MeshStandardMaterial({
        color: col,
        emissive: col,
        emissiveIntensity: n.kind === "seed" || n.kind === "law" ? 0.45 : 0.18,
        metalness: 0.15,
        roughness: 0.45,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.copy(pos);
      mesh.userData.node = n;
      mesh.userData.baseScale = 1;
      nodeGroup.add(mesh);
      nodeMeshes.set(n.id, mesh);
    }
    highlightSelection();
  }

  function buildEdges() {
    clearGroup(edgeGroup);
    const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
    const positions = [];
    const colors = [];
    let count = 0;
    const maxEdges = lodUltra ? 8000 : lodDense ? 4000 : 2200;

    for (const e of edges) {
      if (!edgeAllowed(e, lodDense, lodUltra)) continue;
      const a = byId[e.source];
      const b = byId[e.target];
      if (!a || !b) continue;
      const pa = nodeWorldPos(a, isFull);
      const pb = nodeWorldPos(b, isFull);
      positions.push(pa.x, pa.y, pa.z, pb.x, pb.y, pb.z);

      const k = e.kind || "";
      let c = new THREE.Color(0x67e8f9);
      let alpha = 0.35;
      if (k === "law_to_domain") {
        c = new THREE.Color(0xc4b5fd);
        alpha = isFull ? 0.08 : 0.18;
      } else if (k === "routes_to_core") {
        c = new THREE.Color(0xa3e635);
        alpha = 0.45;
      } else if (k === "coupling_lean_overlap" || k === "by_core_membership") {
        c = new THREE.Color(0x22d3ee);
        alpha = lodUltra ? 0.12 : 0.07;
      } else if (k === "long_range" || k === "ladder") {
        c = new THREE.Color(0x67e8f9);
        alpha = 0.55;
      } else if (k === "problem_route") {
        c = new THREE.Color(0xf472b6);
        alpha = 0.5;
      } else if (k === "seed_to_law") {
        c = new THREE.Color(0xffffff);
        alpha = 0.7;
      }
      // vertex colors (rgb only; opacity via material)
      colors.push(c.r * alpha * 2, c.g * alpha * 2, c.b * alpha * 2);
      colors.push(c.r * alpha * 2, c.g * alpha * 2, c.b * alpha * 2);
      count += 1;
      if (count >= maxEdges) break;
    }

    if (!positions.length) return;
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    const mat = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      depthWrite: false,
    });
    edgeGroup.add(new THREE.LineSegments(geo, mat));
  }

  function highlightSelection() {
    for (const [id, mesh] of nodeMeshes) {
      const sel = id === selectedId;
      mesh.scale.setScalar(sel ? 1.55 : 1);
      if (mesh.material && mesh.material.emissiveIntensity != null) {
        const n = mesh.userData.node || {};
        mesh.material.emissiveIntensity = sel
          ? 0.7
          : n.kind === "seed" || n.kind === "law"
            ? 0.45
            : 0.18;
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
    // frame camera
    const box = new THREE.Box3().setFromObject(nodeGroup);
    if (!box.isEmpty()) {
      const size = box.getSize(new THREE.Vector3());
      const center = box.getCenter(new THREE.Vector3());
      controls.target.copy(center);
      const dist = Math.max(size.length() * 0.55, 80);
      camera.position.set(center.x + dist * 0.45, center.y + dist * 0.35, center.z + dist * 0.55);
      controls.update();
    }
  }

  function setSelected(nodeOrId) {
    selectedId = nodeOrId && typeof nodeOrId === "object" ? nodeOrId.id : nodeOrId || null;
    highlightSelection();
  }

  function setLodFromDistance() {
    const d = camera.position.distanceTo(controls.target);
    // closer → denser mesh
    const nextDense = d < 140;
    const nextUltra = d < 70;
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
    el.textContent = `${n.label || n.id}${n.physics_spine ? " · " + n.physics_spine : ""}${n.D_eff != null ? " · D_eff " + n.D_eff : ""}`;
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
    // ignore if user was orbiting (small move threshold handled by OrbitControls)
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
    renderer.render(scene, camera);
  }
  animate();

  // initial size
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
      renderer.dispose();
      if (renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
      if (labelEl && labelEl.parentNode) labelEl.parentNode.removeChild(labelEl);
    },
  };
}
