(() => {
  const root = document.querySelector('[data-game]');
  if (!root) return;
  const slug = root.dataset.game;
  const $ = id => document.getElementById(id);
  let challenge, wave = 1, score = 0, busy = false, ended = false;
  let frame = 0, waveStarted = 0, feedbackTimer = 0, selectedLane = 0, flashUntil = 0;
  let snakeTimer = 0, snake = [{x:4,y:4}], direction = {x:0,y:0}, nextDirection = {x:0,y:0}, fruit = [], lives = 3;
  let bits = Array(8).fill(0);
  const snakeCanvas = $('snake-canvas'), snakeCtx = snakeCanvas.getContext('2d');
  const invaderCanvas = $('invader-canvas'), invaderCtx = invaderCanvas.getContext('2d');
  const packetCanvas = $('packet-canvas'), packetCtx = packetCanvas.getContext('2d');

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
    ['snake-game','bits-game','packet-game'].forEach(id => { $(id).hidden = true; });
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
      flashUntil = performance.now() + 850;
      if (slug === 'bit-flip') drawInvader(performance.now());
      if (slug === 'packet-patrol') drawPacket(performance.now());
      if (result.finished) { finish(result); return; }
      feedbackTimer = setTimeout(() => { wave += 1; showWave(result.next); }, 1050);
    } catch (error) {
      feedback(error.message, false);
      $('play-again').hidden = false;
    }
  }
  function showWave(next) {
    challenge = next; busy = false; ended = false; waveStarted = performance.now();
    $('play-again').hidden = true; $('next-round').hidden = true;
    ['snake-game','bits-game','packet-game'].forEach(id => { $(id).hidden = true; });
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
      bits = Array(8).fill(0); renderBits();
      frame = requestAnimationFrame(animateInvader);
    } else {
      $('packet-game').hidden = false;
      $('game-prompt').textContent = next.prompt;
      selectedLane = 0; renderPacketOptions();
      frame = requestAnimationFrame(animatePacket);
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
      button.addEventListener('click',()=>{bits[index]^=1;updateBits();});holder.append(button);
    });updateBits();
  }
  function updateBits() {
    const binary=bits.join(''),value=parseInt(binary,2);
    $('binary-value').textContent=binary;$('decimal-value').textContent=String(value);
    $('hex-value').textContent=value.toString(16).toUpperCase().padStart(2,'0');
    [...$('bit-buttons').children].forEach((button,index)=>{button.classList.toggle('is-on',!!bits[index]);button.setAttribute('aria-pressed',String(!!bits[index]));button.querySelector('strong').textContent=String(bits[index]);});
  }
  function drawBackground(ctx,width,height,now) {
    const gradient=ctx.createLinearGradient(0,0,0,height);gradient.addColorStop(0,'#0752ad');gradient.addColorStop(1,'#1a0b5c');
    ctx.fillStyle=gradient;ctx.fillRect(0,0,width,height);
    for(let i=0;i<44;i++){const x=(i*137+47)%width,y=(i*83+now*.012*(i%3+1))%height;ctx.fillStyle=i%3?'#9eeaff':'#fffbb1';ctx.fillRect(x,y,2+(i%3),2+(i%3));}
    ctx.fillStyle='#401858';ctx.fillRect(0,height-31,width,31);ctx.fillStyle='#fbcc34';ctx.fillRect(0,height-34,width,4);
  }
  function drawInvader(now) {
    const ctx=invaderCtx,w=760,h=350,progress=Math.min(1,(now-waveStarted)/23000);
    drawBackground(ctx,w,h,now);
    const x=380+Math.sin(now/480)*160,y=56+progress*215;
    const pattern=['00111100','01111110','11111111','11011011','11111111','10100101','00100100'];
    ctx.fillStyle='#ff37a6';ctx.shadowColor='#ff37a6';ctx.shadowBlur=18;
    pattern.forEach((row,ry)=>[...row].forEach((cell,rx)=>{if(cell==='1')ctx.fillRect(x-48+rx*12,y-42+ry*12,11,11);}));ctx.shadowBlur=0;
    ctx.fillStyle='#14002f';ctx.fillRect(x-34,y-17,69,39);
    ctx.font='900 29px monospace';ctx.textAlign='center';ctx.fillStyle='#fff';ctx.fillText(challenge.target,x,y+12);
    ctx.fillStyle='#e7f8ff';ctx.fillRect(w/2-18,h-65,36,31);ctx.fillStyle='#00e6ff';ctx.fillRect(w/2-5,h-79,10,18);
    if(now<flashUntil){ctx.fillStyle='#fff94a';ctx.fillRect(w/2-3,y+43,6,h-y-90);}
    ctx.fillStyle='#ffcc32';ctx.fillRect(0,h-12,(1-progress)*w,8);
  }
  function animateInvader(now) {
    if(busy||ended)return;
    drawInvader(now);
    const remaining=Math.max(0,Math.ceil((23000-(now-waveStarted))/1000));$('timer').textContent=`${remaining}s TO IMPACT`;
    if(remaining===0){answer(bits.join(''));return;}
    frame=requestAnimationFrame(animateInvader);
  }
  $('bits-submit').addEventListener('click',()=>{flashUntil=performance.now()+500;answer(bits.join(''));});

  // Moving packet: steer into the lane representing the correct decision.
  function renderPacketOptions() {
    const holder=$('packet-options');holder.replaceChildren();
    challenge.choices.forEach((choice,index)=>{
      const button=document.createElement('button');button.type='button';button.className='packet-option';button.textContent=`${index+1} · ${choice}`;
      button.addEventListener('click',()=>{selectedLane=index;updateLanes();});holder.append(button);
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
    if(remaining===0){answer(challenge.choices[selectedLane]);return;}
    frame=requestAnimationFrame(animatePacket);
  }
  function moveLane(delta){selectedLane=(selectedLane+delta+4)%4;updateLanes();}
  $('packet-submit').addEventListener('click',()=>answer(challenge.choices[selectedLane]));
  packetCanvas.addEventListener('click',event=>{const rect=packetCanvas.getBoundingClientRect();selectedLane=Math.min(3,Math.floor((event.clientX-rect.left)/rect.width*4));updateLanes();});

  document.addEventListener('keydown',event=>{
    if(event.target.matches('input,textarea,select'))return;
    if(!challenge||busy||ended)return;
    if(slug==='hex-snake'){
      const vectors={ArrowUp:[0,-1],ArrowDown:[0,1],ArrowLeft:[-1,0],ArrowRight:[1,0],w:[0,-1],s:[0,1],a:[-1,0],d:[1,0]};
      if(vectors[event.key]){event.preventDefault();steer(...vectors[event.key]);}
    } else if(slug==='bit-flip'){
      if(/^[1-8]$/.test(event.key)){event.preventDefault();const index=Number(event.key)-1;bits[index]^=1;updateBits();}
      if(event.code==='Space'){event.preventDefault();answer(bits.join(''));}
    } else {
      if(event.key==='ArrowLeft'){event.preventDefault();moveLane(-1);}
      if(event.key==='ArrowRight'){event.preventDefault();moveLane(1);}
      if(/^[1-4]$/.test(event.key)){selectedLane=Number(event.key)-1;updateLanes();}
      if(event.code==='Space'){event.preventDefault();answer(challenge.choices[selectedLane]);}
    }
  });
  $('play-again').addEventListener('click',start);
  start();
})();
