const BASE = "/flashcards";

const editorRoot = document.getElementById("flashcard-editor-root");
const cardsContainer = document.getElementById("cards-container");
const selectedKeywordsBox = document.getElementById("selected-keywords-box");
const statusBox = document.getElementById("editor-status");

const setTitleInput = document.getElementById("set-title");
const setDescriptionInput = document.getElementById("set-description");
const saveSetBtn = document.getElementById("save-set-btn");
const shareSetBtn = document.getElementById("share-set-btn");
const publicToggle = document.getElementById("public-toggle");
const shareBox = document.getElementById("share-box");
const shareLinkInput = document.getElementById("share-link");
const copyShareLinkBtn = document.getElementById("copy-share-link");

const viewSetLink = document.getElementById("view-set-link");
const playSetLink = document.getElementById("play-set-link");
const printSetLink = document.getElementById("print-set-link");

const addStandardCardBtn = document.getElementById("add-standard-card");
const addClozeCardBtn = document.getElementById("add-cloze-card");
const addDiagramCardBtn = document.getElementById("add-diagram-card");

const editable = editorRoot?.dataset.editable === "true";

const defaultCardMeta = {
  standard: { label: "Standard", front_label: "Front", back_label: "Back" },
  cloze: { label: "Fill in the blanks", front_label: "Sentence with gap", back_label: "Completed answer" },
  diagram: { label: "Diagram prompt", front_label: "Prompt / image task", back_label: "Model answer" },
  table: { label: "Table / compare", front_label: "Prompt / comparison", back_label: "Completed answer" },
  quiz: { label: "Quick quiz", front_label: "Question", back_label: "Answer" }
};

const cardTypeMeta = window.cardTypeMeta || defaultCardMeta;

function clone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

function blankCard(position, type = "standard") {
  return {
    position,
    keyword: "",
    card_type: type,
    front_text: type === "cloze" ? "The CPU contains the ______ and the Control Unit." : "",
    back_text: type === "cloze" ? "The CPU contains the ALU and the Control Unit." : "",
    prompt_text: "",
    answer_text: "",
    hint: "",
    word_bank: "",
    image_front: "",
    image_back: "",
    notes: ""
  };
}

function normaliseState(input) {
  const state = clone(input || {});
  state.id = state.id || null;
  state.title = state.title || "New Flashcard Set";
  state.description = state.description || "";
  state.owner = state.owner || "guest";
  state.selected_keywords = Array.isArray(state.selected_keywords) ? state.selected_keywords : [];
  state.cards = Array.isArray(state.cards) ? state.cards : [];

  while (state.cards.length < 10) {
    state.cards.push(blankCard(state.cards.length + 1));
  }

  state.cards = state.cards.map((card, index) => ({
    ...blankCard(index + 1, card.card_type || "standard"),
    ...card,
    position: index + 1,
    card_type: card.card_type || "standard"
  }));

  state.is_public = Boolean(state.is_public);
  state.share_code = state.share_code || "";
  return state;
}

let state = normaliseState(window.initialFlashcardSet || {});

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
    viewSetLink.href = "#";
    playSetLink.href = "#";
    printSetLink.href = "#";
    viewSetLink.classList.add("disabled");
    playSetLink.classList.add("disabled");
    printSetLink.classList.add("disabled");
    return;
  }

  viewSetLink.href = `${BASE}/set/${state.id}`;
  playSetLink.href = `${BASE}/play/${state.id}`;
  printSetLink.href = `${BASE}/print/${state.id}`;
  viewSetLink.classList.remove("disabled");
  playSetLink.classList.remove("disabled");
  printSetLink.classList.remove("disabled");
}

