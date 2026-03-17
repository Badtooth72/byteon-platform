let username = "guest";

// Session check
fetch("/api/session-user")
  .then(res => res.json())
  .then(data => {
    username = data.username;
    if (username === "guest") {
      alert("Please log in to access the quiz.");
      window.location.href = "/login";
    }
  })
  .catch(() => {
    alert("Session check failed. Please log in again.");
    window.location.href = "/login";
  });

function enableDrag(selector) {
  document.querySelectorAll(selector).forEach(item => {
    item.addEventListener("dragstart", e => {
      e.dataTransfer.setData("text/plain", e.target.id);
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  enableDrag(".gate-img");
});

// ---------- Helpers ----------
function gateNameFromId(id) {
  if (!id) return "none";
  if (id === "img-AND") return "AND";
  if (id === "img-OR") return "OR";
  if (id === "img-NOT") return "NOT";
  return id;
}

function renderTruthTable(table) {
  const hdr = Object.keys(table[0]).map(h => `<th>${h}</th>`).join("");
  const bd = table
    .map(r => `<tr>${Object.values(r).map(v => `<td>${v}</td>`).join("")}</tr>`)
    .join("");
  return `<table class="table table-dark mb-0"><thead><tr>${hdr}</tr></thead><tbody>${bd}</tbody></table>`;
}

// ---------- Level 4 questions ----------
const level4Questions = [
  // 2-dropzone circuits
  {
    id: "level4_q1",
    truthTable: [
      { A: 0, B: 0, C: 1, P: 0 },
      { A: 1, B: 0, C: 1, P: 1 }
    ],
    dropzones: 2,
    expected: ["img-AND", "img-OR"],
    diagramHTML: `
      <div class="circuit-board circuit-2">
        <svg class="wires" viewBox="0 0 980 240" preserveAspectRatio="none">
          <!-- A -> g1 -->
          <path d="M90 60 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <!-- B -> g1 -->
          <path d="M90 120 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <!-- g1 -> g2 -->
          <path d="M460 120 H640" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <!-- C (hint wire) -->
          <path d="M90 180 H220" stroke="rgba(255,255,255,0.12)" stroke-width="3" fill="none"/>
          <!-- g2 -> P -->
          <path d="M840 120 H930" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
        </svg>

        <div class="node inA"><span class="tag">A</span><span class="arrow">→</span></div>
        <div class="node inB"><span class="tag">B</span><span class="arrow">→</span></div>
        <div class="node inC"><span class="tag">C</span><span class="arrow">→</span></div>

        <div class="image-dropzone g1" data-expected="img-AND" data-slot="1"></div>
        <div class="link">→</div>
        <div class="image-dropzone g2" data-expected="img-OR" data-slot="2"></div>
        <div class="node op"><span class="arrow">→</span><span class="tag">P</span></div>
      </div>
    `
  },
  {
    id: "level4_q2",
    truthTable: [
      { A: 0, B: 1, C: 0, P: 1 },
      { A: 1, B: 1, C: 1, P: 0 }
    ],
    dropzones: 2,
    expected: ["img-OR", "img-NOT"],
    diagramHTML: `
      <div class="circuit-board circuit-2">
        <svg class="wires" viewBox="0 0 980 240" preserveAspectRatio="none">
          <path d="M90 60 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M90 120 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M460 120 H640" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M90 180 H220" stroke="rgba(255,255,255,0.12)" stroke-width="3" fill="none"/>
          <path d="M840 120 H930" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
        </svg>

        <div class="node inA"><span class="tag">A</span><span class="arrow">→</span></div>
        <div class="node inB"><span class="tag">B</span><span class="arrow">→</span></div>
        <div class="node inC"><span class="tag">C</span><span class="arrow">→</span></div>

        <div class="image-dropzone g1" data-expected="img-OR" data-slot="1"></div>
        <div class="link">→</div>
        <div class="image-dropzone g2" data-expected="img-NOT" data-slot="2"></div>
        <div class="node op"><span class="arrow">→</span><span class="tag">P</span></div>
      </div>
    `
  },
  {
    id: "level4_q3",
    truthTable: [
      { A: 1, B: 1, C: 0, P: 0 },
      { A: 0, B: 0, C: 0, P: 1 }
    ],
    dropzones: 2,
    expected: ["img-OR", "img-NOT"],
    diagramHTML: `
      <div class="circuit-board circuit-2">
        <svg class="wires" viewBox="0 0 980 240" preserveAspectRatio="none">
          <path d="M90 60 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M90 120 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M460 120 H640" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M90 180 H220" stroke="rgba(255,255,255,0.12)" stroke-width="3" fill="none"/>
          <path d="M840 120 H930" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
        </svg>

        <div class="node inA"><span class="tag">A</span><span class="arrow">→</span></div>
        <div class="node inB"><span class="tag">B</span><span class="arrow">→</span></div>
        <div class="node inC"><span class="tag">C</span><span class="arrow">→</span></div>

        <div class="image-dropzone g1" data-expected="img-OR" data-slot="1"></div>
        <div class="link">→</div>
        <div class="image-dropzone g2" data-expected="img-NOT" data-slot="2"></div>
        <div class="node op"><span class="arrow">→</span><span class="tag">P</span></div>
      </div>
    `
  },
  {
    id: "level4_q4",
    truthTable: [
      { A: 0, B: 0, C: 0, P: 0 },
      { A: 1, B: 1, C: 1, P: 1 }
    ],
    dropzones: 2,
    expected: ["img-AND", "img-OR"],
    diagramHTML: `
      <div class="circuit-board circuit-2">
        <svg class="wires" viewBox="0 0 980 240" preserveAspectRatio="none">
          <path d="M90 60 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M90 120 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M460 120 H640" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M90 180 H220" stroke="rgba(255,255,255,0.12)" stroke-width="3" fill="none"/>
          <path d="M840 120 H930" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
        </svg>

        <div class="node inA"><span class="tag">A</span><span class="arrow">→</span></div>
        <div class="node inB"><span class="tag">B</span><span class="arrow">→</span></div>
        <div class="node inC"><span class="tag">C</span><span class="arrow">→</span></div>

        <div class="image-dropzone g1" data-expected="img-AND" data-slot="1"></div>
        <div class="link">→</div>
        <div class="image-dropzone g2" data-expected="img-OR" data-slot="2"></div>
        <div class="node op"><span class="arrow">→</span><span class="tag">P</span></div>
      </div>
    `
  },

  // 3-dropzone circuits
  {
    id: "level4_q5",
    truthTable: [
      { A: 0, B: 0, C: 0, P: 1 },
      { A: 1, B: 1, C: 0, P: 1 },
      { A: 1, B: 1, C: 1, P: 0 }
    ],
    dropzones: 3,
    expected: ["img-AND", "img-NOT", "img-OR"],
    diagramHTML: `
      <div class="circuit-board circuit-3">
        <svg class="wires" viewBox="0 0 980 240" preserveAspectRatio="none">
          <path d="M90 60 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M90 120 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M90 180 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M460 120 H640" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M840 120 H930" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
        </svg>

        <div class="node inA"><span class="tag">A</span><span class="arrow">→</span></div>
        <div class="node inB"><span class="tag">B</span><span class="arrow">→</span></div>
        <div class="node inC"><span class="tag">C</span><span class="arrow">→</span></div>

        <div class="image-dropzone g1" data-expected="img-AND" data-slot="1"></div>
        <div class="image-dropzone g2" data-expected="img-NOT" data-slot="2"></div>

        <div class="link">→</div>
        <div class="image-dropzone g3" data-expected="img-OR" data-slot="3"></div>
        <div class="node op"><span class="arrow">→</span><span class="tag">P</span></div>
      </div>
    `
  },
  {
    id: "level4_q6",
    truthTable: [
      { A: 0, B: 1, C: 1, P: 1 },
      { A: 1, B: 0, C: 1, P: 0 }
    ],
    dropzones: 3,
    expected: ["img-OR", "img-AND", "img-NOT"],
    diagramHTML: `
      <div class="circuit-board circuit-3">
        <svg class="wires" viewBox="0 0 980 240" preserveAspectRatio="none">
          <path d="M90 60 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M90 120 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M90 180 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M460 120 H640" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M840 120 H930" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
        </svg>

        <div class="node inA"><span class="tag">A</span><span class="arrow">→</span></div>
        <div class="node inB"><span class="tag">B</span><span class="arrow">→</span></div>
        <div class="node inC"><span class="tag">C</span><span class="arrow">→</span></div>

        <div class="image-dropzone g1" data-expected="img-OR" data-slot="1"></div>
        <div class="image-dropzone g2" data-expected="img-AND" data-slot="2"></div>

        <div class="link">→</div>
        <div class="image-dropzone g3" data-expected="img-NOT" data-slot="3"></div>
        <div class="node op"><span class="arrow">→</span><span class="tag">P</span></div>
      </div>
    `
  },
  {
    id: "level4_q7",
    truthTable: [
      { A: 0, B: 1, C: 0, P: 0 },
      { A: 1, B: 0, C: 0, P: 1 }
    ],
    dropzones: 3,
    expected: ["img-AND", "img-NOT", "img-OR"],
    diagramHTML: `
      <div class="circuit-board circuit-3">
        <svg class="wires" viewBox="0 0 980 240" preserveAspectRatio="none">
          <path d="M90 60 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M90 120 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M90 180 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M460 120 H640" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M840 120 H930" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
        </svg>

        <div class="node inA"><span class="tag">A</span><span class="arrow">→</span></div>
        <div class="node inB"><span class="tag">B</span><span class="arrow">→</span></div>
        <div class="node inC"><span class="tag">C</span><span class="arrow">→</span></div>

        <div class="image-dropzone g1" data-expected="img-AND" data-slot="1"></div>
        <div class="image-dropzone g2" data-expected="img-NOT" data-slot="2"></div>

        <div class="link">→</div>
        <div class="image-dropzone g3" data-expected="img-OR" data-slot="3"></div>
        <div class="node op"><span class="arrow">→</span><span class="tag">P</span></div>
      </div>
    `
  },
  {
    id: "level4_q8",
    truthTable: [
      { A: 0, B: 0, C: 1, P: 1 },
      { A: 1, B: 1, C: 0, P: 1 }
    ],
    dropzones: 3,
    expected: ["img-NOT", "img-AND", "img-OR"],
    diagramHTML: `
      <div class="circuit-board circuit-3">
        <svg class="wires" viewBox="0 0 980 240" preserveAspectRatio="none">
          <path d="M90 60 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M90 120 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M90 180 H260" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M460 120 H640" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
          <path d="M840 120 H930" stroke="rgba(255,255,255,0.20)" stroke-width="3" fill="none"/>
        </svg>

        <div class="node inA"><span class="tag">A</span><span class="arrow">→</span></div>
        <div class="node inB"><span class="tag">B</span><span class="arrow">→</span></div>
        <div class="node inC"><span class="tag">C</span><span class="arrow">→</span></div>

        <div class="image-dropzone g1" data-expected="img-NOT" data-slot="1"></div>
        <div class="image-dropzone g2" data-expected="img-AND" data-slot="2"></div>

        <div class="link">→</div>
        <div class="image-dropzone g3" data-expected="img-OR" data-slot="3"></div>
        <div class="node op"><span class="arrow">→</span><span class="tag">P</span></div>
      </div>
    `
  }
];

// ---------- Attempt-all flow ----------
let level4Pool = [];
let level4Index = 0;
let level4TotalScore = 0;
let level4Results = []; // per question record

function startLevel4() {
  level4Pool = [...level4Questions].sort(() => 0.5 - Math.random());
  level4Index = 0;
  level4TotalScore = 0;
  level4Results = [];
  renderLevel4(level4Pool[level4Index]);
}

function renderLevel4(q) {
  if (!q) return finishLevel4();

  window.level4Current = q;

  // render truth table
  document.getElementById("level4-table").outerHTML = `
    <table class="table table-dark" id="level4-table">${renderTruthTable(q.truthTable).replace('<table class="table table-dark mb-0">','').replace('</table>','')}</table>
  `;

  // render diagram
  document.getElementById("level4-diagram").innerHTML = q.diagramHTML;

  setupDrops();
  updateProgressUI();
}

function setupDrops() {
  enableDrag(".gate-img");

  document.querySelectorAll(".image-dropzone").forEach(z => {
    z.innerHTML = "";
    z.classList.remove("correct", "incorrect");
    delete z.dataset.answer;

    z.addEventListener("dragover", e => e.preventDefault());
    z.addEventListener("drop", e => {
      e.preventDefault();
      const id = e.dataTransfer.getData("text/plain");
      z.innerHTML = "";
      const img = document.getElementById(id).cloneNode(true);
      img.removeAttribute("draggable");
      z.appendChild(img);
      z.dataset.answer = id;
    });
  });
}

function updateProgressUI() {
  const el = document.getElementById("level4-progress");
  if (!el) return;
  el.textContent = `Question ${level4Index + 1} / ${level4Pool.length}`;
}

function submitLevel4() {
  const q = window.level4Current;
  const zones = Array.from(document.querySelectorAll(".image-dropzone"));

  // collect answers in slot order
  const answers = zones
    .sort((a, b) => (parseInt(a.dataset.slot || "0", 10) - parseInt(b.dataset.slot || "0", 10)))
    .map(z => z.dataset.answer || null);

  // mark
  let correctCount = 0;
  zones.forEach(z => {
    if ((z.dataset.answer || null) === z.dataset.expected) {
      z.classList.add("correct");
      correctCount++;
    } else {
      z.classList.add("incorrect");
    }
  });

  level4TotalScore += correctCount;

  // store per question result
  const resultRecord = {
    id: q.id,
    score: correctCount,
    outOf: zones.length,
    answers,
    expected: q.expected,
    truthTable: q.truthTable
  };
  level4Results.push(resultRecord);

  // log attempt to backend
  fetch("/api/progress", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username,
      activity_key: "logic_gate_quiz",
      challenge_id: q.id,
      score: correctCount,
      submission: `Level 4: ${correctCount}/${zones.length} | ${answers.map(gateNameFromId).join(", ")}`
    })
  }).finally(() => {
    // next question
    level4Index++;
    renderLevel4(level4Pool[level4Index]);
  });
}

