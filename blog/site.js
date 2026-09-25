const method = document.querySelector('#compare-method');
const frame = document.querySelector('#compare-frame');
function refresh() {
  const id = String(frame.value).padStart(3, '0');
  const name = method.selectedOptions[0].textContent;
  document.querySelector('#compare-pred').src = `assets/views/${method.value}_${id}.png`;
  document.querySelector('#compare-gt').src = `assets/views/GT_${id}.jpg`;
  document.querySelector('#compare-label').textContent = `${name} / KEYFRAME ${frame.value}`;
}
if (method && frame) {
  method.addEventListener('change', refresh);
  frame.addEventListener('change', refresh);
  refresh();
}
addEventListener('scroll', () => {
  const length = document.documentElement.scrollHeight - innerHeight;
  document.querySelector('#progress').style.width = (length > 0 ? 100 * scrollY / length : 0) + '%';
}, { passive: true });
