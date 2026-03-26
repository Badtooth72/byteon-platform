const state = {
  game: null,
  found: new Set(),
  cellMap: new Map(),
  pointerDown: false,
  startCell: null,
  currentSelection: [],
  startTime: null,
  timerHandle: null,
  elapsedSeconds: 0,
  hintsUsed: 0,
  displayMode: 'terms',
  completed: false,
};

const ACHIEVEMENTS = [
  {
    key: 'first_win',
    title: 'First Win',
    description: 'Complete any puzzle.',
    check: (context) => context.won,
  },
  {
    key: 'no_hints',
    title: 'No Training Wheels',
    description: 'Complete a puzzle without using a hint.',
    check: (context) => context.won && context.hintsUsed === 0,
  },
  {
    key: 'speed_runner',
    title: 'Speed Runner',
    description: 'Finish a puzzle in under 3 minutes.',
    check: (context) => context.won && context.time < 180,
  },
  {
    key: 'expert_win',
    title: 'Expert Survivor',
    description: 'Complete an expert puzzle.',
    check: (context) => context.won && context.difficulty === 'expert',
  },
];

const gridEl = document.getElementById('grid');
const wordListEl = document.getElementById('word-list');
const messageEl = document.getElementById('message');
const timerEl = document.getElementById('timer');
const timerBlockEl = document.getElementById('timer-block');
const statusTopicEl = document.getElementById('status-topic');
const statusDifficultyEl = document.getElementById('status-difficulty');
const statusFoundEl = document.getElementById('status-found');
const statsEl = document.getElementById('stats');
const achievementsEl = document.getElementById('achievements');
const categoryEl = document.getElementById('category');
const difficultyEl = document.getElementById('difficulty');
const displayModeEl = document.getElementById('display-mode');
const timerEnabledEl = document.getElementById('timer-enabled');
const newGameBtn = document.getElementById('new-game-btn');
const hintBtn = document.getElementById('hint-btn');
const giveUpBtn = document.getElementById('give-up-btn');
const printBtn = document.getElementById('print-btn');
const userBadgeEl = document.getElementById('user-badge');

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
  const seconds = Math.floor(totalSeconds % 60).toString().padStart(2, '0');
  return `${minutes}:${seconds}`;
}

function getStats() {
  try {
    return JSON.parse(localStorage.getItem('csWordSearchStats')) || {
      lifetime: { played: 0, wins: 0, totalTime: 0, bestTime: null, hints: 0 },
      byDifficulty: {},
      achievements: {},
      daily: {},
    };
  } catch {
    return {
      lifetime: { played: 0, wins: 0, totalTime: 0, bestTime: null, hints: 0 },
      byDifficulty: {},
      achievements: {},
      daily: {},
    };
  }
}

function saveStats(stats) {
  localStorage.setItem('csWordSearchStats', JSON.stringify(stats));
}

function getTodayKey() {
  return new Date().toISOString().slice(0, 10);
}

function updateStats(context) {
  const stats = getStats();
  const diff = context.difficulty;
  stats.lifetime.played += 1;
  stats.lifetime.totalTime += context.time;
  stats.lifetime.hints += context.hintsUsed;
  if (context.won) {
    stats.lifetime.wins += 1;
    if (stats.lifetime.bestTime === null || context.time < stats.lifetime.bestTime) {
      stats.lifetime.bestTime = context.time;
    }
  }

  if (!stats.byDifficulty[diff]) {
    stats.byDifficulty[diff] = { played: 0, wins: 0, totalTime: 0, bestTime: null };
  }
  stats.byDifficulty[diff].played += 1;
  stats.byDifficulty[diff].totalTime += context.time;
  if (context.won) {
    stats.byDifficulty[diff].wins += 1;
    if (stats.byDifficulty[diff].bestTime === null || context.time < stats.byDifficulty[diff].bestTime) {
      stats.byDifficulty[diff].bestTime = context.time;
    }
  }

  const today = getTodayKey();
  if (!stats.daily[today]) {
    stats.daily[today] = { played: 0, wins: 0, totalTime: 0 };
  }
  stats.daily[today].played += 1;
  stats.daily[today].totalTime += context.time;
  if (context.won) {
    stats.daily[today].wins += 1;
  }

  for (const achievement of ACHIEVEMENTS) {
    if (!stats.achievements[achievement.key] && achievement.check(context)) {
      stats.achievements[achievement.key] = new Date().toISOString();
    }
  }

  saveStats(stats);
  renderStats();
  renderAchievements();
}