function finishLevel4() {
  // hide question UI
  document.getElementById("level4-question-area").style.display = "none";

  // show results
  const finished = document.getElementById("level4-finished");
  finished.style.display = "block";

  document.getElementById("level4-final-score").textContent =
    `${level4TotalScore} marks across ${level4Results.length} questions`;

  // build review list
  const list = document.getElementById("level4-results-list");
  list.innerHTML = "";

  level4Results.forEach((r, idx) => {
    const attempted = r.answers.map(gateNameFromId).join(", ");
    const correct = r.expected.map(gateNameFromId).join(", ");

    const card = document.createElement("div");
    card.className = "result-card";

    card.innerHTML = `
      <h5>Question ${idx + 1} <span class="badge-mini">${r.score}/${r.outOf}</span></h5>
      <div class="result-meta">
        <div><span class="badge-mini">Attempted</span> <code class="inline">${attempted}</code></div>
        <div><span class="badge-mini">Correct</span> <code class="inline">${correct}</code></div>
      </div>
      <div style="margin-top: 12px;">
        ${renderTruthTable(r.truthTable)}
      </div>
    `;
    list.appendChild(card);
  });

  // post summary too
  fetch("/api/progress", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username,
      activity_key: "logic_gate_quiz",
      challenge_id: "level4_summary",
      score: level4TotalScore,
      submission: `Level 4 completed: ${level4TotalScore} marks / ${level4Results.length} questions`
    })
  }).catch(() => {});
}

