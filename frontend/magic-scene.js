export function mountMagicScene(root) {
  const scene = root.querySelector('.magic-scene');
  const layer = scene?.querySelector('.carpet-depth');
  const toggle = root.querySelector('.motion-toggle');
  if (!scene || !layer || !toggle) return;
  const canvas = document.createElement('canvas');
  canvas.className = 'starfield'; canvas.setAttribute('aria-hidden', 'true');
  root.prepend(canvas);
  const ctx = canvas.getContext('2d');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let paused = reduced.matches, frame = 0, w = 1, h = 1, tx = 0, ty = 0, x = 0, y = 0, last = 0, elapsed = 0;
  const stars = Array.from({length: 85}, (_, i) => ({x: (i * .6180339) % 1, y: (i * .4142136) % 1, z: .2 + (i % 13) / 16}));
  function draw() {
    if (!ctx) return;
    ctx.clearRect(0, 0, w, h);
    for (const s of stars) {
      const px = ((s.x * w + elapsed * .003 * s.z + x * 25 * s.z) % w + w) % w;
      const py = s.y * h + y * 18 * s.z;
      ctx.beginPath(); ctx.arc(px, py, .4 + s.z, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(226,218,187,${.15 + s.z * .45})`; ctx.fill();
    }
  }
  function resize() {
    w = root.clientWidth; h = root.clientHeight;
    const dpr = Math.min(devicePixelRatio || 1, 1.5);
    canvas.width = w * dpr; canvas.height = h * dpr;
    ctx?.setTransform(dpr, 0, 0, dpr, 0, 0); draw();
  }
  function tick(now) {
    frame = 0;
    if (!root.isConnected || paused || document.hidden) { last = 0; return; }
    elapsed += last ? Math.min(now - last, 40) : 0; last = now;
    x += (tx - x) * .055; y += (ty - y) * .055;
    layer.style.transform = `translate3d(${x * 24}px,${y * 14 + Math.sin(elapsed / 2300) * 4}px,28px) rotateY(${x * 5}deg) rotateX(${-y * 3}deg)`;
    draw(); frame = requestAnimationFrame(tick);
  }
  function update() {
    cancelAnimationFrame(frame); frame = 0; last = 0;
    root.classList.toggle('motion-paused', paused);
    toggle.textContent = paused ? 'Activar animación' : 'Pausar animación';
    toggle.setAttribute('aria-pressed', String(paused));
    if (paused) { x = y = tx = ty = 0; layer.style.transform = 'none'; draw(); }
    else if (!document.hidden) frame = requestAnimationFrame(tick);
  }
  const preference = () => { paused = reduced.matches; update(); };
  const visibility = () => update();
  root.addEventListener('pointermove', e => {
    if (paused || e.pointerType !== 'mouse') return;
    const b = root.getBoundingClientRect();
    tx = ((e.clientX - b.left) / b.width - .5) * 2;
    ty = ((e.clientY - b.top) / b.height - .5) * 2;
  });
  root.addEventListener('pointerleave', () => { tx = ty = 0; });
  toggle.addEventListener('click', () => { paused = !paused; update(); });
  reduced.addEventListener('change', preference);
  document.addEventListener('visibilitychange', visibility);
  const size = new ResizeObserver(resize); size.observe(root);
  const cleanup = new MutationObserver(() => {
    if (root.isConnected) return;
    cancelAnimationFrame(frame); size.disconnect(); cleanup.disconnect();
    reduced.removeEventListener('change', preference);
    document.removeEventListener('visibilitychange', visibility);
  });
  cleanup.observe(root.parentNode, {childList:true});
  resize(); update();
}
