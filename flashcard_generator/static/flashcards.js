const BASE = "/flashcards";

function byId(id) {
  return document.getElementById(id);
}

function clone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

function normaliseText(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^\w\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function parseAnswerPatterns(raw) {
  return String(raw || "")
    .split("|")
    .map(part => part.trim())
    .filter(Boolean)
    .map(part => {
      if (part.includes(",")) {
        return {
          type: "keywords",
          tokens: part.split(",").map(token => normaliseText(token)).filter(Boolean)
        };
      }
      return {
        type: "exact",
        value: normaliseText(part)
      };
    });
}

function answerMatches(studentAnswer, acceptedRaw, { caseSensitive = false } = {}) {
  const prepared = caseSensitive
    ? String(studentAnswer || "").replace(/\s+/g, " ").trim()
    : normaliseText(studentAnswer);

  const patterns = parseAnswerPatterns(acceptedRaw);
  if (!patterns.length) return false;

  return patterns.some(pattern => {
    if (pattern.type === "exact") {
      return prepared === pattern.value || prepared.includes(pattern.value);
    }
    return pattern.tokens.every(token => prepared.includes(token));
  });
}

(function setupEditor() {
  const editorRoot = byId("flashcard-editor-root");
  if (!editorRoot) return;

  const minCards = Number(window.minFlashcards || 5);
  const cardsContainer = byId("cards-container");
  const selectedKeywordsBox = byId("selected-keywords-box");
  const statusBox = byId("editor-status");

  const setTitleInput = byId("set-title");
  const setDescriptionInput = byId("set-description");
  const saveSetBtn = byId("save-set-btn");
  const shareSetBtn = byId("share-set-btn");
  const publicToggle = byId("public-toggle");
  const shareBox = byId("share-box");
  const shareLinkInput = byId("share-link");
  const copyShareLinkBtn = byId("copy-share-link");

  const viewSetLink = byId("view-set-link");
  const playSetLink = byId("play-set-link");
  const printSetLink = byId("print-set-link");

  const addStandardCardBtn = byId("add-standard-card");
  const addQuizCardBtn = byId("add-quiz-card");
  const addClozeCardBtn = byId("add-cloze-card");
  const addDiagramCardBtn = byId("add-diagram-card");

  let state = clone(window.initialFlashcardSet || {});

  function blankCard(position, type = "standard") {
    const templates = {
      standard: {
        keyword: "",
        front_text: "",
        back_text: "",
        hint: "",
        word_bank: "",
        image_front: "",
        image_back: "",
        notes: ""
      },
      quiz: {
        keyword: "",
        front_text: "",
        back_text: "",
        hint: "",
        word_bank: "",
        image_front: "",
        image_back: "",
        notes: ""
      },
      cloze: {
        keyword: "",
        front_text: "The CPU contains the ____ and the Control Unit.",
        back_text: "ALU",
        hint: "",
        word_bank: "ALU, cache, register",
        image_front: "",
        image_back: "",
        notes: ""
      },
      diagram: {
        keyword: "",
        front_text: "",
        back_text: "",
        hint: "",
        word_bank: "",
        image_front: "",
        image_back: "",
        notes: ""
      }
    };
    return { position, card_type: type, ...templates[type] };
  }

  function sanitiseState() {
    state.id = state.id || null;
    state.title = state.title || "New Flashcard Set";
    state.description = state.description || "";
    state.selected_keywords = Array.isArray(state.selected_keywords) ? state.selected_keywords : [];
    state.cards = Array.isArray(state.cards) ? state.cards : [];

    while (state.cards.length < minCards) {
      state.cards.push(blankCard(state.cards.length + 1));
    }

    state.cards = state.cards.map((card, index) => ({
      ...blankCard(index + 1, card.card_type || "standard"),
      ...card,
      position: index + 1
    }));
  }

  function setStatus(message, kind = "neutral") {
    if (!statusBox) return;
    statusBox.textContent = message;
    statusBox.classList.remove("status-success", "status-error", "status-info");
    if (kind === "success") statusBox.classList.add("status-success");
    if (kind === "error") statusBox.classList.add("status-error");
    if (kind === "info") statusBox.classList.add("status-info");
  }

  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function updateTopFields() {
    if (setTitleInput) setTitleInput.value = state.title || "";
    if (setDescriptionInput) setDescriptionInput.value = state.description || "";
    if (publicToggle) publicToggle.checked = !!state.is_public;

    if (selectedKeywordsBox) {
      selectedKeywordsBox.innerHTML = "";
      if (!state.selected_keywords.length) {
        selectedKeywordsBox.innerHTML = `<span class="badge text-bg-secondary">No keywords selected</span>`;
      } else {
        state.selected_keywords.forEach(keyword => {
          const badge = document.createElement("span");
          badge.className = "badge text-bg-primary";
          badge.textContent = keyword;
          selectedKeywordsBox.appendChild(badge);
        });
      }
    }

    updateActionLinks();
  }

  function updateActionLinks() {
    if (!viewSetLink || !playSetLink || !printSetLink) return;

    if (!state.id) {
      [viewSetLink, playSetLink, printSetLink].forEach(link => {
        link.href = "#";
        link.classList.add("disabled");
      });
      return;
    }

    viewSetLink.href = `${BASE}/set/${state.id}`;
    playSetLink.href = `${BASE}/play/${state.id}`;
    printSetLink.href = `${BASE}/print/${state.id}`;
    [viewSetLink, playSetLink, printSetLink].forEach(link => link.classList.remove("disabled"));
  }

  function typeOptions(selected) {
    return [
      ["standard", "Standard"],
      ["quiz", "Quiz"],
      ["cloze", "Fill in the blanks"],
      ["diagram", "Diagram / image prompt"]
    ].map(([value, label]) => `<option value="${value}" ${selected === value ? "selected" : ""}>${label}</option>`).join("");
  }

  function imageField(card, index, field, label) {
    const value = card[field] || "";
    return `
      <div class="col-md-6">
        <label class="form-label">${label}</label>
        <div class="image-paste-zone" data-image-field="${field}" data-card-index="${index}" tabindex="0">
          ${value ? `<img src="${escapeHtml(value)}" class="pasted-preview" alt="Card image preview">` : `<div class="image-paste-help">Paste image here or click to upload</div>`}
          <input type="file" class="image-upload-input d-none" accept="image/*">
        </div>
      </div>
    `;
  }

  function renderFields(card, index) {
    if (card.card_type === "standard") {
      return `
        <div class="col-md-4"><label class="form-label">Term / keyword</label><input class="form-control" data-field="keyword" value="${escapeHtml(card.keyword)}" placeholder="e.g. CPU"></div>
        <div class="col-md-4"><label class="form-label">Card type</label><select class="form-select" data-field="card_type">${typeOptions(card.card_type)}</select></div>
        <div class="col-md-4"><label class="form-label">Hint</label><input class="form-control" data-field="hint" value="${escapeHtml(card.hint)}" placeholder="e.g. It's three words"></div>
        <div class="col-md-6"><label class="form-label">Prompt / keyword</label><textarea class="form-control" rows="3" data-field="front_text" placeholder="e.g. CPU">${escapeHtml(card.front_text)}</textarea></div>
        <div class="col-md-6"><label class="form-label">Meaning / answer</label><textarea class="form-control" rows="3" data-field="back_text" placeholder="e.g. Central Processing Unit">${escapeHtml(card.back_text)}</textarea></div>
        ${imageField(card, index, "image_front", "Front image (optional)")}
        ${imageField(card, index, "image_back", "Back image (optional)")}
        <div class="col-12"><label class="form-label">Teacher notes</label><input class="form-control" data-field="notes" value="${escapeHtml(card.notes)}" placeholder="Author-only notes"></div>
      `;
    }

    if (card.card_type === "quiz") {
      return `
        <div class="col-md-6"><label class="form-label">Question</label><textarea class="form-control" rows="3" data-field="front_text" placeholder="e.g. What does CPU stand for?">${escapeHtml(card.front_text)}</textarea></div>
        <div class="col-md-6"><label class="form-label">Accepted answer(s) or keywords</label><textarea class="form-control" rows="3" data-field="back_text" placeholder="cpu | central processing unit | central,processing,unit">${escapeHtml(card.back_text)}</textarea><div class="form-text">Use | for alternatives. Use commas for required keywords in any order.</div></div>
        <div class="col-md-6"><label class="form-label">Hint</label><input class="form-control" data-field="hint" value="${escapeHtml(card.hint)}" placeholder="Optional hint"></div>
        <div class="col-md-6"><label class="form-label">Card type</label><select class="form-select" data-field="card_type">${typeOptions(card.card_type)}</select></div>
        <div class="col-12"><label class="form-label">Teacher notes</label><input class="form-control" data-field="notes" value="${escapeHtml(card.notes)}" placeholder="Author-only notes"></div>
      `;
    }

    if (card.card_type === "cloze") {
      return `
        <div class="col-md-6"><label class="form-label">Sentence with blanks</label><textarea class="form-control" rows="3" data-field="front_text" placeholder="The CPU contains the ____ and the Control Unit.">${escapeHtml(card.front_text)}</textarea></div>
        <div class="col-md-6"><label class="form-label">Accepted answer(s)</label><textarea class="form-control" rows="3" data-field="back_text" placeholder="ALU | arithmetic logic unit">${escapeHtml(card.back_text)}</textarea><div class="form-text">Not case sensitive in play mode.</div></div>
        <div class="col-md-6"><label class="form-label">Word bank</label><input class="form-control" data-field="word_bank" value="${escapeHtml(card.word_bank)}" placeholder="ALU, register, cache"></div>
        <div class="col-md-3"><label class="form-label">Hint</label><input class="form-control" data-field="hint" value="${escapeHtml(card.hint)}" placeholder="Optional hint"></div>
        <div class="col-md-3"><label class="form-label">Card type</label><select class="form-select" data-field="card_type">${typeOptions(card.card_type)}</select></div>
        <div class="col-12"><label class="form-label">Teacher notes</label><input class="form-control" data-field="notes" value="${escapeHtml(card.notes)}" placeholder="Author-only notes"></div>
      `;
    }

    return `
      <div class="col-md-6"><label class="form-label">Task / question</label><textarea class="form-control" rows="3" data-field="front_text" placeholder="e.g. Label the ALU in this diagram">${escapeHtml(card.front_text)}</textarea></div>
      <div class="col-md-6"><label class="form-label">Model answer</label><textarea class="form-control" rows="3" data-field="back_text" placeholder="e.g. The ALU performs arithmetic and logic operations">${escapeHtml(card.back_text)}</textarea></div>
      ${imageField(card, index, "image_front", "Paste or upload image")}
      <div class="col-md-3"><label class="form-label">Hint</label><input class="form-control" data-field="hint" value="${escapeHtml(card.hint)}" placeholder="Optional hint"></div>
      <div class="col-md-3"><label class="form-label">Card type</label><select class="form-select" data-field="card_type">${typeOptions(card.card_type)}</select></div>
      <div class="col-12"><label class="form-label">Teacher notes</label><input class="form-control" data-field="notes" value="${escapeHtml(card.notes)}" placeholder="Author-only notes"></div>
    `;
  }

  function bindImageZones() {
    document.querySelectorAll(".image-paste-zone").forEach(zone => {
      if (zone.dataset.bound === "yes") return;
      zone.dataset.bound = "yes";
      const input = zone.querySelector(".image-upload-input");

      zone.addEventListener("click", () => input.click());
      zone.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          input.click();
        }
      });

      input.addEventListener("change", event => {
        const file = event.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
          const index = Number(zone.dataset.cardIndex);
          const field = zone.dataset.imageField;
          state.cards[index][field] = reader.result;
          renderCards();
          setStatus("Image added", "info");
        };
        reader.readAsDataURL(file);
      });

      zone.addEventListener("paste", event => {
        const items = [...(event.clipboardData?.items || [])];
        const imageItem = items.find(item => item.type.startsWith("image/"));
        if (!imageItem) return;
        event.preventDefault();
        const file = imageItem.getAsFile();
        const reader = new FileReader();
        reader.onload = () => {
          const index = Number(zone.dataset.cardIndex);
          const field = zone.dataset.imageField;
          state.cards[index][field] = reader.result;
          renderCards();
          setStatus("Image pasted", "info");
        };
        reader.readAsDataURL(file);
      });
    });
  }

  function renderCards() {
    cardsContainer.innerHTML = "";

    state.cards.forEach((card, index) => {
      const wrapper = document.createElement("section");
      wrapper.className = "card glass-card editor-card";
      wrapper.innerHTML = `
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center gap-2 mb-3">
            <div><h2 class="h5 mb-1">Card ${index + 1}</h2><div class="text-light-emphasis small">${card.card_type}</div></div>
            <div class="btn-group btn-group-sm">
              <button type="button" class="btn btn-outline-light move-up-btn">↑</button>
              <button type="button" class="btn btn-outline-light move-down-btn">↓</button>
              <button type="button" class="btn btn-outline-light duplicate-card-btn">Duplicate</button>
              <button type="button" class="btn btn-outline-danger remove-card-btn">Remove</button>
            </div>
          </div>
          <div class="row g-3">${renderFields(card, index)}</div>
        </div>
      `;
      cardsContainer.appendChild(wrapper);

      wrapper.querySelectorAll("[data-field]").forEach(input => {
        input.addEventListener("input", event => {
          const field = event.target.dataset.field;
          state.cards[index][field] = event.target.value;
          if (field === "card_type") {
            const next = event.target.value;
            state.cards[index] = { ...blankCard(index + 1, next), ...state.cards[index], card_type: next };
            renderCards();
          } else {
            setStatus("Unsaved changes");
          }
        });
      });

      wrapper.querySelector(".move-up-btn").addEventListener("click", () => {
        if (index === 0) return;
        [state.cards[index - 1], state.cards[index]] = [state.cards[index], state.cards[index - 1]];
        state.cards.forEach((item, idx) => item.position = idx + 1);
        renderCards();
        setStatus("Card moved", "info");
      });

      wrapper.querySelector(".move-down-btn").addEventListener("click", () => {
        if (index >= state.cards.length - 1) return;
        [state.cards[index + 1], state.cards[index]] = [state.cards[index], state.cards[index + 1]];
        state.cards.forEach((item, idx) => item.position = idx + 1);
        renderCards();
        setStatus("Card moved", "info");
      });

      wrapper.querySelector(".duplicate-card-btn").addEventListener("click", () => {
        state.cards.splice(index + 1, 0, clone({ ...state.cards[index], position: index + 2 }));
        state.cards.forEach((item, idx) => item.position = idx + 1);
        renderCards();
        setStatus("Card duplicated", "info");
      });

      wrapper.querySelector(".remove-card-btn").addEventListener("click", () => {
        if (state.cards.length <= minCards) {
          setStatus(`The set must keep at least ${minCards} cards.`, "error");
          return;
        }
        state.cards.splice(index, 1);
        state.cards.forEach((item, idx) => item.position = idx + 1);
        renderCards();
        setStatus("Card removed", "info");
      });
    });

    bindImageZones();
  }

  async function saveSet() {
    state.title = setTitleInput?.value?.trim() || "Untitled set";
    state.description = setDescriptionInput?.value?.trim() || "";

    const response = await fetch(`${BASE}/api/sets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({
        id: state.id,
        title: state.title,
        description: state.description,
        selected_keywords: state.selected_keywords,
        cards: state.cards
      })
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || `Save failed (${response.status})`);

    state.id = payload.set?.id || payload.id || state.id;
    updateActionLinks();
    setStatus("Set saved", "success");
  }

  async function shareSet() {
    if (!state.id) {
      setStatus("Save the set first before creating a share link.", "error");
      return;
    }

    const response = await fetch(`${BASE}/api/sets/${state.id}/share`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ public: !!publicToggle?.checked })
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || `Share failed (${response.status})`);

    state.share_code = payload.share_code || "";
    state.is_public = !!payload.is_public;

    if (shareBox) shareBox.classList.remove("d-none");
    if (shareLinkInput) shareLinkInput.value = payload.share_url || `${window.location.origin}${BASE}/shared/${state.share_code}`;
    setStatus("Share link updated", "success");
  }

  function addCard(type) {
    state.cards.push(blankCard(state.cards.length + 1, type));
    renderCards();
    setStatus("Card added", "info");
  }

  sanitiseState();
  updateTopFields();
  renderCards();

  setTitleInput?.addEventListener("input", () => { state.title = setTitleInput.value; setStatus("Unsaved changes"); });
  setDescriptionInput?.addEventListener("input", () => { state.description = setDescriptionInput.value; setStatus("Unsaved changes"); });
  saveSetBtn?.addEventListener("click", async () => { try { await saveSet(); } catch (err) { setStatus(err.message, "error"); } });
  shareSetBtn?.addEventListener("click", async () => { try { await shareSet(); } catch (err) { setStatus(err.message, "error"); } });
  copyShareLinkBtn?.addEventListener("click", async () => {
    if (!shareLinkInput?.value) return;
    await navigator.clipboard.writeText(shareLinkInput.value);
    setStatus("Share link copied", "info");
  });
  publicToggle?.addEventListener("change", () => { state.is_public = publicToggle.checked; setStatus("Unsaved share setting", "info"); });
  addStandardCardBtn?.addEventListener("click", () => addCard("standard"));
  addQuizCardBtn?.addEventListener("click", () => addCard("quiz"));
  addClozeCardBtn?.addEventListener("click", () => addCard("cloze"));
  addDiagramCardBtn?.addEventListener("click", () => addCard("diagram"));
})();

(function setupPlayMode() {
  const root = byId("play-root");
  if (!root) return;

  const data = window.playSetData || {};
  const cards = Array.isArray(data.cards) ? data.cards : [];
  let index = 0;
  let score = 0;
  let scoredCards = new Set();
  let flipped = false;

  const shell = byId("play-card-shell");
  const progress = byId("play-progress");
  const scoreBox = byId("play-score");
  const prevBtn = byId("prev-card");
  const nextBtn = byId("next-card");
  const flipBtn = byId("flip-card");
  const checkBtn = byId("check-answer");
  const fullscreenBtn = byId("fullscreen-toggle");
  const themeBtn = byId("theme-toggle");

  function updateMeta() {
    progress.textContent = `Card ${index + 1} / ${cards.length}`;
    scoreBox.textContent = `Score ${score}`;
  }

  function currentCard() {
    return cards[index] || {};
  }

  function standardOrDiagramCard(card) {
    const frontImage = card.image_front ? `<img class="play-image" src="${card.image_front}" alt="Card image">` : "";
    const backImage = card.image_back ? `<img class="play-image" src="${card.image_back}" alt="Card answer image">` : "";

    return `
      <div class="flip-card ${flipped ? "is-flipped" : ""}">
        <div class="flip-card-inner">
          <section class="flip-face flip-front">
            <div class="play-card-type">${card.card_type}</div>
            ${frontImage}
            <h2>${card.front_text || card.keyword || "Untitled card"}</h2>
            ${card.hint ? `<div class="play-hint">Hint: ${card.hint}</div>` : ""}
          </section>
          <section class="flip-face flip-back">
            <div class="play-card-type">Answer</div>
            ${backImage}
            <h2>${card.back_text || "No answer added yet."}</h2>
          </section>
        </div>
      </div>
    `;
  }

  function quizOrClozeCard(card) {
    const help = card.card_type === "quiz"
      ? "Keyword matching enabled. Variations are allowed."
      : `Not case sensitive. ${card.word_bank ? `Word bank: ${card.word_bank}` : ""}`;

    return `
      <section class="play-response-card">
        <div class="play-card-type">${card.card_type}</div>
        <h2>${card.front_text || card.keyword || "Untitled card"}</h2>
        ${card.hint ? `<div class="play-hint">Hint: ${card.hint}</div>` : ""}
        ${card.word_bank && card.card_type === "cloze" ? `<div class="play-word-bank">Word bank: ${card.word_bank}</div>` : ""}
        <input id="student-answer" class="form-control form-control-lg play-answer-input" placeholder="${card.card_type === "quiz" ? "Type your answer" : "Type the missing word or phrase"}">
        <div id="play-feedback" class="play-feedback"></div>
        <div id="play-model-answer" class="play-model-answer d-none"><strong>Accepted answer(s):</strong> ${card.back_text || "No answer added"}</div>
        <div class="play-help">${help}</div>
      </section>
    `;
  }

  function render() {
    const card = currentCard();
    flipped = false;
    const isTyped = card.card_type === "quiz" || card.card_type === "cloze";
    shell.innerHTML = isTyped ? quizOrClozeCard(card) : standardOrDiagramCard(card);
    flipBtn.classList.toggle("d-none", isTyped);
    checkBtn.classList.toggle("d-none", !isTyped);
    updateMeta();

    const input = byId("student-answer");
    if (input) {
      input.addEventListener("keydown", event => {
        if (event.key === "Enter") {
          event.preventDefault();
          checkCurrentAnswer();
        }
      });
      input.focus();
    }
  }

  function checkCurrentAnswer() {
    const card = currentCard();
    const input = byId("student-answer");
    const feedback = byId("play-feedback");
    const answerBox = byId("play-model-answer");
    if (!input || !feedback) return;

    const correct = answerMatches(input.value, card.back_text, { caseSensitive: false });
    feedback.textContent = correct ? "Correct" : "Not quite right";
    feedback.className = `play-feedback ${correct ? "correct" : "incorrect"}`;
    answerBox?.classList.remove("d-none");

    if (correct && !scoredCards.has(index)) {
      scoredCards.add(index);
      score += 1;
      updateMeta();
    }
  }

  prevBtn?.addEventListener("click", () => {
    if (index > 0) index -= 1;
    render();
  });

  nextBtn?.addEventListener("click", () => {
    if (index < cards.length - 1) index += 1;
    render();
  });

  flipBtn?.addEventListener("click", () => {
    flipped = !flipped;
    const flipCard = shell.querySelector(".flip-card");
    if (flipCard) flipCard.classList.toggle("is-flipped", flipped);
  });

  checkBtn?.addEventListener("click", () => checkCurrentAnswer());

  fullscreenBtn?.addEventListener("click", async () => {
    const element = document.documentElement;
    if (!document.fullscreenElement) await element.requestFullscreen?.();
    else await document.exitFullscreen?.();
  });

  themeBtn?.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    document.body.setAttribute("data-theme", next);
    localStorage.setItem("byteon-theme", next);
  });

  render();
})();
