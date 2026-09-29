(() => {
  const root = document.querySelector('[data-game]');
  if (!root) return;
  const slug = root.dataset.game;
  const $ = id => document.getElementById(id);
  let challenge, wave = 1, score = 0, busy = false, ended = false;
  let frame = 0, waveStarted = 0, feedbackTimer = 0, selectedLane = 0, flashUntil = 0, firing = false;
  let snakeTimer = 0, snake = [{x:4,y:4}], direction = {x:0,y:0}, nextDirection = {x:0,y:0}, fruit = [], lives = 3;
  let bits = Array(8).fill(0), selectedInvader = 0;
  const snakeCanvas = $('snake-canvas'), snakeCtx = snakeCanvas.getContext('2d');
  const invaderCanvas = $('invader-canvas'), invaderCtx = invaderCanvas.getContext('2d');
  const packetCanvas = $('packet-canvas'), packetCtx = packetCanvas.getContext('2d');
  const challengeCanvas = $('challenge-canvas'), challengeCtx = challengeCanvas.getContext('2d');
  const surfaceName = slug === 'hex-snake' ? 'snake' : slug === 'bit-flip' ? 'invader' : slug === 'packet-patrol' ? 'packet' : 'challenge';
  const surfaceCanvas = $(`${surfaceName}-canvas`);
  let phaserGame = null, activeScene = null;
  function ensurePhaser() {
    if (phaserGame || !window.Phaser) return;
    const width = surfaceCanvas.width, height = surfaceCanvas.height;
    const scene = {
      create() {
        activeScene = this;
        this.stars = Array.from({length: 18}, (_, index) => {
          const x = (index * 131 + 17) % width, y = (index * 79 + 23) % height;
          return this.add.circle(x, y, index % 3 === 0 ? 2 : 1, 0xc9faff, .28).setBlendMode(Phaser.BlendModes.ADD);
        });
        this.scanline = this.add.rectangle(width / 2, 0, width, 2, 0x63faff, .16).setBlendMode(Phaser.BlendModes.ADD);
      },
      update(time) {
        this.scanline.y = (time * .055) % height;
        this.stars.forEach((star, index) => { star.alpha = .15 + .2 * (1 + Math.sin(time / 320 + index)); });
      }
    };
    phaserGame = new Phaser.Game({type: Phaser.CANVAS, parent: `${surfaceName}-phaser`, width, height,
      transparent: true, scale: {mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH, width, height},
      render: {pixelArt: true}, scene});
  }
  function loadPhaserEffects() {
    const script = document.createElement('script');
    script.src = '/static/phaser.min.js?v=3.90.0';
    script.async = true;
    script.onload = ensurePhaser;
    document.head.append(script);
  }
  if ('requestIdleCallback' in window) requestIdleCallback(loadPhaserEffects, {timeout: 2500});
  else setTimeout(loadPhaserEffects, 500);
  let soundOn = true, audioContext = null, musicTimer = 0, noteIndex = 0;
  function tone(frequency, duration = .11, type = 'square', volume = .035) {
    if (!soundOn) return;
    try {
      audioContext ||= new (window.AudioContext || window.webkitAudioContext)();
      audioContext.resume();
      const oscillator = audioContext.createOscillator(), gain = audioContext.createGain();
      oscillator.type = type; oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
      gain.gain.setValueAtTime(volume, audioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(.001, audioContext.currentTime + duration);
      oscillator.connect(gain).connect(audioContext.destination); oscillator.start();
      oscillator.stop(audioContext.currentTime + duration);
      if (!musicTimer) updateMusic();
    } catch (_) { soundOn = false; $('arcade-sound').textContent = '♫ Sound unavailable'; }
  }
  function effect(kind) {
    if (activeScene && ['fire','hit','miss'].includes(kind)) {
      const width = surfaceCanvas.width, height = surfaceCanvas.height;
      const colour = kind === 'miss' ? 0xff4abf : kind === 'hit' ? 0xb7ff45 : 0xffcf36;
      for (let i = 0; i < 16; i++) {
        const spark = activeScene.add.circle(width / 2, height * .72, 2 + i % 4, colour, .9).setBlendMode(Phaser.BlendModes.ADD);
        const angle = i * Math.PI / 8;
        activeScene.tweens.add({targets:spark, x:width / 2 + Math.cos(angle) * (40 + i * 5),
          y:height * .72 + Math.sin(angle) * (40 + i * 5), alpha:0, duration:420, onComplete:() => spark.destroy()});
      }
    }
    if (kind === 'fire') { tone(620,.07,'sawtooth'); setTimeout(()=>tone(330,.09,'square'),70); }
    if (kind === 'hit') { tone(440,.11); setTimeout(()=>tone(660,.11),100); setTimeout(()=>tone(880,.16),190); }
    if (kind === 'miss') { tone(190,.18,'sawtooth'); setTimeout(()=>tone(100,.22,'sawtooth'),120); }
    if (kind === 'flip') tone(260,.035,'square',.018);
  }
  function updateMusic() {
    clearInterval(musicTimer); musicTimer = 0;
    if (!soundOn || document.hidden) return;
    const melody = [110,0,165,0,146.8,0,196,0,110,0,220,0,164.8,0,146.8,0];
    musicTimer = setInterval(() => { if (!ended && melody[noteIndex % melody.length]) tone(melody[noteIndex % melody.length],.12,'triangle',.014); noteIndex++; }, 220);
  }
  $('arcade-sound').addEventListener('click', () => {
    soundOn = !soundOn; $('arcade-sound').textContent = soundOn ? '♫ Sound on' : '♫ Sound off';
    $('arcade-sound').setAttribute('aria-pressed', String(soundOn));
    if (soundOn) tone(440,.1); updateMusic();
  });
  document.addEventListener('visibilitychange', updateMusic);

  async function post(action, body = {}) {
    const response = await fetch(`/api/games/${slug}/${action}`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    const data = await response.json().catch(() => ({error:'The game server returned an unexpected response.'}));
    if (!response.ok) throw new Error(data.error || 'The game could not save this wave.');
    return data;
  }
  function feedback(message, good) {
    const area = $('game-feedback');
    area.textContent = message;
    area.className = `game-feedback ${good === true ? 'correct' : good === false ? 'incorrect' : ''}`;
  }
  function stopMotion() { cancelAnimationFrame(frame); clearInterval(snakeTimer); frame = 0; snakeTimer = 0; }
  function updateStatus() {
    $('round-count').textContent = `Wave ${wave}/10`;
    $('run-score').textContent = `Score ${score}/100`;
  }
  function finish(result) {
    ended = true; busy = true; stopMotion();
    $('game-prompt').textContent = `GAME OVER · ${score}/100`;
    $('best-score').textContent = `${result.best}/100`;
    ['snake-game','bits-game','packet-game','challenge-game'].forEach(id => { $(id).hidden = true; });
    $('timer').textContent = '';
    $('play-again').hidden = false;
  }
  async function answer(value) {
    if (busy || ended) return;
    busy = true; stopMotion();
    try {
      const result = await post('answer', {answer:value});
      score = result.score; updateStatus();
      feedback(`${result.correct ? 'HIT!' : 'MISS!'} ${result.explanation}`, result.correct);
      effect(result.correct ? 'hit' : 'miss');
      if (slug === 'packet-patrol') drawPacket(performance.now());
      if (['logic-defender','ctrl-alt-defeat','cpu-tower'].includes(slug)) drawChallenge(performance.now());
      if (result.finished) { finish(result); return; }
      feedbackTimer = setTimeout(() => { wave += 1; showWave(result.next); }, 1050);
    } catch (error) {
      feedback(error.message, false);
      $('play-again').hidden = false;
    }
  }
  function showWave(next) {
    challenge = next; busy = false; ended = false; firing = false; waveStarted = performance.now();
    $('play-again').hidden = true; $('next-round').hidden = true;
    ['snake-game','bits-game','packet-game','challenge-game'].forEach(id => { $(id).hidden = true; });
    updateStatus(); feedback('', null);
    $('round-category').textContent = next.category || (slug === 'hex-snake' ? 'HEX HUNT' : 'HEX INVADERS');
    if (slug === 'hex-snake') {
      $('snake-game').hidden = false;
      $('game-prompt').textContent = 'CATCH THE RIGHT HEX TILE';
      $('snake-target').textContent = next.prompt;
      placeFruit(); drawSnake();
      if (direction.x || direction.y) snakeTimer = setInterval(stepSnake, Math.max(290, 430 - wave * 12));
    } else if (slug === 'bit-flip') {
      $('bits-game').hidden = false;
      $('game-prompt').textContent = 'FLIP THE BITS. FIRE BEFORE IMPACT!';
      selectedInvader = 0; bits = Array(8).fill(0); renderInvaderSelect(); renderBits();
      frame = requestAnimationFrame(animateInvader);
    } else if (slug === 'packet-patrol') {
      $('packet-game').hidden = false;
      $('game-prompt').textContent = next.prompt;
      selectedLane = 0; renderPacketOptions();
      frame = requestAnimationFrame(animatePacket);
    } else {
      $('challenge-game').hidden = false;
      $('game-prompt').textContent = next.prompt;
      selectedLane = 0; renderChallengeOptions();
      frame = requestAnimationFrame(animateChallenge);
    }
  }
  async function start() {
    clearTimeout(feedbackTimer); stopMotion(); busy = true; ended = false;
    $('play-again').hidden = true; $('timer').textContent = '';
    try {
      const data = await post('start');
      wave = 1; score = 0; lives = 3;
      snake = [{x:4,y:4}]; direction = {x:0,y:0}; nextDirection = {x:0,y:0};
      $('snake-lives').textContent = '♥ ♥ ♥';
      showWave(data.challenge);
    } catch (error) { feedback(error.message, false); $('play-again').hidden = false; }
  }

  // Classic continuous snake: new hex targets appear without resetting the trail.
  function placeFruit() {
    const free = [];
    for (let y=0; y<9; y++) for (let x=0; x<9; x++) {
      if (!snake.some(part => part.x === x && part.y === y) && Math.abs(x - snake[0].x) + Math.abs(y - snake[0].y) > 1) free.push({x,y});
    }
    for (let i=free.length-1; i>0; i--) { const j=Math.floor(Math.random()*(i+1)); [free[i],free[j]]=[free[j],free[i]]; }
    fruit = challenge.choices.map((label,index) => ({...free[index],label}));
  }
  function drawSnake() {
    const ctx = snakeCtx;
    ctx.fillStyle = '#061638'; ctx.fillRect(0,0,450,450);
    ctx.strokeStyle = '#1c4175'; ctx.lineWidth = 1;
    for (let i=0;i<=9;i++) { ctx.beginPath();ctx.moveTo(i*50,0);ctx.lineTo(i*50,450);ctx.stroke();ctx.beginPath();ctx.moveTo(0,i*50);ctx.lineTo(450,i*50);ctx.stroke(); }
    fruit.forEach((item,index) => {
      const x=item.x*50,y=item.y*50;
      ctx.fillStyle = ['#ff45bd','#00e6ff','#ffcb36','#adff4e'][index];
      ctx.shadowColor=ctx.fillStyle;ctx.shadowBlur=13;ctx.fillRect(x+5,y+5,40,40);ctx.shadowBlur=0;
      ctx.fillStyle='#09112b';ctx.font='900 19px monospace';ctx.textAlign='center';ctx.fillText(item.label,x+25,y+32);
    });
    snake.forEach((part,index) => {
      const x=part.x*50,y=part.y*50;
      ctx.fillStyle=index===0?'#fff15c':'#adff4e';ctx.shadowColor=ctx.fillStyle;ctx.shadowBlur=index===0?18:8;
      ctx.fillRect(x+5,y+5,40,40);ctx.shadowBlur=0;
      if(index===0){ctx.fillStyle='#071126';ctx.fillRect(x+29,y+15,5,5);ctx.fillRect(x+29,y+29,5,5);}
    });
  }
  function crash() {
    lives -= 1;
    $('snake-lives').textContent = `${'♥ '.repeat(lives)}${'♡ '.repeat(3-lives)}`;
    if (lives === 0) {
      lives=3;$('snake-lives').textContent='♥ ♥ ♥';
      snake=[{x:4,y:4}];direction={x:0,y:0};nextDirection={x:0,y:0};
      // A crash uses an intentionally invalid response, scored as a miss server-side.
      answer('CRASH');
    } else {
      snake=[{x:4,y:4}];direction={x:0,y:0};nextDirection={x:0,y:0};
      clearInterval(snakeTimer);snakeTimer=0;placeFruit();drawSnake();feedback('CRASH! Steer again to keep hunting.', false);
    }
  }
  function stepSnake() {
    if (busy || (!nextDirection.x && !nextDirection.y)) return;
    direction=nextDirection;
    const head={x:snake[0].x+direction.x,y:snake[0].y+direction.y};
    const prize=fruit.find(item=>item.x===head.x&&item.y===head.y);
    if(head.x<0||head.y<0||head.x>=9||head.y>=9||(prize?snake:snake.slice(0,-1)).some(part=>part.x===head.x&&part.y===head.y)){crash();return;}
    snake.unshift(head);
    if(!prize) snake.pop();
    drawSnake();
    if(prize) answer(prize.label);
  }
  function steer(x,y) {
    if(slug!=='hex-snake'||busy||ended)return;
    if(snake.length>1&&direction.x===-x&&direction.y===-y)return;
    nextDirection={x,y};
    if(!snakeTimer) effect('flip');
    if(!snakeTimer)snakeTimer=setInterval(stepSnake,Math.max(290,430-wave*12));
  }
  document.querySelectorAll('[data-direction]').forEach(button=>button.addEventListener('click',()=>{
    const vectors={up:[0,-1],down:[0,1],left:[-1,0],right:[1,0]};steer(...vectors[button.dataset.direction]);
  }));
  let touchPoint=null;
  snakeCanvas.addEventListener('touchstart',e=>{touchPoint=[e.touches[0].clientX,e.touches[0].clientY];},{passive:true});
  snakeCanvas.addEventListener('touchend',e=>{
    if(!touchPoint)return;
    const dx=e.changedTouches[0].clientX-touchPoint[0],dy=e.changedTouches[0].clientY-touchPoint[1];
    if(Math.max(Math.abs(dx),Math.abs(dy))>20)steer(Math.abs(dx)>Math.abs(dy)?Math.sign(dx):0,Math.abs(dy)>Math.abs(dx)?Math.sign(dy):0);
    touchPoint=null;
  },{passive:true});
  snakeCanvas.addEventListener('click',()=>{if(!snakeTimer)steer(1,0);});

  // Falling hex invader: flip switches while the target advances.
  function renderBits() {
    const holder=$('bit-buttons');holder.replaceChildren();
    [128,64,32,16,8,4,2,1].forEach((weight,index)=>{
      const button=document.createElement('button');button.type='button';button.className='bit-switch';
      button.innerHTML=`<span>${weight}</span><strong>0</strong>`;
      button.setAttribute('aria-label',`Toggle ${weight} bit`);
      button.addEventListener('click',()=>{if(busy||firing)return;bits[index]^=1;updateBits();effect('flip');});holder.append(button);
    });updateBits();
  }
  function updateBits() {
    const binary=bits.join(''),value=parseInt(binary,2);
    $('binary-value').textContent=binary;$('decimal-value').textContent=String(value);
    $('hex-value').textContent=value.toString(16).toUpperCase().padStart(2,'0');
    [...$('bit-buttons').children].forEach((button,index)=>{button.classList.toggle('is-on',!!bits[index]);button.setAttribute('aria-pressed',String(!!bits[index]));button.querySelector('strong').textContent=String(bits[index]);});
  }
  function renderInvaderSelect() {
    const holder=$('invader-select');holder.replaceChildren();
    challenge.targets.forEach((target,index)=>{
      const button=document.createElement('button');button.type='button';button.className='invader-choice';
      button.textContent=`INVADER ${index+1} · ${target}`;
      button.addEventListener('click',()=>selectInvader(index));holder.append(button);
    });updateInvaderSelection();
  }
  function selectInvader(index){if(busy||firing)return;selectedInvader=index;updateInvaderSelection();effect('flip');}
  function updateInvaderSelection(){
    $('bit-target').textContent=challenge.targets[selectedInvader];
    [...$('invader-select').children].forEach((button,index)=>{
      button.classList.toggle('selected',index===selectedInvader);
      button.setAttribute('aria-pressed',String(index===selectedInvader));
    });
  }
  function drawBackground(ctx,width,height,now) {
    const gradient=ctx.createLinearGradient(0,0,0,height);gradient.addColorStop(0,'#0752ad');gradient.addColorStop(1,'#1a0b5c');
    ctx.fillStyle=gradient;ctx.fillRect(0,0,width,height);
    for(let i=0;i<44;i++){const x=(i*137+47)%width,y=(i*83+now*.012*(i%3+1))%height;ctx.fillStyle=i%3?'#9eeaff':'#fffbb1';ctx.fillRect(x,y,2+(i%3),2+(i%3));}
    ctx.fillStyle='#401858';ctx.fillRect(0,height-31,width,31);ctx.fillStyle='#fbcc34';ctx.fillRect(0,height-34,width,4);
  }
  function drawInvader(now) {
    const ctx=invaderCtx,w=420,h=650,progress=Math.min(1,(now-waveStarted)/22000);
    drawBackground(ctx,w,h,now);
    const pattern=['00111100','01111110','11111111','11011011','11111111','10100101','00100100'];
    const positions=[];
    challenge.targets.forEach((target,index)=>{
      const x=80+index*130+Math.sin(now/570+index)*14;
      const y=95+progress*395+index*42;
      positions.push({x,y});
      ctx.fillStyle=['#ff37a6','#ffcf36','#a7ff51'][index];ctx.shadowColor=ctx.fillStyle;ctx.shadowBlur=15;
      pattern.forEach((row,ry)=>[...row].forEach((cell,rx)=>{if(cell==='1')ctx.fillRect(x-40+rx*10,y-36+ry*10,9,9);}));ctx.shadowBlur=0;
      ctx.fillStyle='#14002f';ctx.fillRect(x-30,y-14,61,34);
      ctx.font='900 25px monospace';ctx.textAlign='center';ctx.fillStyle='#fff';ctx.fillText(target,x,y+11);
      if(index===selectedInvader){ctx.strokeStyle='#00f0ff';ctx.lineWidth=3;ctx.strokeRect(x-46,y-43,92,79);}
    });
    const selected=positions[selectedInvader];
    ctx.fillStyle='#e7f8ff';ctx.fillRect(selected.x-18,h-65,36,31);ctx.fillStyle='#00e6ff';ctx.fillRect(selected.x-5,h-79,10,18);
    if(now<flashUntil){const matched=parseInt(bits.join(''),2).toString(16).toUpperCase().padStart(2,'0')===challenge.targets[selectedInvader];ctx.fillStyle=matched?'#fff94a':'#ff4abf';ctx.shadowColor=ctx.fillStyle;ctx.shadowBlur=24;ctx.fillRect(selected.x-3,selected.y+43,6,h-selected.y-90);ctx.shadowBlur=0;ctx.fillStyle=matched?'#fff':'#ff8bd6';ctx.beginPath();ctx.arc(selected.x,selected.y,Math.max(8,(flashUntil-now)/9),0,Math.PI*2);ctx.fill();}
    ctx.fillStyle='#ffcc32';ctx.fillRect(0,h-12,(1-progress)*w,8);
  }
  function animateInvader(now) {
    if(busy||ended)return;
    drawInvader(now);
    if(firing && now>=flashUntil){firing=false;answer(`${selectedInvader}:${bits.join('')}`);return;}
    const remaining=Math.max(0,Math.ceil((22000-(now-waveStarted))/1000));$('timer').textContent=`${remaining}s TO IMPACT`;
    if(remaining===0 && !firing){answer('TIMEOUT');return;}
    frame=requestAnimationFrame(animateInvader);
  }
  function fireBits(){if(busy||ended||firing)return;firing=true;flashUntil=performance.now()+550;effect('fire');}
  $('bits-submit').addEventListener('click',fireBits);
  invaderCanvas.addEventListener('click',event=>{
    const rect=invaderCanvas.getBoundingClientRect();
    selectInvader(Math.min(2,Math.max(0,Math.floor((event.clientX-rect.left)/rect.width*3))));
  });

  // Moving packet: steer into the lane representing the correct decision.
  function renderPacketOptions() {
    const holder=$('packet-options');holder.replaceChildren();
    challenge.choices.forEach((choice,index)=>{
      const button=document.createElement('button');button.type='button';button.className='packet-option';button.textContent=`${index+1} · ${choice}`;
      button.addEventListener('click',()=>{selectedLane=index;updateLanes();effect('flip');});holder.append(button);
    });updateLanes();
  }
  function updateLanes(){[...$('packet-options').children].forEach((button,index)=>button.classList.toggle('selected',index===selectedLane));}
  function drawPacket(now) {
    const ctx=packetCtx,w=760,h=350,progress=Math.min(1,(now-waveStarted)/19000);
    drawBackground(ctx,w,h,now);
    for(let lane=0;lane<4;lane++){
      const x=lane*190+6;ctx.fillStyle=lane===selectedLane?'rgba(0,240,255,.22)':'rgba(255,255,255,.08)';ctx.fillRect(x,0,178,h-35);
      ctx.strokeStyle=lane===selectedLane?'#00eaff':'#5263ba';ctx.lineWidth=lane===selectedLane?4:2;ctx.strokeRect(x+4,6,170,h-48);
      ctx.fillStyle='#fff';ctx.font='900 25px monospace';ctx.textAlign='center';ctx.fillText(String(lane+1),x+89,h-52);
    }
    const x=selectedLane*190+95,y=35+progress*245;
    ctx.fillStyle='#ffcf36';ctx.shadowColor='#ffcf36';ctx.shadowBlur=18;ctx.beginPath();ctx.arc(x,y,20,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;
    ctx.fillStyle='#061638';ctx.font='900 18px monospace';ctx.fillText('◆',x,y+7);
    ctx.fillStyle='#ffcc32';ctx.fillRect(0,h-12,(1-progress)*w,8);
  }
  function animatePacket(now) {
    if(busy||ended)return;
    drawPacket(now);
    const remaining=Math.max(0,Math.ceil((19000-(now-waveStarted))/1000));$('timer').textContent=`${remaining}s TO GATE`;
    if(remaining===0){answer('TIMEOUT');return;}
    frame=requestAnimationFrame(animatePacket);
  }
  function moveLane(delta){selectedLane=(selectedLane+delta+4)%4;updateLanes();}
  $('packet-submit').addEventListener('click',()=>answer(challenge.choices[selectedLane]));
  packetCanvas.addEventListener('click',event=>{const rect=packetCanvas.getBoundingClientRect();selectedLane=Math.min(3,Math.floor((event.clientX-rect.left)/rect.width*4));updateLanes();});

  // Three distinct arcade scenes share the same server-marked question rounds.
  function renderChallengeOptions() {
    const holder=$('challenge-options');holder.replaceChildren();
    challenge.choices.forEach((choice,index)=>{
      const button=document.createElement('button');button.type='button';button.className='packet-option';
      button.textContent=`${index+1} · ${choice}`;
      button.addEventListener('click',()=>{if(firing||busy)return;selectedLane=index;updateChallengeLanes();effect('flip');});holder.append(button);
    });updateChallengeLanes();
  }
  function updateChallengeLanes(){[...$('challenge-options').children].forEach((button,index)=>button.classList.toggle('selected',index===selectedLane));}
  function drawChallenge(now) {
    const ctx=challengeCtx,w=760,h=480,elapsed=now-waveStarted;
    const limit=slug==='cpu-tower'?24000:20000,progress=Math.min(1,elapsed/limit);
    drawBackground(ctx,w,h,now);
    const lanes=[95,285,475,665],x=lanes[selectedLane];
    if(slug==='logic-defender') {
      ctx.fillStyle='#07102f';ctx.fillRect(0,h-76,w,53);
      ctx.fillStyle='#00eaff';ctx.shadowColor='#00eaff';ctx.shadowBlur=20;
      ctx.beginPath();ctx.arc(w/2,h-54,27,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;
      lanes.forEach((lane,index)=>{
        ctx.fillStyle=index===selectedLane?'#adff4e':'#7255c8';ctx.fillRect(lane-34,h-113,68,40);
        ctx.fillStyle='#09132f';ctx.font='900 22px monospace';ctx.textAlign='center';ctx.fillText(String(index+1),lane,h-86);
      });
      for(let i=0;i<3;i++){
        const hx=125+i*245+Math.sin(now/350+i)*25,hy=35+((progress+i*.17)%1)*300;
        ctx.fillStyle='#ff3baf';ctx.shadowColor='#ff3baf';ctx.shadowBlur=16;ctx.beginPath();ctx.arc(hx,hy,20,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;
        ctx.fillStyle='#fff';ctx.font='900 19px monospace';ctx.fillText('!',hx,hy+7);
      }
      if(now<flashUntil){ctx.strokeStyle='#adff4e';ctx.lineWidth=11;ctx.shadowColor='#adff4e';ctx.shadowBlur=25;ctx.beginPath();ctx.moveTo(x,h-113);ctx.lineTo(x,50);ctx.stroke();ctx.shadowBlur=0;}
    } else if(slug==='ctrl-alt-defeat') {
      for(let i=0;i<5;i++){
        const vx=75+i*150+Math.sin(now/460+i)*24,vy=45+((progress+i*.15)%1)*295;
        ctx.fillStyle='#ff3baf';ctx.shadowColor='#ff3baf';ctx.shadowBlur=14;ctx.fillRect(vx-24,vy-17,48,34);ctx.shadowBlur=0;
        ctx.fillStyle='#fff';ctx.font='900 19px monospace';ctx.textAlign='center';ctx.fillText('X',vx,vy+7);
      }
      ctx.fillStyle='#00eaff';ctx.shadowColor='#00eaff';ctx.shadowBlur=24;
      ctx.beginPath();ctx.moveTo(x,h-92);ctx.lineTo(x-30,h-34);ctx.lineTo(x+30,h-34);ctx.closePath();ctx.fill();ctx.shadowBlur=0;
      if(now<flashUntil){ctx.strokeStyle='#fff84d';ctx.lineWidth=8;ctx.beginPath();ctx.moveTo(x,h-94);ctx.lineTo(x,25);ctx.stroke();}
    } else {
      lanes.forEach((lane,index)=>{
        const top=h-100-progress*295;
        ctx.fillStyle=index===selectedLane?'#adff4e':'#5b73d2';ctx.fillRect(lane-52,top,104,14);
        ctx.fillStyle='#fff';ctx.font='900 20px monospace';ctx.textAlign='center';ctx.fillText(String(index+1),lane,top-14);
      });
      const heroY=now<flashUntil?h-110-Math.min(260,(520-(flashUntil-now))*.55):h-110;
      ctx.fillStyle='#ffcf36';ctx.shadowColor='#ffcf36';ctx.shadowBlur=22;ctx.fillRect(x-16,heroY-38,32,35);ctx.fillRect(x-20,heroY-3,40,9);ctx.shadowBlur=0;
      ctx.fillStyle='#fff';ctx.font='bold 18px monospace';ctx.textAlign='center';ctx.fillText('CPU TOWER',w/2,37);
    }
    ctx.fillStyle='#ffcf36';ctx.fillRect(0,h-10,(1-progress)*w,7);
  }
  function animateChallenge(now) {
    if(busy||ended)return;
    drawChallenge(now);
    if(firing && now>=flashUntil){firing=false;answer(challenge.choices[selectedLane]);return;}
    const limit=slug==='cpu-tower'?24000:20000;
    const remaining=Math.max(0,Math.ceil((limit-(now-waveStarted))/1000));
    $('timer').textContent=`${remaining}s TO ${slug==='cpu-tower'?'JUMP':'IMPACT'}`;
    if(remaining===0 && !firing){answer('TIMEOUT');return;}
    frame=requestAnimationFrame(animateChallenge);
  }
  function actChallenge(){if(busy||ended||firing)return;firing=true;flashUntil=performance.now()+520;effect('fire');}
  $('challenge-submit').addEventListener('click',actChallenge);
  challengeCanvas.addEventListener('click',event=>{
    if(firing||busy)return;const rect=challengeCanvas.getBoundingClientRect();selectedLane=Math.min(3,Math.floor((event.clientX-rect.left)/rect.width*4));updateChallengeLanes();
  });

  document.addEventListener('keydown',event=>{
    if(event.target.matches('input,textarea,select'))return;
    if(!challenge||busy||ended||firing)return;
    if(slug==='hex-snake'){
      const vectors={ArrowUp:[0,-1],ArrowDown:[0,1],ArrowLeft:[-1,0],ArrowRight:[1,0],w:[0,-1],s:[0,1],a:[-1,0],d:[1,0]};
      if(vectors[event.key]){event.preventDefault();steer(...vectors[event.key]);}
    } else if(slug==='bit-flip'){
      if(/^[1-8]$/.test(event.key)){event.preventDefault();const index=Number(event.key)-1;bits[index]^=1;updateBits();}
      if(event.key==='ArrowLeft'){event.preventDefault();selectInvader((selectedInvader+2)%3);}
      if(event.key==='ArrowRight'){event.preventDefault();selectInvader((selectedInvader+1)%3);}
      if(event.code==='Space'){event.preventDefault();fireBits();}
    } else if(slug==='packet-patrol') {
      if(event.key==='ArrowLeft'){event.preventDefault();moveLane(-1);}
      if(event.key==='ArrowRight'){event.preventDefault();moveLane(1);}
      if(/^[1-4]$/.test(event.key)){selectedLane=Number(event.key)-1;updateLanes();}
      if(event.code==='Space'){event.preventDefault();answer(challenge.choices[selectedLane]);}
    } else {
      if(event.key==='ArrowLeft'){event.preventDefault();selectedLane=(selectedLane+3)%4;updateChallengeLanes();}
      if(event.key==='ArrowRight'){event.preventDefault();selectedLane=(selectedLane+1)%4;updateChallengeLanes();}
      if(/^[1-4]$/.test(event.key)){selectedLane=Number(event.key)-1;updateChallengeLanes();}
      if(event.code==='Space'){event.preventDefault();actChallenge();}
    }
  });
  $('play-again').addEventListener('click',start);
  start();
})();
