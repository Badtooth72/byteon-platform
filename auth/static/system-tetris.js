(() => {
  'use strict';
  const $=id=>document.getElementById(id),COLS=10,ROWS=20,CELL=27,BX=65,BY=30,W=400,H=600;
  const pieces=[
    {name:'RAM',colour:0x2ddff4,shape:[[0,0],[1,0],[2,0],[3,0]],detail:'Random access memory holds programs and data currently in use.'},
    {name:'Cache',colour:0xffd448,shape:[[0,0],[1,0],[0,1],[1,1]],detail:'Cache holds frequently used data close to the CPU for fast access.'},
    {name:'ALU',colour:0xff66b6,shape:[[0,0],[1,0],[2,0],[1,1]],detail:'The arithmetic logic unit performs calculations and logical comparisons.'},
    {name:'CU',colour:0xb8ff65,shape:[[1,0],[2,0],[0,1],[1,1]],detail:'The control unit coordinates the fetch–decode–execute cycle.'},
    {name:'MAR',colour:0xff8956,shape:[[0,0],[1,0],[1,1],[2,1]],detail:'The memory address register holds the address in memory being accessed.'},
    {name:'MDR',colour:0x9985ff,shape:[[0,0],[0,1],[1,1],[2,1]],detail:'The memory data register holds data moving to or from memory.'},
    {name:'PC',colour:0x65adff,shape:[[2,0],[0,1],[1,1],[2,1]],detail:'The program counter holds the address of the next instruction.'},
    {name:'Accumulator',colour:0xff6c76,shape:[[0,0],[1,0],[0,1],[1,1],[0,2]],detail:'The accumulator stores intermediate results of calculations.'},
    {name:'Motherboard',colour:0xe2dc8f,shape:[[0,0],[2,0],[0,1],[1,1],[2,1]],detail:'The motherboard connects components so they can communicate.'}
  ];
  let scene,graphics,label,board=[],active,next,bag=[],phase='intro',runId=null,lines=0,level=1,best=Number($('ts-best').textContent)||0;
  let fallClock=0,soundOn=true,audio;
  function beep(frequency,duration=.07,volume=.025){
    if(!soundOn)return;
    try{audio ||=new(window.AudioContext||window.webkitAudioContext)();if(audio.state==='suspended')audio.resume();
      const oscillator=audio.createOscillator(),gain=audio.createGain(),now=audio.currentTime;
      oscillator.type='square';oscillator.frequency.setValueAtTime(frequency,now);oscillator.frequency.exponentialRampToValueAtTime(Math.max(40,frequency*.6),now+duration);
      gain.gain.setValueAtTime(volume,now);gain.gain.exponentialRampToValueAtTime(.0001,now+duration);
      oscillator.connect(gain);gain.connect(audio.destination);oscillator.start(now);oscillator.stop(now+duration+.01);
    }catch(_){/* Silent play remains available. */}
  }
  function randomPiece(){
    if(!bag.length){bag=pieces.slice();for(let i=bag.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[bag[i],bag[j]]=[bag[j],bag[i]];}}
    return bag.pop();
  }
  function updateHud(){
    $('ts-lines').textContent=lines;$('ts-level').textContent=level;$('ts-best').textContent=best;
    if(active){$('ts-component').textContent=active.def.name;$('ts-description').textContent=active.def.detail;}
    $('ts-next-name').textContent=next?.name||'—';drawNext();
  }
  function drawNext(){
    const canvas=$('ts-next'),ctx=canvas.getContext('2d');ctx.clearRect(0,0,canvas.width,canvas.height);
    if(!next)return;
    const minX=Math.min(...next.shape.map(c=>c[0])),maxX=Math.max(...next.shape.map(c=>c[0]));
    const minY=Math.min(...next.shape.map(c=>c[1])),maxY=Math.max(...next.shape.map(c=>c[1]));
    const size=25,left=(canvas.width-(maxX-minX+1)*size)/2,top=(canvas.height-(maxY-minY+1)*size)/2;
    const color=`#${next.colour.toString(16).padStart(6,'0')}`;
    next.shape.forEach(([x,y])=>{const px=left+(x-minX)*size,py=top+(y-minY)*size;ctx.fillStyle=color;ctx.fillRect(px+1,py+1,size-2,size-2);ctx.fillStyle='#ffffff77';ctx.fillRect(px+3,py+3,size-7,3);ctx.strokeStyle='#06132a';ctx.strokeRect(px+1,py+1,size-2,size-2);});
  }
  function fits(shape,x,y){return shape.every(([dx,dy])=>{const cx=x+dx,cy=y+dy;return cx>=0&&cx<COLS&&cy<ROWS&&(cy<0||!board[cy][cx]);});}
  function show(kicker,title,copy,button){$('ts-kicker').textContent=kicker;$('ts-title').textContent=title;$('ts-copy').textContent=copy;$('ts-action').textContent=button;$('ts-overlay').hidden=false;}
  function spawn(){
    const def=next||randomPiece();next=randomPiece();active={def,shape:def.shape.map(cell=>cell.slice()),x:3,y:0};
    updateHud();
    if(!fits(active.shape,active.x,active.y))endGame();
  }
  function lock(){
    if(phase!=='playing')return;
    for(const [dx,dy] of active.shape){const y=active.y+dy;if(y<0){endGame();return;}board[y][active.x+dx]=active.def.colour;}
    const remaining=board.filter(row=>row.some(cell=>!cell)),cleared=ROWS-remaining.length;
    if(cleared){while(remaining.length<ROWS)remaining.unshift(Array(COLS).fill(null));board=remaining;lines+=cleared;level=1+Math.floor(lines/5);beep(490+cleared*90,.25,.055);}
    else beep(175,.065,.018);
    spawn();
  }
  function move(dx,dy){
    if(phase!=='playing')return false;
    if(fits(active.shape,active.x+dx,active.y+dy)){active.x+=dx;active.y+=dy;if(dx)beep(260,.025,.009);return true;}
    if(dy>0)lock();return false;
  }
  function rotate(){
    if(phase!=='playing')return;
    const rotated=active.shape.map(([x,y])=>[-y,x]);
    const minX=Math.min(...rotated.map(c=>c[0])),minY=Math.min(...rotated.map(c=>c[1]));
    rotated.forEach(c=>{c[0]-=minX;c[1]-=minY;});
    for(const offset of [0,-1,1,-2,2])if(fits(rotated,active.x+offset,active.y)){active.shape=rotated;active.x+=offset;beep(430,.05);return;}
  }
  function drop(){
    if(phase!=='playing')return;
    while(fits(active.shape,active.x,active.y+1))active.y++;
    beep(590,.09,.035);lock();
  }
  async function startGame(){
    if(!scene||phase==='loading')return;
    phase='loading';$('ts-action').disabled=true;$('ts-copy').textContent='Starting your run…';
    try{
      const response=await fetch('/api/games/system-tetris/start',{method:'POST'}),data=await response.json();
      if(!response.ok)throw new Error(data.error||'Could not start the game.');
      runId=data.run_id;board=Array.from({length:ROWS},()=>Array(COLS).fill(null));bag=[];active=null;next=randomPiece();lines=0;level=1;fallClock=0;
      phase='playing';$('ts-overlay').hidden=true;$('ts-pause').textContent='PAUSE';spawn();beep(440,.16,.04);
    }catch(error){phase='intro';show('CONNECTION ERROR','COULD NOT START',error.message,'TRY AGAIN');}
    finally{$('ts-action').disabled=false;}
  }
  async function endGame(){
    if(phase!=='playing')return;
    phase='over';show('SYSTEM FULL','STACK COMPLETE',`${lines} line${lines===1?'':'s'} cleared. Saving your result…`,'PLAY AGAIN');
    $('ts-action').disabled=true;
    try{
      const response=await fetch('/api/games/system-tetris/finish',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({run_id:runId,lines})});
      const data=await response.json();if(!response.ok)throw new Error(data.error||'Could not save the run.');
      best=data.best;updateHud();$('ts-copy').textContent=`${lines} line${lines===1?'':'s'} cleared. Best saved run: ${best} line${best===1?'':'s'}.`;
    }catch(error){$('ts-copy').textContent=`${lines} lines cleared. Save failed: ${error.message}`;}
    finally{$('ts-action').disabled=false;}
    beep(140,.42,.045);
  }
  function pause(){
    if(phase==='playing'){phase='paused';show('PAUSED','TAKE A BREATH','Your stack is safe until you resume.','RESUME');$('ts-pause').textContent='RESUME';}
    else if(phase==='paused'){phase='playing';$('ts-overlay').hidden=true;$('ts-pause').textContent='PAUSE';}
  }
  function block(x,y,colour,alpha=1){
    const px=BX+x*CELL,py=BY+y*CELL;
    graphics.fillStyle(colour,alpha);graphics.fillRoundedRect(px+1,py+1,CELL-2,CELL-2,3);
    graphics.fillStyle(0xffffff,alpha*.28);graphics.fillRect(px+4,py+4,CELL-9,3);
    graphics.lineStyle(1,0x06132a,alpha);graphics.strokeRoundedRect(px+1,py+1,CELL-2,CELL-2,3);
  }
  function draw(time){
    graphics.clear();graphics.fillStyle(0x07162f);graphics.fillRect(0,0,W,H);
    for(let i=0;i<32;i++){graphics.fillStyle(i%3?0x3171a0:0x9beeff,.13+.12*Math.sin(time/800+i));graphics.fillRect((i*97+13)%W,(i*173+27)%H,2,2);}
    graphics.fillStyle(0x0a2341);graphics.fillRoundedRect(BX-6,BY-6,COLS*CELL+12,ROWS*CELL+12,6);
    graphics.lineStyle(2,0x24d9ef,.9);graphics.strokeRoundedRect(BX-6,BY-6,COLS*CELL+12,ROWS*CELL+12,6);
    graphics.lineStyle(1,0x1e385c,.65);
    for(let x=1;x<COLS;x++)graphics.lineBetween(BX+x*CELL,BY,BX+x*CELL,BY+ROWS*CELL);
    for(let y=1;y<ROWS;y++)graphics.lineBetween(BX,BY+y*CELL,BX+COLS*CELL,BY+y*CELL);
    board.forEach((row,y)=>row.forEach((colour,x)=>{if(colour)block(x,y,colour);}));
    if(active){
      let ghost=active.y;while(fits(active.shape,active.x,ghost+1))ghost++;
      active.shape.forEach(([x,y])=>{if(ghost+y>=0)block(active.x+x,ghost+y,active.def.colour,.22);});
      active.shape.forEach(([x,y])=>{if(active.y+y>=0)block(active.x+x,active.y+y,active.def.colour);});
      const centerX=active.x+Math.max(...active.shape.map(c=>c[0]))/2+.5;
      label.setText(active.def.name.toUpperCase()).setPosition(BX+centerX*CELL,BY+(active.y+1)*CELL).setVisible(phase!=='intro');
    }else label.setVisible(false);
    graphics.fillStyle(0x20dfef,.8);graphics.fillRect(BX-5,BY+ROWS*CELL+7,COLS*CELL+10,2);
  }
  new Phaser.Game({type:Phaser.AUTO,parent:'tetris-stage',width:W,height:H,backgroundColor:'#07162f',render:{pixelArt:true},
    scale:{mode:Phaser.Scale.FIT,autoCenter:Phaser.Scale.CENTER_BOTH,width:W,height:H},scene:{
      create(){scene=this;graphics=this.add.graphics();label=this.add.text(0,0,'',{fontFamily:'monospace',fontSize:'12px',fontStyle:'bold',color:'#06132a',stroke:'#ffffff',strokeThickness:2}).setOrigin(.5).setDepth(3).setVisible(false);},
      update(time,delta){if(phase==='playing'){fallClock+=Math.min(delta,100);const interval=Math.max(115,820-(level-1)*70);if(fallClock>=interval){fallClock=0;move(0,1);}}draw(time);}
    }});
  $('ts-action').addEventListener('click',()=>phase==='paused'?pause():startGame());
  $('ts-pause').addEventListener('click',pause);
  $('ts-sound').addEventListener('click',()=>{soundOn=!soundOn;$('ts-sound').textContent=soundOn?'SOUND ON':'SOUND OFF';$('ts-sound').setAttribute('aria-pressed',String(soundOn));});
  const actions={left:()=>move(-1,0),right:()=>move(1,0),down:()=>move(0,1),rotate,drop};
  document.querySelectorAll('[data-move]').forEach(button=>button.addEventListener('click',()=>actions[button.dataset.move]()));
  window.addEventListener('keydown',event=>{
    if(event.target.matches('input,textarea,select'))return;
    const action={ArrowLeft:'left',ArrowRight:'right',ArrowDown:'down',ArrowUp:'rotate',x:'rotate',X:'rotate',' ':'drop'}[event.key];
    if(action){event.preventDefault();actions[action]();}
    if(event.key.toLowerCase()==='p')pause();
  });
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&phase==='playing')pause();});
  updateHud();
})();
