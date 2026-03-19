(function () {
  const cfg = window.flashcardConfig;
  if (!cfg) return;
  const prefix = cfg.prefix;
  const minCards = cfg.minCards;
  const initialData = JSON.parse(document.getElementById("flashcard-data").textContent);
  const cardsContainer = document.getElementById("cards-container");
  const titleInput = document.getElementById("set-title");
  const descriptionInput = document.getElementById("set-description");
  const publicInput = document.getElementById("is-public");
  const sharedToInput = document.getElementById("shared-to");
  const saveBtn = document.getElementById("save-set");
  const saveStatus = document.getElementById("save-status");
  const cardTotalBadge = document.getElementById("card-total-badge");
  const targetCountInput = document.getElementById("target-count");
  const applyCountBtn = document.getElementById("apply-count");
  const addBlankCardBtn = document.getElementById("add-blank-card");
  const deleteBtn = document.getElementById("delete-set");
  const keywordSearch = document.getElementById("keyword-search");
  let currentSetId = initialData.id || null;
  function blankCard(keyword = "") { return { keyword, meaning: "", notes: "", image: "" }; }
  function updateCountBadge() { const count = cardsContainer.querySelectorAll(".card-editor").length; cardTotalBadge.textContent = `${count} card${count === 1 ? "" : "s"}`; }
  function createTextArea(labelText, className, value = "", rows = 4) {
    const wrap = document.createElement("div"); wrap.className = "mb-3";
    const label = document.createElement("label"); label.className = "form-label"; label.textContent = labelText;
    const textarea = document.createElement("textarea"); textarea.className = `form-control ${className}`; textarea.rows = rows; textarea.value = value || "";
    wrap.append(label, textarea); return { wrap, textarea };
  }
  function processImageFile(file) {
    return new Promise((resolve, reject) => {
      if (!file.type.startsWith("image/")) { reject(new Error("That is not an image file.")); return; }
      const reader = new FileReader();
      reader.onload = () => {
        const img = new Image();
        img.onload = () => {
          const maxSize = 1200; let { width, height } = img;
          const scale = Math.min(1, maxSize / Math.max(width, height)); width = Math.round(width * scale); height = Math.round(height * scale);
          const canvas = document.createElement("canvas"); canvas.width = width; canvas.height = height;
          const ctx = canvas.getContext("2d"); ctx.drawImage(img, 0, 0, width, height);
          resolve(canvas.toDataURL("image/jpeg", 0.85));
        };
        img.onerror = reject; img.src = reader.result;
      };
      reader.onerror = reject; reader.readAsDataURL(file);
    });
  }
  function attachImageHandlers(dropzone, fileInput, imagePreview, helperText) {
    async function handleFile(file) {
      try {
        helperText.textContent = "Processing image...";
        const dataUrl = await processImageFile(file);
        imagePreview.src = dataUrl; imagePreview.hidden = false; dropzone.classList.add("has-image"); dropzone.dataset.image = dataUrl; helperText.textContent = "Image ready.";
      } catch (err) { helperText.textContent = err.message || "Image processing failed."; }
    }
    dropzone.addEventListener("paste", async (event) => {
      const items = event.clipboardData?.items || [];
      for (const item of items) {
        if (item.type.startsWith("image/")) {
          event.preventDefault(); const file = item.getAsFile(); if (file) { await handleFile(file); return; }
        }
      }
    });
    fileInput.addEventListener("change", async () => { const file = fileInput.files?.[0]; if (file) await handleFile(file); });
  }
  function buildCard(cardData = {}, index = 0) {
    const card = document.createElement("section"); card.className = "card-editor";
    const header = document.createElement("div"); header.className = "d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3";
    const heading = document.createElement("h3"); heading.className = "h5 mb-0"; heading.textContent = `Card ${index + 1}`;
    const removeBtn = document.createElement("button"); removeBtn.type = "button"; removeBtn.className = "btn btn-sm btn-outline-danger"; removeBtn.textContent = "Remove";
    removeBtn.addEventListener("click", () => { const remaining = cardsContainer.querySelectorAll(".card-editor").length; if (remaining <= minCards) { alert(`You need at least ${minCards} cards in a set.`); return; } card.remove(); renumberCards(); });
    header.append(heading, removeBtn);
    const row = document.createElement("div"); row.className = "row g-3";
    const left = document.createElement("div"); left.className = "col-lg-7";
    const right = document.createElement("div"); right.className = "col-lg-5";
    const keywordWrap = document.createElement("div"); keywordWrap.className = "mb-3";
    const keywordLabel = document.createElement("label"); keywordLabel.className = "form-label"; keywordLabel.textContent = "Keyword";
    const keywordInput = document.createElement("input"); keywordInput.className = "form-control keyword-input"; keywordInput.value = cardData.keyword || "";
    keywordWrap.append(keywordLabel, keywordInput);
    const { wrap: meaningWrap } = createTextArea("Meaning / reverse", "meaning-input", cardData.meaning || "", 5);
    const { wrap: notesWrap } = createTextArea("Front notes / prompts", "notes-input", cardData.notes || "", 4);
    left.append(keywordWrap, meaningWrap, notesWrap);
    const imageWrap = document.createElement("div"); imageWrap.className = "mb-3";
    const imageLabel = document.createElement("label"); imageLabel.className = "form-label d-block"; imageLabel.textContent = "Image";
    const dropzone = document.createElement("div"); dropzone.className = "image-dropzone"; dropzone.tabIndex = 0; dropzone.dataset.image = cardData.image || "";
    const helperText = document.createElement("div"); helperText.textContent = "Paste an image here with Ctrl+V, or upload one.";
    const imagePreview = document.createElement("img"); imagePreview.hidden = !cardData.image; imagePreview.src = cardData.image || ""; if (cardData.image) dropzone.classList.add("has-image");
    dropzone.append(imagePreview, helperText);
    const imageActions = document.createElement("div"); imageActions.className = "image-actions mt-2";
    const fileInput = document.createElement("input"); fileInput.type = "file"; fileInput.accept = "image/*"; fileInput.className = "d-none";
    const uploadBtn = document.createElement("button"); uploadBtn.type = "button"; uploadBtn.className = "btn btn-outline-light btn-sm"; uploadBtn.textContent = "Upload image"; uploadBtn.addEventListener("click", () => fileInput.click());
    const clearBtn = document.createElement("button"); clearBtn.type = "button"; clearBtn.className = "btn btn-outline-danger btn-sm"; clearBtn.textContent = "Remove image";
    clearBtn.addEventListener("click", () => { dropzone.dataset.image = ""; imagePreview.hidden = true; imagePreview.src = ""; dropzone.classList.remove("has-image"); helperText.textContent = "Paste an image here with Ctrl+V, or upload one."; fileInput.value = ""; });
    imageActions.append(uploadBtn, clearBtn, fileInput); imageWrap.append(imageLabel, dropzone, imageActions); right.append(imageWrap); attachImageHandlers(dropzone, fileInput, imagePreview, helperText);
    row.append(left, right); card.append(header, row); return card;
  }
  function renumberCards() { [...cardsContainer.querySelectorAll(".card-editor")].forEach((card, index) => { card.querySelector("h3").textContent = `Card ${index + 1}`; }); updateCountBadge(); }
  function addCard(cardData = {}) { cardsContainer.appendChild(buildCard(cardData, cardsContainer.querySelectorAll(".card-editor").length)); renumberCards(); }
  function collectCards() {
    return [...cardsContainer.querySelectorAll(".card-editor")].map((card) => ({
      keyword: card.querySelector(".keyword-input").value.trim(),
      meaning: card.querySelector(".meaning-input").value.trim(),
      notes: card.querySelector(".notes-input").value.trim(),
      image: card.querySelector(".image-dropzone").dataset.image || "",
    }));
  }
  function populateInitialCards() { const cards = Array.isArray(initialData.cards) ? initialData.cards : []; cards.forEach(addCard); if (cards.length < minCards) for (let i = cards.length; i < minCards; i += 1) addCard(blankCard()); }
  function ensureCount(target) {
    const current = cardsContainer.querySelectorAll(".card-editor").length;
    if (target > current) { for (let i = current; i < target; i += 1) addCard(blankCard()); return; }
    if (target < current) {
      if (target < minCards) { alert(`Minimum card count is ${minCards}.`); return; }
      if (!confirm(`Trim this set down to ${target} cards? Extra cards at the end will be removed.`)) return;
      const cards = [...cardsContainer.querySelectorAll(".card-editor")]; cards.slice(target).forEach((card) => card.remove()); renumberCards();
    }
  }
  async function saveSet() {
    const cards = collectCards(); if (cards.length < minCards) { alert(`You need at least ${minCards} cards.`); return; }
    if (!titleInput.value.trim()) titleInput.value = "Untitled set";
    const payload = { title: titleInput.value.trim(), description: descriptionInput.value.trim(), is_public: publicInput.checked, shared_to: sharedToInput.value, cards };
    saveBtn.disabled = true; saveStatus.textContent = "Saving...";
    const endpoint = currentSetId ? `${prefix}/api/set/${currentSetId}` : `${prefix}/api/set`; const method = currentSetId ? "PUT" : "POST";
    try {
      const res = await fetch(endpoint, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const data = await res.json(); if (!res.ok) throw new Error(data.error || "Save failed"); currentSetId = data.id; saveStatus.textContent = "Saved."; window.location.href = `${prefix}/view/${currentSetId}`;
    } catch (err) { saveStatus.textContent = err.message || "Save failed."; } finally { saveBtn.disabled = false; }
  }
  function filterKeywordButtons() {
    const term = keywordSearch.value.trim().toLowerCase();
    document.querySelectorAll(".keyword-picker").forEach((btn) => {
      const keyword = btn.dataset.keyword.toLowerCase(); const desc = (btn.dataset.description || "").toLowerCase(); const match = !term || keyword.includes(term) || desc.includes(term); btn.classList.toggle("d-none", !match);
    });
    document.querySelectorAll(".keyword-group").forEach((group) => { const anyVisible = group.querySelector(".keyword-picker:not(.d-none)"); group.classList.toggle("d-none", !anyVisible); });
  }
  document.querySelectorAll(".keyword-picker").forEach((btn) => {
    btn.addEventListener("click", () => {
      const keyword = btn.dataset.keyword;
      const existing = [...cardsContainer.querySelectorAll(".keyword-input")].find((input) => input.value.trim().toLowerCase() === keyword.toLowerCase());
      if (existing) { existing.scrollIntoView({ behavior: "smooth", block: "center" }); existing.focus(); return; }
      addCard(blankCard(keyword)); const inputs = cardsContainer.querySelectorAll(".keyword-input"); inputs[inputs.length - 1].focus();
    });
  });
  addBlankCardBtn?.addEventListener("click", () => addCard(blankCard()));
  applyCountBtn?.addEventListener("click", () => ensureCount(Number(targetCountInput.value || minCards)));
  saveBtn?.addEventListener("click", saveSet);
  keywordSearch?.addEventListener("input", filterKeywordButtons);
  deleteBtn?.addEventListener("click", async () => {
    if (!currentSetId) return; if (!confirm("Delete this flashcard set?")) return;
    const res = await fetch(`${prefix}/api/set/${currentSetId}`, { method: "DELETE" }); const data = await res.json(); if (!res.ok) { alert(data.error || "Delete failed"); return; } window.location.href = `${prefix}/my-sets`;
  });
  populateInitialCards();
})();