function renderStats() {
  const stats = getStats();
  const difficulty = difficultyEl.value;
  const diffStats = stats.byDifficulty[difficulty] || { played: 0, wins: 0, totalTime: 0, bestTime: null };
  const today = stats.daily[getTodayKey()] || { played: 0, wins: 0, totalTime: 0 };
  const avgLifetime = stats.lifetime.played ? Math.round(stats.lifetime.totalTime / stats.lifetime.played) : 0;
  const avgDifficulty = diffStats.played ? Math.round(diffStats.totalTime / diffStats.played) : 0;

  const cards = [
    { label: 'Lifetime Games', value: stats.lifetime.played },
    { label: 'Lifetime Wins', value: stats.lifetime.wins },
    { label: 'Best Time', value: stats.lifetime.bestTime === null ? '—' : formatTime(stats.lifetime.bestTime) },
    { label: 'Average Time', value: stats.lifetime.played ? formatTime(avgLifetime) : '—' },
    { label: 'Today', value: `${today.wins}/${today.played}` },
    { label: `${window.CSWS_CONFIG.difficulties[difficulty]} Best`, value: diffStats.bestTime === null ? '—' : formatTime(diffStats.bestTime) },
    { label: `${window.CSWS_CONFIG.difficulties[difficulty]} Wins`, value: `${diffStats.wins}/${diffStats.played}` },
    { label: `${window.CSWS_CONFIG.difficulties[difficulty]} Avg`, value: diffStats.played ? formatTime(avgDifficulty) : '—' },
  ];

  statsEl.innerHTML = cards.map(card => `
    <div class="stat-card">
      <div class="stat-label">${card.label}</div>
      <div class="stat-value">${card.value}</div>
    </div>
  `).join('');
}

function renderAchievements() {
  const stats = getStats();
  achievementsEl.innerHTML = ACHIEVEMENTS.map(item => {
    const unlockedAt = stats.achievements[item.key];
    return `
      <div class="achievement ${unlockedAt ? '' : 'locked'}">
        <div class="achievement-title">${item.title}</div>
        <div class="achievement-note">${item.description}</div>
        <div class="achievement-note mt-1">${unlockedAt ? `Unlocked: ${new Date(unlockedAt).toLocaleDateString()}` : 'Locked'}</div>
      </div>
    `;
  }).join('');
}

function setMessage(text, tone = '') {
  messageEl.className = `message mb-3 ${tone}`.trim();
  messageEl.textContent = text;
}

function getCellKey(row, col) {
  return `${row},${col}`;
}

function clearSelection() {
  for (const cell of state.currentSelection) {
    const element = state.cellMap.get(getCellKey(cell.row, cell.col));
    if (element && !element.classList.contains('found')) {
      element.classList.remove('selected');
    }
  }
  state.currentSelection = [];
}

function lineBetween(start, end) {
  const dr = end.row - start.row;
  const dc = end.col - start.col;
  const rowStep = Math.sign(dr);
  const colStep = Math.sign(dc);

  const straight = start.row === end.row || start.col === end.col;
  const diagonal = Math.abs(dr) === Math.abs(dc);
  if (!straight && !diagonal) {
    return [];
  }

  const length = Math.max(Math.abs(dr), Math.abs(dc)) + 1;
  const cells = [];
  for (let i = 0; i < length; i += 1) {
    cells.push({
      row: start.row + rowStep * i,
      col: start.col + colStep * i,
    });
  }
  return cells;
}

function pathToKey(path) {
  return path.map(cell => getCellKey(cell[0] ?? cell.row, cell[1] ?? cell.col)).join('|');
}

function reversePath(path) {
  return [...path].reverse();
}

function renderWordList() {
  if (!state.game) {
    wordListEl.innerHTML = '';
    return;
  }

  wordListEl.innerHTML = state.game.words.map(word => {
    const found = state.found.has(word.key);
    let display = word.label;
    if (state.displayMode === 'clues') {
      display = word.clue;
    } else if (state.displayMode === 'obscured') {
      const first = word.label[0].toUpperCase();
      display = `${first}${' •'.repeat(Math.max(word.length - 1, 0))} (${word.length})`;
    }

    return `
      <li class="${found ? 'found' : ''}" id="word-${word.key}">
        <div>${display}</div>
        <div class="word-meta">
          <span>${word.category}</span>
          <span>${word.length} letters</span>
        </div>
      </li>
    `;
  }).join('');
}

