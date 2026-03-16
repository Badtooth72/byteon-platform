let questions = [];
let current = 0;
let score = 0;
let times = [];
let startTime;
let gameStartTime;
let mode = "easy";
let timerEnabled = true;
let username = "guest";
let reviewModal;
const binaryBits = [0, 0, 0, 0, 0, 0, 0, 0];

document.addEventListener("DOMContentLoaded", () => {
  const modalEl = document.getElementById("reviewModal");
  if (modalEl) reviewModal = new bootstrap.Modal(modalEl);

  fetch("/auth/api/session-user")
    .then(res => res.json())
    .then(data => {
      username = data.username || "guest";
      console.log("Logged in as:", username);
      fetchPersonalBest();
    })
    .catch(err => console.error("❌ Failed to fetch session user:", err));
});

function fetchPersonalBest() {
  fetch("/auth/api/best-score")
    .then(res => res.json())
    .then(data => {
      if (data?.score !== undefined) {
        const bestBox = document.getElementById("personal-best");
        bestBox?.classList.remove("d-none");
        document.getElementById("best-details").innerHTML =
          `Score: <strong>${data.score}</strong> | Mode: <strong>${data.mode}</strong> | Time: <strong>${data.time}s</strong>`;
      }
    })
    .catch(err => console.error("❌ Error fetching session/best score", err));
}

function updateBinaryTable(binaryString) {
  const padded = binaryString.padStart(8, "0").slice(-8);
  const row = document.getElementById("binary-display")?.children;
  if (!row) return;
  for (let i = 0; i < 8; i++) {
    row[i].textContent = padded[i];
    row[i].style.backgroundColor = padded[i] === "1" ? "#198754" : "transparent";
  }
}

function updateDecimalOutput() {
  const decimalValue = parseInt(binaryBits.join(""), 2);
  const el = document.getElementById("decimal-output");
  if (el) el.textContent = `Decimal Value: ${decimalValue}`;
}

function setupBinaryButtons() {
  const values = [128, 64, 32, 16, 8, 4, 2, 1];
  const container = document.getElementById("binary-buttons");
  if (!container) return;

  container.innerHTML = "";
  binaryBits.fill(0);
  updateDecimalOutput();

  values.forEach((val, i) => {
    const btn = document.createElement("button");
    btn.textContent = "0";
    btn.className = "btn btn-outline-light btn-sm";
    btn.style.minWidth = "32px";
    btn.onclick = () => {
      binaryBits[i] = binaryBits[i] === 1 ? 0 : 1;
      btn.textContent = binaryBits[i];
      btn.className = binaryBits[i]
        ? "btn btn-success btn-sm"
        : "btn btn-outline-light btn-sm";
      updateDecimalOutput();
    };
    const cell = document.createElement("td");
    cell.appendChild(btn);
    container.appendChild(cell);
  });
}

function insertBinary() {
  const binaryStr = binaryBits.join("");
  document.getElementById("answer-input").value = binaryStr;
  updateBinaryTable(binaryStr);
}

function startGame() {
  mode = document.getElementById("mode").value;
  timerEnabled = document.getElementById("timer-toggle")?.checked ?? true;

  let url = `api/questions?mode=${mode}`;
  if (mode === "custom") {
    const checks = document.querySelectorAll("#custom-options input[type=checkbox]:checked");
    const types = Array.from(checks).map(c => c.value);
    const count = parseInt(document.getElementById("custom-count").value || "10");

    if (types.length === 0) {
      alert("❌ Please select at least one conversion type.");
      return;
    }
    if (isNaN(count) || count < 1 || count > 30) {
      alert("❌ Please enter a number of questions between 1 and 30.");
      return;
    }

    url += `&count=${count}&types=${types.join(",")}`;
  }

  fetch(url)
    .then(res => res.json())
    .then(data => {
      questions = data.questions;
      current = 0;
      score = 0;
      times = [];
      gameStartTime = Date.now();

      document.getElementById("setup-section").style.display = "none";
      document.getElementById("game-section").style.display = "block";

      const squareContainer = document.getElementById("feedback-squares");
      squareContainer.innerHTML = "";
      for (let i = 0; i < questions.length; i++) {
        const sq = document.createElement("div");
        sq.classList.add("feedback-square");
        sq.title = `Question ${i + 1}`;
        squareContainer.appendChild(sq);
      }

      if (mode === "easy") {
        document.getElementById("binary-table").style.display = "block";
        setupBinaryButtons();
      } else {
        document.getElementById("binary-table").style.display = "none";
      }

      updateGameTimer();
      nextQuestion();
    })
    .catch(err => {
      alert("❌ Error starting game: " + err.message);
    });
}

