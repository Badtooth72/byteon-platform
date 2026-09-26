let dirty = new Set();
document.querySelectorAll('.review-row').forEach(form => {
  form.addEventListener('input', () => { dirty.add(form); form.querySelector('.status').textContent = 'Unsaved changes'; });
  form.addEventListener('submit', async event => {
    event.preventDefault(); const button = form.querySelector('button'); button.disabled = true;
    try { const response = await fetch(form.action, {method:'POST', body:new FormData(form)}); const data = await editorResponse(response);
      form.elements.revision.value = data.revision; dirty.delete(form); form.querySelector('.status').textContent = data.message;
    } catch(error) { form.querySelector('.status').textContent = error.message; } finally { button.disabled = false; }
  });
});
document.querySelectorAll('details').forEach(detail => detail.addEventListener('toggle', () => {
  const frame = detail.querySelector('iframe'); if (detail.open && frame && !frame.src) frame.src = frame.dataset.src;
}));
window.addEventListener('beforeunload', event => { if(dirty.size) { event.preventDefault(); event.returnValue = ''; } });