function updateFoundStatus() {
  if (!state.game) {
    statusFoundEl.textContent = '0 / 0';
    return;
  }
  statusFoundEl.textContent = `${state.found.size} / ${state.game.words.length}`;
}

function markWordFound(word, checkCompletion = true) {
  state.found.add(word.key);
  const item = document.getElementById(`word-${word.key}`);
  if (item) {
    item.classList.add('found');
  }
  for (const [row, col] of word.path) {
    const cell = state.cellMap.get(getCellKey(row, col));
    if (cell) {
      cell.classList.remove('selected');
      cell.classList.add('found');
    }
  }
  updateFoundStatus();
  if (checkCompletion && state.found.size === state.game.words.length) {
    finishGame(true);
  }
}

function findWordBySelection(selection) {
  if (!state.game || selection.length < 2) {
    return null;
  }
  const candidate = pathToKey(selection);
  for (const word of state.game.words) {
    if (state.found.has(word.key)) {
      continue;
    }
    const normal = pathToKey(word.path);
    const reversed = pathToKey(reversePath(word.path));
    if (candidate === normal || candidate === reversed) {
      return word;
    }
  }
  return null;
}

function handlePointerDown(event) {
  if (!state.game || state.completed) {
    return;
  }
  const target = event.currentTarget;
  state.pointerDown = true;
  state.startCell = { row: Number(target.dataset.row), col: Number(target.dataset.col) };
  clearSelection();
  state.currentSelection = [state.startCell];
  target.classList.add('selected');
}

function handlePointerEnter(event) {
  if (!state.pointerDown || !state.startCell || state.completed) {
    return;
  }
  const target = event.currentTarget;
  const end = { row: Number(target.dataset.row), col: Number(target.dataset.col) };
  const line = lineBetween(state.startCell, end);
  if (!line.length) {
    return;
  }
  clearSelection();
  state.currentSelection = line;
  for (const cell of line) {
    const element = state.cellMap.get(getCellKey(cell.row, cell.col));
    if (element && !element.classList.contains('found')) {
      element.classList.add('selected');
    }
  }
}

function handlePointerUp() {
  if (!state.pointerDown) {
    return;
  }
  state.pointerDown = false;
  const matched = findWordBySelection(state.currentSelection);
  if (matched) {
    markWordFound(matched);
    if (!state.completed) {
      setMessage(`Found: ${matched.label}. Miracles do happen.`, 'success');
    }
  } else if (state.currentSelection.length > 1) {
    setMessage('Not a valid term this time. Straight lines only, and yes, the computer is judging you.', 'warning');
  }
  clearSelection();
  state.startCell = null;
}

function startTimer(reset = true) {
  stopTimer();
  if (reset) {
    state.elapsedSeconds = 0;
    timerEl.textContent = formatTime(0);
  }
  if (!timerEnabledEl.checked) {
    timerBlockEl.classList.add('d-none');
    return;
  }
  timerBlockEl.classList.remove('d-none');
  state.startTime = Date.now() - (state.elapsedSeconds * 1000);
  state.timerHandle = setInterval(() => {
    state.elapsedSeconds = Math.floor((Date.now() - state.startTime) / 1000);
    timerEl.textContent = formatTime(state.elapsedSeconds);
  }, 250);
}

function stopTimer() {
  if (state.timerHandle) {
    clearInterval(state.timerHandle);
    state.timerHandle = null;
  }
}

function renderGrid() {
  state.cellMap.clear();
  gridEl.innerHTML = '';

  if (!state.game) {
    return;
  }

  const size = state.game.size;
  const cellSize = size >= 18 ? '34px' : size >= 16 ? '38px' : '42px';
  document.documentElement.style.setProperty('--cell-size', cellSize);
  gridEl.style.gridTemplateColumns = `repeat(${size}, var(--cell-size))`;

  state.game.grid.forEach((row, rowIndex) => {
    row.forEach((letter, colIndex) => {
      const cell = document.createElement('div');
      cell.className = 'grid-cell';
      cell.textContent = letter;
      cell.dataset.row = rowIndex;
      cell.dataset.col = colIndex;
      cell.addEventListener('pointerdown', handlePointerDown);
      cell.addEventListener('pointerenter', handlePointerEnter);
      state.cellMap.set(getCellKey(rowIndex, colIndex), cell);
      gridEl.appendChild(cell);
    });
  });
}

