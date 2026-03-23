(function () {
  const root = document.getElementById('flashcard-editor-root');
  if (!root || !window.initialFlashcardSet) return;

  const editable = root.dataset.editable === 'true';
  const state = structuredClone(window.initialFlashcardSet);
  state.selected_keywords = state.selected_keywords || [];
  state.cards = state.cards || [];

  const cardsContainer = document.getElementById('cards-container');
  const setTitleInput = document.getElementById('set-title');
  const setDescriptionInput = document.getElementById('set-description');
  const selectedKeywordsBox = document.getElementById('selected-keywords-box');
  const statusBox = document.getElementById('editor-status');
  const viewSetLink = document.getElementById('view-set-link');
  const playSetLink = document.getElementById('play-set-link');
  const printSetLink = document.getElementById('print-set-link');
  const shareBox = document.getElementById('share-box');
  const shareLinkInput = document.getElementById('share-link');
  const publicToggle = document.getElementById('public-toggle');

const BASE = '/flashcards';

viewSetLink.href = `${BASE}/set/${state.id}`;
playSetLink.href = `${BASE}/play/${state.id}`;
printSetLink.href = `${BASE}/print/${state.id}`;

const response = await fetch(`${BASE}/api/sets`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(state)
});

const shareResponse = await fetch(`${BASE}/api/sets/${state.id}/share`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ public: publicToggle.checked })
});

