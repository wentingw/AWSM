import * as THREE from 'three';
import { GLTFLoader } from './vendor/three/loaders/GLTFLoader.js';
import { OrbitControls } from './vendor/three/controls/OrbitControls.js';
import { RoomEnvironment } from './vendor/three/environments/RoomEnvironment.js';

const panel = document.querySelector('#scene-comparison');
if (panel) {
  const stage = panel.querySelector('.scene-stage');
  const select = panel.querySelector('#model-select');
  const mode = panel.querySelector('#scene-mode');
  const slider = panel.querySelector('#scene-split');
  const divider = panel.querySelector('.scene-divider');
  const status = panel.querySelector('.scene-status');
  const leftLabel = panel.querySelector('.scene-label-left');
  const rightLabel = panel.querySelector('.scene-label-right');
  const zh = document.documentElement.lang.startsWith('zh');
  const labels = {
    M1: zh ? 'M1 · 纯视觉 + Astra' : 'M1 · RGB-only + Astra',
    M2: 'M2 · ViPE + Astra',
    M3: 'M3 · OpenVINS + MapAnything + Astra',
    M4: zh ? 'M4 · GT 位姿 + MapAnything + Astra' : 'M4 · GT pose + MapAnything + Astra',
    GT: zh ? 'GT · 原始仿真场景' : 'GT · Original simulator scene'
  };
  let started = false, active = false, renderer, camera, controls, environment, manifest;
  let selectedScene, truthScene, resizeObserver, split = 0.5, version = 0;
  const cache = new Map();
  const setStatus = (text, error = false) => {
    status.textContent = text;
    status.hidden = !text;
    status.classList.toggle('error', error);
    panel.dataset.state = error ? 'error' : text ? 'loading' : 'ready';
  };
  function render() {
    if (!renderer || !selectedScene) return;
    const width = stage.clientWidth, height = stage.clientHeight;
    renderer.setScissorTest(false);
    renderer.setViewport(0, 0, width, height);
    renderer.clear();
    if (mode.value === 'single' || select.value === 'GT' || !truthScene) {
      renderer.render(selectedScene, camera);
      return;
    }
    // One camera, one full-size viewport: scissor only clips pixels, never changes framing.
    const boundary = Math.round(width * split);
    renderer.setScissorTest(true);
    renderer.setScissor(0, 0, boundary, height);
    renderer.render(selectedScene, camera);
    renderer.setScissor(boundary, 0, width - boundary, height);
    renderer.render(truthScene, camera);
    renderer.setScissorTest(false);
  }
  function updateMode() {
    const comparing = mode.value === 'compare' && select.value !== 'GT';
    panel.classList.toggle('is-comparing', comparing);
    slider.disabled = !comparing;
    divider.hidden = !comparing;
    rightLabel.hidden = !comparing;
    leftLabel.textContent = labels[select.value];
    render();
  }
  function updateSplit(value) {
    split = Math.max(0.02, Math.min(0.98, Number(value) / 100));
    slider.value = String(Math.round(split * 100));
    stage.style.setProperty('--split', `${split * 100}%`);
    divider.setAttribute('aria-valuenow', slider.value);
    divider.setAttribute('aria-valuetext', `${slider.value}%`);
    render();
  }
  function resetCamera() {
    if (!camera || !manifest) return;
    const view = manifest.camera;
    controls.target.fromArray(view.target);
    camera.position.fromArray(view.position);
    camera.near = view.near || 0.05;
    camera.far = view.far || 500;
    camera.fov = view.fov || 42;
    camera.updateProjectionMatrix();
    controls.update();
    render();
  }
  function resize() {
    if (!renderer) return;
    const width = stage.clientWidth, height = stage.clientHeight;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    render();
  }
  function loadScene(id) {
    if (!cache.has(id)) {
      const promise = new GLTFLoader().loadAsync(manifest.models[id].url).then(gltf => {
        const scene = new THREE.Scene();
        scene.background = new THREE.Color('#e9ede5');
        scene.environment = environment;
        scene.add(new THREE.HemisphereLight(0xffffff, 0x68746b, 2));
        const sun = new THREE.DirectionalLight(0xffffff, 2.3);
        sun.position.set(12, 25, 18);
        scene.add(sun);
        // Exported models already share the same metric GT frame. Never center or rescale per model.
        scene.add(gltf.scene);
        scene.userData.method = id;
        return scene;
      }).catch(error => { cache.delete(id); throw error; });
      cache.set(id, promise);
    }
    return cache.get(id);
  }
  async function selectScene() {
    if (!manifest) return;
    const request = ++version, id = select.value;
    setStatus(zh ? `正在加载 ${labels[id]}…` : `Loading ${labels[id]}…`);
    try {
      const [model, gt] = await Promise.all([loadScene(id), loadScene('GT')]);
      if (request !== version) return;
      selectedScene = model;
      truthScene = gt;
      setStatus('');
      updateMode();
      panel.dataset.loadedModel = id;
      panel.dataset.gtLoaded = 'true';
    } catch (error) {
      if (request !== version) return;
      console.error('Scene asset load failed', error);
      setStatus(zh ? '场景加载失败，请点击“重试”。' : 'Scene loading failed. Select “Retry”.', true);
    }
  }
  async function start() {
    if (started) return;
    started = true;
    try {
      setStatus(zh ? '正在加载对比场景…' : 'Loading comparison scenes…');
      const response = await fetch('assets/comparison/viewer_manifest.json');
      if (!response.ok) throw new Error(`Scene manifest HTTP ${response.status}`);
      manifest = await response.json();
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
      renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1;
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.domElement.setAttribute('aria-label', zh ? '重建与 GT 三维场景，拖动旋转，滚轮缩放' : 'Reconstruction and GT in 3D; drag to rotate, scroll to zoom');
      renderer.domElement.setAttribute('role', 'img');
      renderer.domElement.tabIndex = 0;
      stage.prepend(renderer.domElement);
      camera = new THREE.PerspectiveCamera(42, 1, 0.05, 500);
      controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = false;
      controls.minDistance = 1;
      controls.maxDistance = 200;
      controls.maxPolarAngle = Math.PI * 0.49;
      controls.addEventListener('change', render);
      const pmrem = new THREE.PMREMGenerator(renderer);
      const room = new RoomEnvironment();
      environment = pmrem.fromScene(room, 0.04).texture;
      room.dispose(); pmrem.dispose();
      resizeObserver = new ResizeObserver(resize);
      resizeObserver.observe(stage);
      resetCamera(); resize();
      renderer.domElement.addEventListener('webglcontextlost', e => {
        e.preventDefault(); setStatus(zh ? '图形上下文已暂停，请刷新页面。' : 'Graphics context paused. Please reload.', true);
      });
      // Read-only diagnostics used by browser checks; both render passes use this exact camera.
      panel.sceneDiagnostics = () => ({
        selected: select.value, loaded: selectedScene?.userData.method, gtLoaded: !!truthScene,
        camera: camera.position.toArray(), target: controls.target.toArray(), split,
        mode: mode.value, singleCamera: true, coordinateFrame: manifest.coordinate_frame,
        viewport: [stage.clientWidth, stage.clientHeight], cachedModels: [...cache.keys()]
      });
      await selectScene();
    } catch (error) {
      console.error('Scene comparison initialization failed', error);
      resizeObserver?.disconnect();
      controls?.dispose();
      environment?.dispose();
      renderer?.dispose();
      renderer?.domElement.remove();
      renderer = camera = controls = environment = manifest = undefined;
      selectedScene = truthScene = undefined;
      cache.clear();
      started = false;
      setStatus(zh ? '无法启动三维场景，请点击“重试”。' : 'Unable to start the 3D viewer. Select “Retry”.', true);
    }
  }
  select.addEventListener('change', () => { updateMode(); selectScene(); });
  mode.addEventListener('change', updateMode);
  slider.addEventListener('input', () => updateSplit(slider.value));
  panel.querySelector('#scene-reset').addEventListener('click', resetCamera);
  panel.querySelector('#scene-retry').addEventListener('click', () => manifest && renderer ? selectScene() : start());
  divider.addEventListener('pointerdown', e => {
    e.preventDefault(); e.stopPropagation(); active = true;
    divider.setPointerCapture(e.pointerId);
    if (controls) controls.enabled = false;
  });
  divider.addEventListener('pointermove', e => {
    if (!active) return;
    const bounds = stage.getBoundingClientRect();
    updateSplit((e.clientX - bounds.left) / bounds.width * 100);
  });
  const stopDrag = () => { active = false; if (controls) controls.enabled = true; };
  divider.addEventListener('pointerup', stopDrag);
  divider.addEventListener('pointercancel', stopDrag);
  divider.addEventListener('lostpointercapture', stopDrag);
  divider.addEventListener('keydown', e => {
    const values = { ArrowLeft: -2, ArrowRight: 2, PageDown: -10, PageUp: 10 };
    if (e.key in values) { e.preventDefault(); updateSplit(split * 100 + values[e.key]); }
    if (e.key === 'Home' || e.key === 'End') { e.preventDefault(); updateSplit(e.key === 'Home' ? 2 : 98); }
  });
  updateSplit(50); updateMode();
  const observer = new IntersectionObserver(entries => {
    if (entries.some(e => e.isIntersecting)) { observer.disconnect(); start(); }
  }, { rootMargin: '300px' });
  observer.observe(panel);
}