function renderCards() {
  if (!cardsContainer) return;

  cardsContainer.innerHTML = "";

  state.cards.forEach((card, index) => {
    const meta = cardTypeMeta[card.card_type] || cardTypeMeta.standard;

    const wrapper = document.createElement("section");
    wrapper.className = "card glass-card editor-card";
    wrapper.innerHTML = `
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center gap-2 mb-3">
          <div>
            <h2 class="h5 mb-1">Card ${index + 1}</h2>
            <div class="text-light-emphasis small">${meta.label}</div>
          </div>
          <div class="btn-group btn-group-sm">
            <button type="button" class="btn btn-outline-light move-up-btn">↑</button>
            <button type="button" class="btn btn-outline-light move-down-btn">↓</button>
            <button type="button" class="btn btn-outline-light duplicate-card-btn">Duplicate</button>
            <button type="button" class="btn btn-outline-danger remove-card-btn">Remove</button>
          </div>
        </div>

        <div class="row g-3">
          <div class="col-md-4">
            <label class="form-label">Keyword</label>
            <input class="form-control" data-field="keyword" value="${escapeHtml(card.keyword)}" ${editable ? "" : "disabled"}>
          </div>

          <div class="col-md-4">
            <label class="form-label">Card type</label>
            <select class="form-select" data-field="card_type" ${editable ? "" : "disabled"}>
              ${Object.entries(cardTypeMeta).map(([key, info]) =>
                `<option value="${key}" ${card.card_type === key ? "selected" : ""}>${info.label}</option>`
              ).join("")}
            </select>
          </div>

          <div class="col-md-4">
            <label class="form-label">Hint</label>
            <input class="form-control" data-field="hint" value="${escapeHtml(card.hint)}" ${editable ? "" : "disabled"}>
          </div>

          <div class="col-md-6">
            <label class="form-label">${meta.front_label}</label>
            <textarea class="form-control" rows="4" data-field="front_text" ${editable ? "" : "disabled"}>${escapeHtml(card.front_text)}</textarea>
          </div>

          <div class="col-md-6">
            <label class="form-label">${meta.back_label}</label>
            <textarea class="form-control" rows="4" data-field="back_text" ${editable ? "" : "disabled"}>${escapeHtml(card.back_text)}</textarea>
          </div>

          <div class="col-md-6">
            <label class="form-label">Prompt / task</label>
            <textarea class="form-control" rows="3" data-field="prompt_text" ${editable ? "" : "disabled"}>${escapeHtml(card.prompt_text)}</textarea>
          </div>

          <div class="col-md-6">
            <label class="form-label">Answer / model response</label>
            <textarea class="form-control" rows="3" data-field="answer_text" ${editable ? "" : "disabled"}>${escapeHtml(card.answer_text)}</textarea>
          </div>

          <div class="col-md-6">
            <label class="form-label">Word bank</label>
            <input class="form-control" data-field="word_bank" value="${escapeHtml(card.word_bank)}" ${editable ? "" : "disabled"}>
          </div>

          <div class="col-md-6">
            <label class="form-label">Teacher notes</label>
            <input class="form-control" data-field="notes" value="${escapeHtml(card.notes)}" ${editable ? "" : "disabled"}>
          </div>
        </div>
      </div>
    `;

    cardsContainer.appendChild(wrapper);

    if (!editable) return;

    wrapper.querySelectorAll("[data-field]").forEach(input => {
      input.addEventListener("input", event => {
        const field = event.target.dataset.field;
        state.cards[index][field] = event.target.value;
        if (field === "card_type") {
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
      state.cards.splice(index + 1, 0, clone(state.cards[index]));
      state.cards.forEach((item, idx) => item.position = idx + 1);
      renderCards();
      setStatus("Card duplicated", "info");
    });

    wrapper.querySelector(".remove-card-btn").addEventListener("click", () => {
      if (state.cards.length <= 10) {
        setStatus("The set must keep at least 10 cards.", "error");
        return;
      }
      state.cards.splice(index, 1);
      state.cards.forEach((item, idx) => item.position = idx + 1);
      renderCards();
      setStatus("Card removed", "info");
    });
  });
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

  if (!response.ok) {
    throw new Error(payload.error || `Save failed (${response.status})`);
  }

  state.id = payload.id || payload.set?.id || state.id;
  if (payload.share_code) state.share_code = payload.share_code;
  if (typeof payload.is_public === "boolean") state.is_public = payload.is_public;

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

  if (!response.ok) {
    throw new Error(payload.error || `Share failed (${response.status})`);
  }

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

if (setTitleInput) {
  setTitleInput.addEventListener("input", () => {
    state.title = setTitleInput.value;
    setStatus("Unsaved changes");
  });
}

if (setDescriptionInput) {
  setDescriptionInput.addEventListener("input", () => {
    state.description = setDescriptionInput.value;
    setStatus("Unsaved changes");
  });
}

if (saveSetBtn) {
  saveSetBtn.addEventListener("click", async () => {
    try {
      await saveSet();
    } catch (err) {
      setStatus(err.message, "error");
    }
  });
}

if (shareSetBtn) {
  shareSetBtn.addEventListener("click", async () => {
    try {
      await shareSet();
    } catch (err) {
      setStatus(err.message, "error");
    }
  });
}

if (copyShareLinkBtn) {
  copyShareLinkBtn.addEventListener("click", async () => {
    if (!shareLinkInput?.value) return;
    await navigator.clipboard.writeText(shareLinkInput.value);
    setStatus("Share link copied", "info");
  });
}

if (publicToggle) {
  publicToggle.addEventListener("change", () => {
    state.is_public = publicToggle.checked;
    setStatus("Unsaved share setting", "info");
  });
}

if (addStandardCardBtn) addStandardCardBtn.addEventListener("click", () => addCard("standard"));
if (addClozeCardBtn) addClozeCardBtn.addEventListener("click", () => addCard("cloze"));
if (addDiagramCardBtn) addDiagramCardBtn.addEventListener("click", () => addCard("diagram"));

updateTopFields();
renderCards();
setStatus("Unsaved changes");