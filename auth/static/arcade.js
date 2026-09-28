(() => {
  const root = document.querySelector("[data-game]");
  if (!root) return;
  const slug = root.dataset.game;
  const byId = id => document.getElementById(id);
  const stage = { snake: byId("snake-game"), bits: byId("bits-game"), packet: byId("packet-game") };
  const nextButton = byId("next-round");
  const againButton = byId("play-again");
  let pending = false, nextChallenge = null, currentChallenge = null, timer = null, seconds = 25;
  let bits = Array(8).fill(0);

  async function post(action, body = {}) {
    const response = await fetch(`/api/games/${slug}/${action}`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body)
    });
    const data = await response.json().catch(() => ({ error: "The game server returned an unexpected response." }));
    if (!response.ok) throw new Error(data.error || "Could not save this round.");
    return data;
  }

  function showError(error) {
    const feedback = byId("game-feedback");
    feedback.textContent = error.message || String(error);
    feedback.className = "game-feedback incorrect";
  }

  function stopTimer() {
    clearInterval(timer); timer = null; byId("timer").textContent = "";
  }

  function updateBits() {
    const binary = bits.join("");
    const value = parseInt(binary, 2);
    byId("binary-value").textContent = binary;
    byId("decimal-value").textContent = String(value);
    byId("hex-value").textContent = value.toString(16).toUpperCase().padStart(2, "0");
    [...byId("bit-buttons").children].forEach((button, index) => {
      button.classList.toggle("is-on", Boolean(bits[index]));
      button.setAttribute("aria-pressed", String(Boolean(bits[index])));
      button.querySelector("strong").textContent = String(bits[index]);
    });
  }

  function showBits() {
    bits = Array(8).fill(0);
    byId("bit-buttons").replaceChildren();
    [128, 64, 32, 16, 8, 4, 2, 1].forEach((weight, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "bit-switch";
      button.innerHTML = `<span>${weight}</span><strong>0</strong>`;
      button.setAttribute("aria-label", `Toggle ${weight} bit`);
      button.addEventListener("click", () => { bits[index] ^= 1; updateBits(); });
      byId("bit-buttons").append(button);
    });
    updateBits();
    seconds = 25;
    byId("timer").textContent = `${seconds}s`;
    timer = setInterval(() => {
      seconds -= 1;
      byId("timer").textContent = `${seconds}s`;
      if (seconds <= 0) submit(bits.join(""));
    }, 1000);
  }

  function showPacket(challenge) {
    const options = byId("packet-options");
    options.replaceChildren();
    challenge.choices.forEach(choice => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "packet-option";
      button.textContent = choice;
      button.addEventListener("click", () => submit(choice));
      options.append(button);
    });
  }

  const board = byId("snake-canvas"), context = board.getContext("2d");
  const size = 9, tile = 50;
  let snake = [{ x: 4, y: 4 }], direction = { x: 0, y: 0 }, desired = { x: 0, y: 0 };
  let fruits = [], snakeTimer = null;
  const colors = { board: "#102239", grid: "#24435f", snake: "#a8ef63", head: "#55d2f4", fruit: "#173b5b", text: "#fff" };

  function stopSnake() { clearInterval(snakeTimer); snakeTimer = null; }

  function drawSnake() {
    context.fillStyle = colors.board; context.fillRect(0, 0, 450, 450);
    context.strokeStyle = colors.grid;
    for (let i = 0; i <= size; i++) {
      context.beginPath(); context.moveTo(i * tile, 0); context.lineTo(i * tile, 450); context.stroke();
      context.beginPath(); context.moveTo(0, i * tile); context.lineTo(450, i * tile); context.stroke();
    }
    fruits.forEach(fruit => {
      context.fillStyle = colors.fruit; context.fillRect(fruit.x * tile + 3, fruit.y * tile + 3, 44, 44);
      context.fillStyle = colors.text; context.font = "bold 19px system-ui"; context.textAlign = "center";
      context.fillText(fruit.label, fruit.x * tile + 25, fruit.y * tile + 32);
    });
    snake.forEach((segment, index) => {
      context.fillStyle = index === 0 ? colors.head : colors.snake;
      context.fillRect(segment.x * tile + 5, segment.y * tile + 5, 40, 40);
    });
  }

  function resetSnake() {
    snake = [{ x: 4, y: 4 }]; direction = { x: 0, y: 0 }; desired = { x: 0, y: 0 };
    const cells = [];
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
      if (Math.abs(x - 4) + Math.abs(y - 4) > 2) cells.push({ x, y });
    }
    cells.sort(() => Math.random() - 0.5);
    fruits = currentChallenge.choices.map((label, index) => ({ ...cells[index], label }));
    drawSnake();
  }

  function steer(x, y) {
    if (pending || !currentChallenge || slug !== "hex-snake") return;
    if (snake.length > 1 && direction.x === -x && direction.y === -y) return;
    desired = { x, y };
    if (!snakeTimer) snakeTimer = setInterval(stepSnake, 280);
  }

  function stepSnake() {
    if (!desired.x && !desired.y) return;
    direction = desired;
    const head = { x: snake[0].x + direction.x, y: snake[0].y + direction.y };
    if (head.x < 0 || head.y < 0 || head.x >= size || head.y >= size || snake.slice(0, -1).some(part => part.x === head.x && part.y === head.y)) {
      resetSnake(); return;
    }
    const fruit = fruits.find(item => item.x === head.x && item.y === head.y);
    snake.unshift(head);
    if (!fruit) snake.pop();
    drawSnake();
    if (fruit) { stopSnake(); submit(fruit.label); }
  }

  async function submit(answer) {
    if (pending) return;
    pending = true; stopTimer(); stopSnake();
    try {
      const result = await post("answer", { answer });
      byId("run-score").textContent = `Score ${result.score}/100`;
      const feedback = byId("game-feedback");
      feedback.textContent = `${result.correct ? "Correct!" : "Not quite."} ${result.explanation}`;
      feedback.className = `game-feedback ${result.correct ? "correct" : "incorrect"}`;
      if (result.finished) {
        byId("game-prompt").textContent = `Run complete: ${result.score}/100`;
        byId("best-score").textContent = `${result.best}/100`;
        Object.values(stage).forEach(item => { item.hidden = true; });
        againButton.hidden = false;
      } else {
        nextChallenge = result.next;
        nextButton.hidden = false;
      }
    } catch (error) {
      showError(error);
      againButton.hidden = false;
    }
  }

  function showRound(challenge, round) {
    currentChallenge = challenge; nextChallenge = null; pending = false;
    byId("round-count").textContent = `Round ${round}/10`;
    byId("game-prompt").textContent = challenge.prompt;
    byId("round-category").textContent = challenge.category || (slug === "bit-flip" ? "BINARY DEFENCE" : "HEX HUNT");
    byId("game-feedback").textContent = "";
    byId("game-feedback").className = "game-feedback";
    nextButton.hidden = true; againButton.hidden = true;
    Object.values(stage).forEach(item => { item.hidden = true; });
    if (slug === "hex-snake") { stage.snake.hidden = false; resetSnake(); }
    if (slug === "bit-flip") { stage.bits.hidden = false; showBits(); }
    if (slug === "packet-patrol") { stage.packet.hidden = false; showPacket(challenge); }
  }

  async function start() {
    stopTimer(); stopSnake(); pending = true;
    try {
      const data = await post("start");
      byId("run-score").textContent = "Score 0/100";
      showRound(data.challenge, data.round);
    } catch (error) { showError(error); }
  }

  nextButton.addEventListener("click", () => { if (nextChallenge) showRound(nextChallenge, Number(byId("round-count").textContent.match(/\d+/)[0]) + 1); });
  againButton.addEventListener("click", start);
  byId("bits-submit").addEventListener("click", () => submit(bits.join("")));
  document.querySelectorAll("[data-direction]").forEach(button => button.addEventListener("click", () => {
    const vectors = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] };
    steer(...vectors[button.dataset.direction]);
  }));
  document.addEventListener("keydown", event => {
    const vectors = { ArrowUp: [0, -1], ArrowDown: [0, 1], ArrowLeft: [-1, 0], ArrowRight: [1, 0], w: [0, -1], s: [0, 1], a: [-1, 0], d: [1, 0] };
    if (slug === "hex-snake" && vectors[event.key]) { event.preventDefault(); steer(...vectors[event.key]); }
  });
  let touchStart = null;
  board.addEventListener("touchstart", event => { touchStart = [event.touches[0].clientX, event.touches[0].clientY]; }, { passive: true });
  board.addEventListener("touchend", event => {
    if (!touchStart) return;
    const dx = event.changedTouches[0].clientX - touchStart[0], dy = event.changedTouches[0].clientY - touchStart[1];
    if (Math.max(Math.abs(dx), Math.abs(dy)) > 20) steer(Math.abs(dx) > Math.abs(dy) ? Math.sign(dx) : 0, Math.abs(dy) > Math.abs(dx) ? Math.sign(dy) : 0);
    touchStart = null;
  }, { passive: true });
  board.addEventListener("click", () => { if (!snakeTimer && !direction.x && !direction.y) steer(1, 0); });
  start();
})();
