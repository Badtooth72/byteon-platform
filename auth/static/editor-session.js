// Renew an existing session after editing activity; idle tabs do not renew it.
let editorActivity = 0, editorRenewed = 0;
['input','pointerdown','keydown'].forEach(type => document.addEventListener(type, () => { editorActivity = Date.now(); }, {passive:true}));
setInterval(async () => {
  if (document.visibilityState !== 'visible' || editorActivity <= editorRenewed || Date.now()-editorActivity > 60000) return;
  editorRenewed = editorActivity;
  try { const response=await fetch('/network-designer/session', {credentials:'same-origin'}); if(response.status===401)document.dispatchEvent(new Event('byteon-session-expired')); } catch (_) { /* Save reports connection errors. */ }
}, 30000);
async function editorResponse(response) {
  if (response.redirected || response.status===401) throw new Error('Your session expired. Sign in again, then reload this page.');
  if (!(response.headers.get('content-type') || '').includes('application/json')) throw new Error(`Unable to save (server response ${response.status}). Please try again. Your edits are still here.`);
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Unable to save');
  return result;
}