shareLinkInput.value = `${window.location.origin}${BASE}/shared/${state.share_code}`;



  function setStatus(message, mode = 'neutral') {
    statusBox.textContent = message;
    statusBox.dataset.mode = mode;
  }

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function createBlankCard(type = 'standard') {
    const number = state.cards.length + 1;
    return {
      position: number,
      keyword: '',
      card_type: type,
      front_text: type === 'cloze' ? 'The CPU contains the ______ and the Control Unit.' : '',
      back_text: type === 'cloze' ? 'The CPU contains the ALU and the Control Unit.' : '',
      prompt_text: '',
      answer_text: '',
      hint: '',
      word_bank: '',
      image_front: '',
      image_back: '',
      notes: ''
    };
  }

  function updateActionLinks() {
    if (!state.id) return;
    viewSetLink.href = `/set/${state.id}`;
    playSetLink.href = `/play/${state.id}`;
    printSetLink.href = `/print/${state.id}`;
    [viewSetLink, playSetLink, printSetLink].forEach(link => link.classList.remove('disabled'));
  }

  function renderSelectedKeywords() {
    selectedKeywordsBox.innerHTML = '';
    if (!state.selected_keywords.length) {
      selectedKeywordsBox.innerHTML = '<span class="text-light-emphasis small">No suggested keywords were chosen for this set.</span>';
      return;
    }
    state.selected_keywords.forEach(keyword => {
      const span = document.createElement('span');
      span.className = 'badge rounded-pill text-bg-dark border border-secondary';
      span.textContent = keyword;
      selectedKeywordsBox.appendChild(span);
    });
  }

  function syncSetMeta() {
    state.title = setTitleInput.value.trim() || 'Untitled set';
    state.description = setDescriptionInput.value.trim();
  }

  function handleImageInput(file, cardIndex, fieldName, previewImg) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      state.cards[cardIndex][fieldName] = reader.result;
      previewImg.src = reader.result;
      previewImg.classList.remove('d-none');
      setStatus('Image added. Humans do love dragging screenshots into everything.', 'info');
    };
    reader.readAsDataURL(file);
  }

  function bindCardEvents(cardElement, cardIndex) {
    const card = state.cards[cardIndex];
    cardElement.querySelectorAll('[data-field]').forEach(input => {
      input.addEventListener('input', (event) => {
        const field = event.target.dataset.field;
        state.cards[cardIndex][field] = event.target.value;
        if (field === 'card_type') renderCards();
        else if (field === 'keyword' && !state.cards[cardIndex].front_text) renderCards();
        else setStatus('Unsaved changes', 'neutral');
      });
    });

    cardElement.querySelector('.remove-card-btn').addEventListener('click', () => {
      if (state.cards.length <= 10) {
        setStatus('The set must keep at least 10 cards.', 'error');
        return;
      }
      state.cards.splice(cardIndex, 1);
      state.cards.forEach((item, index) => item.position = index + 1);
      renderCards();
      setStatus('Card removed', 'info');
    });

    cardElement.querySelector('.duplicate-card-btn').addEventListener('click', () => {
      const copy = structuredClone(state.cards[cardIndex]);
      state.cards.splice(cardIndex + 1, 0, copy);
      state.cards.forEach((item, index) => item.position = index + 1);
      renderCards();
      setStatus('Card duplicated', 'info');
    });

    const frontPreview = cardElement.querySelector('.preview-front-image');
    const backPreview = cardElement.querySelector('.preview-back-image');

    cardElement.querySelector('.front-image-input').addEventListener('change', (event) => {
      handleImageInput(event.target.files[0], cardIndex, 'image_front', frontPreview);
    });
    cardElement.querySelector('.back-image-input').addEventListener('change', (event) => {
      handleImageInput(event.target.files[0], cardIndex, 'image_back', backPreview);
    });

    cardElement.querySelectorAll('.paste-zone').forEach(zone => {
      zone.addEventListener('paste', (event) => {
        const items = [...(event.clipboardData?.items || [])];
        const imageItem = items.find(item => item.type.startsWith('image/'));
        if (!imageItem) return;
        const fieldName = zone.dataset.target;
        const file = imageItem.getAsFile();
        const preview = fieldName === 'image_front' ? frontPreview : backPreview;
        handleImageInput(file, cardIndex, fieldName, preview);
        event.preventDefault();
      });
    });

    cardElement.querySelectorAll('.clear-image-btn').forEach(button => {
      button.addEventListener('click', () => {
        const field = button.dataset.target;
        state.cards[cardIndex][field] = '';
        const preview = field === 'image_front' ? frontPreview : backPreview;
        preview.src = '';
        preview.classList.add('d-none');
        setStatus('Image removed', 'info');
      });
    });

    cardElement.querySelector('.move-up-btn').addEventListener('click', () => {
      if (cardIndex === 0) return;
      [state.cards[cardIndex - 1], state.cards[cardIndex]] = [state.cards[cardIndex], state.cards[cardIndex - 1]];
      state.cards.forEach((item, index) => item.position = index + 1);
      renderCards();
    });

    cardElement.querySelector('.move-down-btn').addEventListener('click', () => {
      if (cardIndex >= state.cards.length - 1) return;
      [state.cards[cardIndex + 1], state.cards[cardIndex]] = [state.cards[cardIndex], state.cards[cardIndex + 1]];
      state.cards.forEach((item, index) => item.position = index + 1);
      renderCards();
    });
  }

  function cardFields(card, index) {
    const typeMeta = window.cardTypeMeta[card.card_type] || window.cardTypeMeta.standard;
    return `
      <div class="row g-3">
        <div class="col-md-3">
          <label class="form-label">Keyword</label>
          <input class="form-control" data-field="keyword" value="${escapeHtml(card.keyword)}" placeholder="Keyword ${index + 1}">
        </div>
        <div class="col-md-3">
          <label class="form-label">Card type</label>
          <select class="form-select" data-field="card_type">
            ${Object.entries(window.cardTypeMeta).map(([key, meta]) => `
              <option value="${key}" ${card.card_type === key ? 'selected' : ''}>${meta.label}</option>
            `).join('')}
          </select>
        </div>
        <div class="col-md-3">
          <label class="form-label">Hint</label>
          <input class="form-control" data-field="hint" value="${escapeHtml(card.hint)}" placeholder="Optional hint">
        </div>
        <div class="col-md-3">
          <label class="form-label">Word bank</label>
          <input class="form-control" data-field="word_bank" value="${escapeHtml(card.word_bank)}" placeholder="Optional word bank">
        </div>
        <div class="col-md-6">
          <label class="form-label">${typeMeta.front_label}</label>
          <textarea class="form-control" rows="4" data-field="front_text" placeholder="Front side text">${escapeHtml(card.front_text)}</textarea>
        </div>
        <div class="col-md-6">
          <label class="form-label">${typeMeta.back_label}</label>
          <textarea class="form-control" rows="4" data-field="back_text" placeholder="Back side text">${escapeHtml(card.back_text)}</textarea>
        </div>
        <div class="col-md-6">
          <label class="form-label">Prompt / task</label>
          <textarea class="form-control" rows="2" data-field="prompt_text" placeholder="Extra prompt or instruction">${escapeHtml(card.prompt_text)}</textarea>
        </div>
        <div class="col-md-6">
          <label class="form-label">Answer / model response</label>
          <textarea class="form-control" rows="2" data-field="answer_text" placeholder="Extra answer or explanation">${escapeHtml(card.answer_text)}</textarea>
        </div>
        <div class="col-12">
          <label class="form-label">Teacher notes</label>
          <textarea class="form-control" rows="2" data-field="notes" placeholder="Optional private notes">${escapeHtml(card.notes)}</textarea>
        </div>
      </div>`;
  }

  function imagePanel(card) {
    return `
      <div class="row g-3 mt-1">
        <div class="col-md-6">
          <div class="image-zone-card">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <strong>Front image</strong>
              <button type="button" class="btn btn-sm btn-outline-light clear-image-btn" data-target="image_front">Clear</button>
            </div>
            <label class="btn btn-sm btn-outline-light mb-2">Upload image <input class="front-image-input d-none" type="file" accept="image/*"></label>
            <div class="paste-zone" tabindex="0" data-target="image_front">Paste image here with Ctrl+V</div>
            <img src="${escapeHtml(card.image_front)}" class="preview-image preview-front-image ${card.image_front ? '' : 'd-none'}" alt="Front preview">
          </div>
        </div>
        <div class="col-md-6">
          <div class="image-zone-card">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <strong>Back image</strong>
              <button type="button" class="btn btn-sm btn-outline-light clear-image-btn" data-target="image_back">Clear</button>
            </div>
            <label class="btn btn-sm btn-outline-light mb-2">Upload image <input class="back-image-input d-none" type="file" accept="image/*"></label>
            <div class="paste-zone" tabindex="0" data-target="image_back">Paste image here with Ctrl+V</div>
            <img src="${escapeHtml(card.image_back)}" class="preview-image preview-back-image ${card.image_back ? '' : 'd-none'}" alt="Back preview">
          </div>
        </div>
      </div>`;
  }

  function renderCards() {
    cardsContainer.innerHTML = '';
    state.cards.forEach((card, index) => {
      const typeMeta = window.cardTypeMeta[card.card_type] || window.cardTypeMeta.standard;
      const wrapper = document.createElement('section');
      wrapper.className = 'card glass-card editor-card';
      wrapper.innerHTML = `
        <div class="card-body">
          <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
            <div>
              <span class="template-badge">Card ${index + 1}</span>
              <span class="badge text-bg-dark border border-secondary ms-2">${typeMeta.label}</span>
            </div>
            <div class="d-flex flex-wrap gap-2">
              <button type="button" class="btn btn-sm btn-outline-light move-up-btn">↑</button>
              <button type="button" class="btn btn-sm btn-outline-light move-down-btn">↓</button>
              <button type="button" class="btn btn-sm btn-outline-light duplicate-card-btn">Duplicate</button>
              <button type="button" class="btn btn-sm btn-outline-danger remove-card-btn">Remove</button>
            </div>
          </div>
          ${cardFields(card, index)}
          ${imagePanel(card)}
        </div>`;
      cardsContainer.appendChild(wrapper);
      bindCardEvents(wrapper, index);
    });
  }

  async function saveSet() {
    syncSetMeta();
    try {
      const response = await fetch('/api/sets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state)
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'Save failed');
      Object.assign(state, payload.set);
      updateActionLinks();
      setStatus('Set saved successfully', 'success');
    } catch (error) {
      setStatus(error.message, 'error');
    }
  }

  async function shareSet() {
    if (!state.id) {
      setStatus('Save the set before sharing it.', 'error');
      return;
    }
    try {
      const response = await fetch(`/api/sets/${state.id}/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ public: publicToggle.checked })
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'Share failed');
      shareLinkInput.value = payload.share_url;
      publicToggle.checked = payload.is_public;
      shareBox.classList.remove('d-none');
      setStatus('Share link updated', 'success');
    } catch (error) {
      setStatus(error.message, 'error');
    }
  }

  document.getElementById('save-set-btn').addEventListener('click', saveSet);
  document.getElementById('share-set-btn').addEventListener('click', shareSet);
  document.getElementById('copy-share-link').addEventListener('click', async () => {
    if (!shareLinkInput.value) return;
    await navigator.clipboard.writeText(shareLinkInput.value);
    setStatus('Share link copied', 'success');
  });
  publicToggle.addEventListener('change', () => {
    if (state.id) shareSet();
  });

  document.getElementById('add-standard-card').addEventListener('click', () => {
    state.cards.push(createBlankCard('standard'));
    renderCards();
  });
  document.getElementById('add-cloze-card').addEventListener('click', () => {
    state.cards.push(createBlankCard('cloze'));
    renderCards();
  });
  document.getElementById('add-diagram-card').addEventListener('click', () => {
    state.cards.push(createBlankCard('diagram'));
    renderCards();
  });

  setTitleInput.addEventListener('input', () => setStatus('Unsaved changes', 'neutral'));
  setDescriptionInput.addEventListener('input', () => setStatus('Unsaved changes', 'neutral'));

  if (state.share_code) {
    shareBox.classList.remove('d-none');
    shareLinkInput.value = `${window.location.origin}/shared/${state.share_code}`;
    publicToggle.checked = !!state.is_public;
  }

  renderSelectedKeywords();
  renderCards();
  if (state.id) updateActionLinks();
})();