/* =====================================================
   LEVEL 5: JSON-driven exam bank + dashboard logging
   ===================================================== */

async function startLevel5() {
  const $area = document.getElementById("l5-question-area");
  if (!$area) return; // not on level5.html

  const $progress = document.getElementById("l5-progress");
  const $score = document.getElementById("l5-score");
  const $submit = document.getElementById("l5-submit");
  const $next = document.getElementById("l5-next");

  // ---- load bank ----
  let bank;
  try {
    const res = await fetch("level5_questions.json", { cache: "no-store" });
    bank = await res.json();
  } catch (e) {
    $area.innerHTML = `<div class="result-card"><h5>Could not load question bank</h5><div class="text-secondary">Check level5_questions.json exists and is served.</div></div>`;
    $submit.disabled = true;
    return;
  }

  const questions = (bank.questions || []).slice();
  // shuffle (optional)
  questions.sort(() => 0.5 - Math.random());

  // ---- state ----
  let idx = 0;
  let total = 0;
  let submitted = false;
  const results = [];
  const startTime = Date.now();

  function normalizeText(s) {
    return (s || "")
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function truthPairsMark(studentP, answerP, pairsPerMark) {
    let correctRows = 0;
    for (let i = 0; i < answerP.length; i++) {
      if (String(studentP[i]) === String(answerP[i])) correctRows++;
    }
    // GCSE-style: 4 marks from 8 rows -> 1 mark per 2 correct rows
    return Math.min(4, Math.floor(correctRows / (pairsPerMark || 2)));
  }

  function markQuestion(q, resp) {
    if (q.type === "truth_table_fill") {
      const mode = q.scoring?.mode || "pairs";
      if (mode === "pairs") return truthPairsMark(resp, q.answerP, q.scoring?.pairsPerMark || 2);
      // fallback: raw rows (not GCSE-like)
      let m = 0;
      for (let i = 0; i < q.answerP.length; i++) if (String(resp[i]) === String(q.answerP[i])) m++;
      return Math.min(q.marks, m);
    }

    if (q.type === "gate_boxes") {
      const correct = (q.boxes || []).map(b => b.correct);
      let m = 0;
      for (let i = 0; i < correct.length; i++) if (resp[i] === correct[i]) m++;
      return Math.min(q.marks, m);
    }

    if (q.type === "short_text") {
      const t = normalizeText(resp);
      let m = 0;
      const groups = q.keywords || [];
      // each group = one mark if ANY keyword in group is present (or all? we do "any" for robustness)
      // tweak to "all" if you want stricter marking.
      groups.forEach(() => {});
      for (let i = 0; i < groups.length; i++) {
        const group = groups[i];
        if (!Array.isArray(group)) continue;
        // "soft" rule: if any keyword appears, award the mark
        if (group.some(k => t.includes(normalizeText(k)))) m++;
      }
      return Math.min(q.marks, m);
    }

    if (q.type === "number") {
      return Number(resp) === Number(q.correct) ? 1 : 0;
    }

    return 0;
  }

  function modelText(q) {
    if (q.type === "truth_table_fill") return `Model P: ${q.answerP.join("")}`;
    if (q.type === "gate_boxes") return `Model: ${(q.boxes || []).map(b => b.correct).join(", ")}`;
    if (q.type === "short_text") return `Model answer: ${q.model || ""}`;
    if (q.type === "number") return `Correct: ${q.correct}`;
    return "";
  }

  async function logProgress(challenge_id, score, submission, extra = {}) {
    try {
      await fetch("/api/progress", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          activity_key: "logic_gate_quiz",
          challenge_id,
          score,
          submission,
          ...extra
        })
      });
    } catch {}
  }

  function render() {
    submitted = false;
    $next.disabled = true;
    $submit.disabled = false;

    $progress.textContent = `Question ${idx + 1} / ${questions.length}`;
    $score.textContent = `Score: ${total}`;

    const q = questions[idx];
    $area.innerHTML = "";

    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `
      <h5>${q.prompt} <span class="badge-mini">${q.marks} marks</span></h5>
      <div id="l5-body"></div>
      <div class="mt-2 text-secondary" id="l5-feedback" style="display:none;"></div>
    `;
    $area.appendChild(card);

    const body = card.querySelector("#l5-body");

    if (q.type === "truth_table_fill") {
      const cols = q.columns || ["A", "B", "C", "P"];
      const rows = q.rows || [];

      const table = document.createElement("table");
      table.className = "table table-dark";
      table.innerHTML = `
        <thead><tr>${cols.map(c => `<th>${c}</th>`).join("")}</tr></thead>
        <tbody>
          ${rows.map((r,i)=>`
            <tr>
              <td>${r.A}</td><td>${r.B}</td><td>${r.C}</td>
              <td>
                <input class="form-control form-control-sm text-center l5-p" data-i="${i}" inputmode="numeric" maxlength="1"
                  style="max-width:70px;margin:0 auto;background:#14171a;color:#e9ecef;border:1px solid rgba(255,255,255,0.15);" />
              </td>
            </tr>
          `).join("")}
        </tbody>
      `;
      body.appendChild(table);

      const hint = document.createElement("div");
      hint.className = "text-secondary";
      hint.textContent = "Enter 0 or 1 in the P column.";
      body.appendChild(hint);
    }

    if (q.type === "gate_boxes") {
      const wrap = document.createElement("div");
      wrap.className = "kv";
      wrap.innerHTML = (q.boxes || []).map((b,i)=>`
        <div class="k">${b.label}</div>
        <div>
          <select class="form-select form-select-sm l5-gate" data-i="${i}"
                  style="max-width:260px;background:#14171a;color:#e9ecef;border:1px solid rgba(255,255,255,0.15);">
            <option value="">-- choose --</option>
            <option value="AND">AND</option>
            <option value="OR">OR</option>
            <option value="NOT">NOT</option>
          </select>
        </div>
      `).join("");
      body.appendChild(wrap);
    }

    if (q.type === "short_text") {
      const ta = document.createElement("textarea");
      ta.className = "form-control";
      ta.rows = 4;
      ta.id = "l5-text";
      ta.placeholder = "Write your answer here...";
      ta.style.background = "#14171a";
      ta.style.color = "#e9ecef";
      ta.style.border = "1px solid rgba(255,255,255,0.15)";
      body.appendChild(ta);
    }

    if (q.type === "number") {
      const inp = document.createElement("input");
      inp.className = "form-control";
      inp.id = "l5-num";
      inp.type = "number";
      inp.placeholder = "Enter a number...";
      inp.style.maxWidth = "220px";
      inp.style.background = "#14171a";
      inp.style.color = "#e9ecef";
      inp.style.border = "1px solid rgba(255,255,255,0.15)";
      body.appendChild(inp);
    }
  }

  function getResponseForCurrent() {
    const q = questions[idx];

    if (q.type === "truth_table_fill") {
      return Array.from(document.querySelectorAll(".l5-p"))
        .sort((a,b)=>Number(a.dataset.i)-Number(b.dataset.i))
        .map(x => x.value.trim());
    }

    if (q.type === "gate_boxes") {
      return Array.from(document.querySelectorAll(".l5-gate"))
        .sort((a,b)=>Number(a.dataset.i)-Number(b.dataset.i))
        .map(x => x.value);
    }

    if (q.type === "short_text") return (document.getElementById("l5-text")?.value || "");
    if (q.type === "number") return (document.getElementById("l5-num")?.value || "");

    return null;
  }

  $submit.addEventListener("click", async () => {
    if (submitted) return;
    submitted = true;

    const q = questions[idx];
    const resp = getResponseForCurrent();

    const marks = markQuestion(q, resp);
    total += marks;

    const fb = document.getElementById("l5-feedback");
    fb.style.display = "block";
    const model = modelText(q);
    fb.innerHTML = `<span class="badge-mini">${marks}/${q.marks}</span> &nbsp; ${model}`;

    results.push({
      id: q.id,
      prompt: q.prompt,
      marks,
      outOf: q.marks,
      model,
      response: resp
    });

    $score.textContent = `Score: ${total}`;
    $next.disabled = false;
    $submit.disabled = true;

    await logProgress(q.id, marks, `Level 5: ${marks}/${q.marks}`, {
      level: 5
    });
  });

  $next.addEventListener("click", () => {
    idx++;
    if (idx >= questions.length) return finish();
    render();
  });

  async function finish() {
    document.getElementById("l5-question-area").style.display = "none";
    document.getElementById("l5-submit").style.display = "none";
    document.getElementById("l5-next").style.display = "none";

    const elapsedMs = Date.now() - startTime;

    const fin = document.getElementById("l5-finished");
    fin.style.display = "block";
    document.getElementById("l5-final-score").textContent =
      `${total} total marks • ${(elapsedMs/1000).toFixed(1)}s`;

    const list = document.getElementById("l5-results-list");
    list.innerHTML = "";

    results.forEach((r, i) => {
      const card = document.createElement("div");
      card.className = "result-card";
      card.innerHTML = `
        <h5>Question ${i + 1} <span class="badge-mini">${r.marks}/${r.outOf}</span></h5>
        <div class="text-secondary" style="margin-top:6px;">${r.prompt}</div>
        <div style="margin-top:10px;"><span class="badge-mini">Model</span> ${r.model}</div>
      `;
      list.appendChild(card);
    });

    // summary used for leaderboard + best score + tie-break by time
    await logProgress("level5_summary", total, `Level 5 completed: ${total} marks`, {
      level: 5,
      elapsed_ms: elapsedMs,
      question_count: questions.length
    });
  }

  render();
}