function updateGameTimer() {
  const timerBox = document.getElementById("timer-box");
  const timerText = document.getElementById("timer");

  if (!timerEnabled) {
    timerBox.classList.add("d-none");
    return;
  }

  timerBox.classList.remove("d-none");
  window.timerInterval = setInterval(() => {
    const elapsed = (Date.now() - gameStartTime) / 1000;
    const seconds = Math.floor(elapsed);

    if (seconds < 60) {
      timerText.textContent = `${seconds}s`;
      timerBox.style.color = "#00ff7f";
    } else {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      timerText.textContent = `${mins}:${secs.toString().padStart(2, "0")}`;
      timerBox.style.color = seconds < 120 ? "#ffc107" : "#dc3545";
    }
  }, 1000);
}

function nextQuestion() {
  if (current >= questions.length) {
    endGame();
    return;
  }

  const inputEl = document.getElementById("answer-input");
  document.getElementById("question-box").textContent = `Q${current + 1}: ${questions[current].question}`;
  inputEl.value = "";
  inputEl.focus();

  const handleKey = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      inputEl.removeEventListener("keydown", handleKey);
      submitAnswer();
    }
  };
  inputEl.addEventListener("keydown", handleKey);

  inputEl.addEventListener("input", (e) => {
    const val = e.target.value.trim();
    if (/^[01]+$/.test(val)) {
      updateBinaryTable(val);
    } else {
      updateBinaryTable("");
    }
  });

  startTime = Date.now();
}

function submitAnswer() {
  const input = document.getElementById("answer-input").value.trim().toLowerCase();
  const correct = questions[current].answer.toLowerCase();
  const timeTaken = (Date.now() - startTime) / 1000;

  const isCorrect = parseInt(input, 2) === parseInt(correct, 2);
  times.push(timeTaken);
  if (isCorrect) score++;

  const square = document.getElementById("feedback-squares").children[current];
  square.classList.add(isCorrect ? "feedback-correct" : "feedback-wrong");

  const qIndex = current;
  square.onclick = () => {
    const q = questions[qIndex];
    const wasCorrect = square.classList.contains("feedback-correct");
    const html = `
      <p><strong>Question ${qIndex + 1}:</strong></p>
      <p>${q.question}</p>
      <hr/>
      ${wasCorrect
        ? `<p class="text-success">✅ You got it right!</p>`
        : `<p class="text-danger">❌ You got it wrong.</p><p>Correct answer: <code>${q.answer}</code></p>`}
      <p><span class="text-muted">Time taken: ${Math.round(times[qIndex])}s</span></p>
    `;
    document.getElementById("modal-body-content").innerHTML = html;
    reviewModal?.show();
  };

  current++;
  nextQuestion();
}

function endGame() {
  clearInterval(window.timerInterval);
  document.getElementById("binary-table").style.display = "none";
  document.getElementById("game-section").style.display = "none";
  document.getElementById("result-box").style.display = "block";

  const correctTimes = times.filter((_, i) =>
    document.getElementById("feedback-squares").children[i].classList.contains("feedback-correct")
  );

  const total = correctTimes.reduce((a, b) => a + b, 0);
  const fastest = correctTimes.length ? Math.min(...correctTimes) : 0;

  document.getElementById("final-score").textContent = `✅ Score: ${score} / ${questions.length}`;
  document.getElementById("timing-summary").textContent =
    `Correct answer time — Total: ${total.toFixed(2)}s | Fastest: ${fastest.toFixed(2)}s`;

  submitScore();
}

async function submitScore() {
  try {
    const userRes = await fetch("/auth/api/user");
    const user = await userRes.json();

    const payload = {
      username,
      mode,
      score,
      times
    };

    if (user.forename) payload.forename = user.forename;
    if (user.surname) payload.surname = user.surname;
    if (user.class_name) payload.class_name = user.class_name;
    if (user.current_yeargroup) payload.current_yeargroup = user.current_yeargroup;

    const res = await fetch("api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await res.json();
    console.log("✅ Score submitted:", result);
  } catch (err) {
    console.error("❌ Failed to submit score:", err);
  }
}

function showReviewModal() {
  const container = document.getElementById("review-modal-body");
  container.innerHTML = "";

  questions.forEach((q, i) => {
    const isCorrect = document.getElementById("feedback-squares").children[i].classList.contains("feedback-correct");
    const timeTaken = times[i] !== undefined ? Math.round(times[i]) : null;
    const box = document.createElement("div");
    box.classList.add("mb-3", "p-3", "rounded");
    box.style.backgroundColor = isCorrect ? "#d4edda" : "#f8d7da";

    box.innerHTML = `
      <strong>Q${i + 1}:</strong> ${q.question}<br/>
      ${isCorrect
        ? `<span class="text-success fw-bold">✅ You got it right!</span>`
        : `<span class="text-danger fw-bold">❌ You got it wrong</span><br/>
           <span>Correct answer: <code>${q.answer}</code></span>`}
      <br/><span class="text-muted">Time taken: ${timeTaken}s</span>
    `;
    container.appendChild(box);
  });

  reviewModal?.show();
}