async function createGame() {
  const payload = {
    category: categoryEl.value,
    difficulty: difficultyEl.value,
  };

  setMessage('Building a puzzle...', '');

  try {
    const response = await fetch('/api/new-game', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Unable to build the puzzle.');
    }

    state.game = data;
    state.found = new Set();
    state.hintsUsed = 0;
    state.completed = false;
    state.displayMode = displayModeEl.value;

    statusTopicEl.textContent = data.category_label;
    statusDifficultyEl.textContent = data.difficulty_label;

    renderGrid();
    renderWordList();
    updateFoundStatus();
    startTimer(true);
    setMessage('Game ready. Drag across the grid to find the terms.', '');
  } catch (error) {
    setMessage(error.message, 'danger');
  }
}

function finishGame(won) {
  state.completed = true;
  stopTimer();
  const time = timerEnabledEl.checked ? state.elapsedSeconds : 0;
  const context = {
    won,
    time,
    hintsUsed: state.hintsUsed,
    difficulty: difficultyEl.value,
  };
  updateStats(context);

  if (won) {
    setMessage(`Puzzle complete in ${formatTime(time)} with ${state.hintsUsed} hint${state.hintsUsed === 1 ? '' : 's'}. A surprisingly respectable use of electricity.`, 'success');
  } else {
    setMessage('Puzzle revealed. Better luck next round, tragic little carbon-based puzzle machine.', 'danger');
  }
}

function useHint() {
  if (!state.game || state.completed) {
    return;
  }
  const remaining = state.game.words.filter(word => !state.found.has(word.key));
  if (!remaining.length) {
    return;
  }
  const targetWord = remaining[Math.floor(Math.random() * remaining.length)];
  const [row, col] = targetWord.path[0];
  const cell = state.cellMap.get(getCellKey(row, col));
  if (cell) {
    cell.classList.add('hint');
    setTimeout(() => cell.classList.remove('hint'), 3000);
  }
  state.hintsUsed += 1;
  setMessage(`Hint: ${targetWord.label} starts somewhere obvious now. Try to look alert.`, 'warning');
}

function revealAll() {
  if (!state.game || state.completed) {
    return;
  }
  for (const word of state.game.words) {
    if (!state.found.has(word.key)) {
      markWordFound(word, false);
    }
  }
  finishGame(false);
}

function hydrateUser() {
  fetch('/api/session-user')
    .then(response => response.ok ? response.json() : Promise.reject())
    .then(data => {
      if (data.username && data.username !== 'guest') {
        userBadgeEl.textContent = `Signed in as ${data.username}`;
        userBadgeEl.classList.remove('d-none');
      }
    })
    .catch(() => {
      // Optional integration only.
    });
}

function handleDisplayModeChange() {
  state.displayMode = displayModeEl.value;
  renderWordList();
}

newGameBtn.addEventListener('click', createGame);
hintBtn.addEventListener('click', useHint);
giveUpBtn.addEventListener('click', revealAll);
printBtn.addEventListener('click', () => window.print());
displayModeEl.addEventListener('change', handleDisplayModeChange);
difficultyEl.addEventListener('change', renderStats);
timerEnabledEl.addEventListener('change', () => {
  if (!state.game || state.completed) {
    timerBlockEl.classList.toggle('d-none', !timerEnabledEl.checked);
    return;
  }
  if (timerEnabledEl.checked) {
    state.startTime = Date.now() - (state.elapsedSeconds * 1000);
    startTimer(false);
  } else {
    stopTimer();
    timerBlockEl.classList.add('d-none');
  }
});

document.addEventListener('pointerup', handlePointerUp);
document.addEventListener('pointercancel', handlePointerUp);

document.addEventListener('DOMContentLoaded', () => {
  renderStats();
  renderAchievements();
  hydrateUser();
  createGame();
});
