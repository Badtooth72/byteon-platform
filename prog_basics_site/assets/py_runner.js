
let pyodideReady = null;
async function loadPyodideOnce() {
  if (!pyodideReady) {
    pyodideReady = new Promise(async (resolve, reject) => {
      try {
        const pyodide = await loadPyodide({ indexURL: "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/" });
        resolve(pyodide);
      } catch (e) { reject(e); }
    });
  }
  return pyodideReady;
}
async function runPython(code, outputEl) {
  const py = await loadPyodideOnce();
  outputEl.textContent = "Running...";
  try {
    const wrapped = `
import sys, io
from contextlib import redirect_stdout, redirect_stderr
_out = io.StringIO(); _err = io.StringIO()
code = r\"\"\"${code.replace('\\','\\\\').replace('`','\\`')}\"\"\"
with redirect_stdout(_out), redirect_stderr(_err):
    try:
        exec(code, {})
    except Exception as e:
        import traceback; traceback.print_exc()
out = _out.getvalue(); err = _err.getvalue()
`;
    await py.runPythonAsync(wrapped);
    const out = py.globals.get("out");
    const err = py.globals.get("err");
    outputEl.textContent = (out || "") + (err || "");
  } catch (err) {
    outputEl.textContent = String(err);
  }
}
window.initRunner = function(textareaId, outputId, starter) {
  const ta = document.getElementById(textareaId);
  const out = document.getElementById(outputId);
  if (starter) ta.value = starter.trim();
  document.getElementById(textareaId+"-run").addEventListener("click", () => runPython(ta.value, out));
  document.getElementById(textareaId+"-reset").addEventListener("click", () => { ta.value = (starter || "").trim(); out.textContent = ""; });
}
