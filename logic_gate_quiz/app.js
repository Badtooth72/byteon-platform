const state = { challenges: [], index: 0, answer: null, score: 0, mode: "core", random: null, token: null };
const $ = id => document.getElementById(id);

async function json(url, options) {
  const response = await fetch(url, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}

async function start() {
  const [session, bank] = await Promise.all([json("/api/session-user"), json("/api/logic-gates/challenges")]);
  if (session.username === "guest") {
    location.href = "/login?next=/logic-gate-quiz/";
    return;
  }
  $("user").textContent = session.username;
  state.challenges = bank.challenges;
  renderStages();
  render();
}

function renderStages() {
  const names = ["Gate basics", "Truth tables", "Circuit builder", "GCSE challenge", "Above the spec"];
  $("stages").innerHTML = names.map((name, index) =>
    `<button class="stage ${index ? "" : "active"}" data-stage="${index + 1}">${index + 1}. ${name}</button>`
  ).join("");
  document.querySelectorAll(".stage").forEach(button => button.onclick = () => {
    const index = state.challenges.findIndex(question => question.stage === +button.dataset.stage);
    if (index >= 0) {
      state.mode = "core";
      state.index = index;
      render();
    }
  });
}

function currentChallenge() {
  return state.mode === "random" ? state.random : state.challenges[state.index];
}

function render() {
  const challenge = currentChallenge();
  state.answer = challenge.type === "truth" ? Array(challenge.inputs.length).fill(0) :
    challenge.type === "circuit" ? Array(challenge.slots).fill("") : null;
  document.querySelectorAll(".stage").forEach(button =>
    button.classList.toggle("active", state.mode === "core" && +button.dataset.stage === challenge.stage)
  );
  $("stage-label").textContent = state.mode === "random" ? "RANDOM CIRCUIT BUILDER" :
    `STAGE ${challenge.stage} · CHALLENGE ${state.index + 1} OF ${state.challenges.length}`;
  $("title").textContent = challenge.title;
  $("prompt").textContent = challenge.prompt;
  $("feedback").textContent = "";
  $("feedback").className = "";
  $("next").hidden = true;
  $("next").textContent = state.mode === "random" ? "Another random circuit" : "Next challenge";
  $("check").hidden = false;
  $("check").disabled = false;

  if (challenge.type === "choice") {
    $("activity").innerHTML = `<div class="options">${challenge.options.map(gate =>
      `<button class="gate" data-value="${gate}"><img class="gate-image" src="gates/${gate.toLowerCase()}.svg" alt=""><span>${gateIcon(gate)} ${gate}</span></button>`
    ).join("")}</div>`;
  } else if (challenge.type === "truth") {
    const headings = ["A", "B", "C"].slice(0, challenge.inputs[0].length);
    $("activity").innerHTML = `${gateReferences(challenge)}<table class="truth"><thead><tr>${headings.map(value => `<th>${value}</th>`).join("")}<th>Output P</th></tr></thead><tbody>${challenge.inputs.map((row, index) =>
      `<tr>${row.map(value => `<td>${value}</td>`).join("")}<td><button class="bit" data-i="${index}">0</button></td></tr>`
    ).join("")}</tbody></table>`;
  } else {
    $("activity").innerHTML = circuitMarkup(challenge);
  }
  bindInputs();
}

function gateIcon(gate) {
  return { AND: "∧", OR: "∨", NOT: "¬", XOR: "⊕", NAND: "⊼" }[gate] || "";
}

function gateReferences(challenge) {
  const gates = challenge.gates || (challenge.gate ? [challenge.gate] : []);
  if (!gates.length) return "";
  return `<div class="question-gates">${gates.map(gate => `<div class="question-gate"><img src="gates/${gate.toLowerCase()}.svg" alt="${gate} gate"><strong>${gateIcon(gate)} ${gate}</strong></div>`).join("")}</div>`;
}

function circuitMarkup(challenge) {
  const threeInput = challenge.topology === "three-input";
  const wires = threeInput ?
    `<path d="M55 75H175L225 120M55 165H175L225 120M390 120H520L585 205M55 325H225M390 300H520L585 205M750 205H945"/>` :
    `<path d="M55 105H180L235 180M55 275H180L235 180M405 180H590M760 180H945"/>`;
  const terminals = threeInput ?
    `<span class="terminal input a">A</span><span class="terminal input b">B</span><span class="terminal input c">C</span>` :
    `<span class="terminal input a">A</span><span class="terminal input b">B</span>`;
  const slots = Array.from({ length: challenge.slots }, (_, index) =>
    `<div class="circuit-slot slot-${index}"><span class="slot-number">Gate ${index + 1}</span><div class="gate-preview"><img class="slot-gate" data-gate="${index}" alt="" hidden><strong data-symbol="${index}">?</strong></div><select aria-label="Choose gate ${index + 1}" data-i="${index}"><option value="">Choose a gate</option>${challenge.options.map(gate => `<option value="${gate}">${gateIcon(gate)} ${gate}</option>`).join("")}</select></div>`
  ).join("");
  return `<div class="circuit-board ${threeInput ? "three-input" : "two-stage"}"><svg class="circuit-wires" viewBox="0 0 1000 400" preserveAspectRatio="none" aria-hidden="true">${wires}</svg>${terminals}${slots}<span class="terminal output">P</span></div>`;
}

function bindInputs() {
  document.querySelectorAll(".gate").forEach(button => button.onclick = () => {
    document.querySelectorAll(".gate").forEach(item => item.classList.remove("selected"));
    button.classList.add("selected");
    state.answer = button.dataset.value;
  });
  document.querySelectorAll(".bit").forEach(button => button.onclick = () => {
    const index = +button.dataset.i;
    state.answer[index] = state.answer[index] ? 0 : 1;
    button.textContent = state.answer[index];
  });
  document.querySelectorAll("select").forEach(select => select.onchange = () => {
    const index = +select.dataset.i;
    const image = document.querySelector(`[data-gate="${index}"]`);
    const symbol = document.querySelector(`[data-symbol="${index}"]`);
    state.answer[index] = select.value;
    if (select.value) {
      image.src = `gates/${select.value.toLowerCase()}.svg`;
      image.alt = `${select.value} gate`;
      image.hidden = false;
      symbol.textContent = gateIcon(select.value);
    } else {
      image.hidden = true;
      symbol.textContent = "?";
    }
  });
}

$("check").onclick = async () => {
  const challenge = currentChallenge();
  if (state.answer === null || Array.isArray(state.answer) && state.answer.some(value => value === "")) {
    $("feedback").textContent = "Complete every part before checking.";
    $("feedback").className = "incorrect";
    return;
  }
  try {
    const random = state.mode === "random";
    const result = await json(random ? "/api/logic-gates/random-attempt" : "/api/logic-gates/attempt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(random ? { token: state.token, response: state.answer } : { challenge_id: challenge.id, response: state.answer })
    });
    $("feedback").textContent = `${result.correct ? "Correct." : "Have another look."} ${result.explanation}`;
    $("feedback").className = result.correct ? "correct" : "incorrect";
    if (result.correct) {
      if (!random) {
        state.score++;
        $("score").textContent = state.score;
      }
      $("check").disabled = true;
      $("next").hidden = false;
    }
  } catch (error) {
    $("feedback").textContent = error.message;
    $("feedback").className = "incorrect";
  }
};

$("next").onclick = () => {
  if (state.mode === "random") return loadRandom();
  if (state.index === state.challenges.length - 1) return showCompletion();
  state.index++;
  render();
};

function showCompletion() {
  document.querySelectorAll(".stage").forEach(button => button.classList.remove("active"));
  $("stage-label").textContent = "LOGIC LAB COMPLETE";
  $("title").textContent = "Well done!";
  $("prompt").textContent = `You scored ${state.score} out of ${state.challenges.length}.`;
  $("activity").innerHTML = `<div class="completion"><div class="completion-score"><strong>${state.score}</strong><span>/ ${state.challenges.length}</span></div><p>Your attempts have been saved to your Byteon progress record.</p><div class="completion-actions"><a href="/dashboard">Return to dashboard</a><button id="random-challenge" type="button">Build a random circuit</button></div></div>`;
  $("feedback").textContent = "";
  $("check").hidden = true;
  $("next").hidden = true;
  $("random-challenge").onclick = loadRandom;
}

async function loadRandom() {
  try {
    const result = await json("/api/logic-gates/random-circuit");
    state.mode = "random";
    state.random = result.challenge;
    state.token = result.token;
    render();
  } catch (error) {
    $("feedback").textContent = error.message;
    $("feedback").className = "incorrect";
  }
}

document.addEventListener("keydown", event => {
  if (event.key === "Enter" && !$("check").hidden) $("check").click();
  const number = +event.key;
  if (number > 0 && number < 5) [...document.querySelectorAll(".gate,.bit")][number - 1]?.click();
});

start().catch(error => {
  $("title").textContent = "Logic Lab unavailable";
  $("prompt").textContent = error.message;
});
