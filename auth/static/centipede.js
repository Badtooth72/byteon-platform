(() => {
  'use strict';
  const W = 840, H = 640, CELL = 38, COLS = 20, TOP = 42, LEFT = 40;
  const $ = id => document.getElementById(id);
  const hud = {score:$('cg-score'), best:$('cg-best'), wave:$('cg-wave'), lives:$('cg-lives')};
  const overlay = $('centipede-overlay');
  const keys = {left:false,right:false,fire:false};
  let scene, running = false, paused = false, wave = 1, score = 0, lives = 3;
  let best = Number(localStorage.getItem('byteon-centipede-best') || 0) || 0;
  let playerX = W / 2, targetX = null, firing = false, cooldown = 0, stepClock = 0;
  let chains = [], mushrooms = [], bullets = [], spider = null, invincible = 0;
  let audio = null, soundOn = true;
  const random = (a,b) => a + Math.random() * (b-a);
  const clamp = (x,a,b) => Math.max(a,Math.min(b,x));
  const coord = (x,y) => ({x:LEFT + x*CELL + CELL/2,y:TOP + y*CELL + CELL/2});
  const fmt = n => String(n).padStart(6,'0');
  function updateHud() {
    hud.score.textContent = fmt(score); hud.best.textContent = fmt(best);
    hud.wave.textContent = String(wave).padStart(2,'0');
    hud.lives.textContent = '♥ '.repeat(lives).trim() || '—';
  }
  function tone(freq, length=.08, type='square', gain=.025, slide=1) {
    if (!soundOn) return;
    try {
      audio ||= new (window.AudioContext || window.webkitAudioContext)();
      if (audio.state === 'suspended') audio.resume();
      const osc=audio.createOscillator(), vol=audio.createGain(), at=audio.currentTime;
      osc.type=type; osc.frequency.setValueAtTime(freq,at);
      osc.frequency.exponentialRampToValueAtTime(Math.max(30,freq*slide),at+length);
      vol.gain.setValueAtTime(gain,at); vol.gain.exponentialRampToValueAtTime(.0001,at+length);
      osc.connect(vol); vol.connect(audio.destination); osc.start(at); osc.stop(at+length+.01);
    } catch (_) { /* Audio is optional. */ }
  }
  function burst(x,y,color,count=10) {
    if (!scene) return;
    for(let i=0;i<count;i++) {
      const dot=scene.add.circle(x,y,random(2,5),color).setDepth(8);
      scene.tweens.add({targets:dot,x:x+random(-55,55),y:y+random(-55,55),alpha:0,scale:0,
        duration:random(220,520),onComplete:()=>dot.destroy()});
    }
  }
  function addPoints(n,x,y) {
    score+=n;
    if(score>best) {best=score;localStorage.setItem('byteon-centipede-best',String(best));}
    updateHud();
    const label=scene.add.text(x,y,'+'+n,{fontFamily:'monospace',fontSize:'18px',fontStyle:'bold',color:'#ffe467'}).setOrigin(.5).setDepth(9);
    scene.tweens.add({targets:label,y:y-36,alpha:0,duration:650,onComplete:()=>label.destroy()});
  }
  function mushroomAt(x,y) {return mushrooms.find(m=>m.x===x&&m.y===y);}
  function seedMushrooms() {
    mushrooms=[];
    for(let i=0;i<75;i++) {
      const x=Math.floor(random(0,COLS)), y=Math.floor(random(2,13));
      if(!mushroomAt(x,y) && !(x>=8&&x<=11&&y>=10)) mushrooms.push({x,y,hp:2+Math.floor(random(0,2))});
    }
  }
  function spawnChain() {
    const length=Math.min(15,9+wave);
    chains=[{dir:1,vertical:1,parts:Array.from({length},(_,i)=>({x:Math.floor(COLS/2)-i,y:0}))}];
    stepClock=0;
  }
  function newWave() {
    if(!running) return;
    wave++; seedMushrooms(); spawnChain(); bullets=[];
    spider=null; updateHud(); tone(420,.25,'sawtooth',.04,1.8);
    const label=scene.add.text(W/2,H/2,`WAVE ${wave}`,{fontFamily:'monospace',fontSize:'46px',fontStyle:'bold',color:'#fff288',stroke:'#461c67',strokeThickness:7}).setOrigin(.5).setDepth(10);
    scene.tweens.add({targets:label,scale:1.5,alpha:0,duration:900,onComplete:()=>label.destroy()});
  }
  function showOverlay(kicker,title,copy,button) {
    $('cg-overlay-kicker').textContent=kicker; $('cg-overlay-title').textContent=title;
    $('cg-overlay-copy').textContent=copy; $('cg-start').textContent=button;
    overlay.hidden=false;
  }
  function startGame() {
    score=0;wave=1;lives=3;playerX=W/2;targetX=null;bullets=[];spider=null;
    cooldown=0;stepClock=0;invincible=0;seedMushrooms();spawnChain();
    running=true;paused=false;overlay.hidden=true;$('cg-pause').textContent='PAUSE';updateHud();
    tone(330,.12);setTimeout(()=>tone(660,.18),100);
  }
  function loseLife() {
    if(invincible>0||!running) return;
    lives--; invincible=1.7; burst(playerX,H-48,0xff4d91,22);tone(130,.45,'sawtooth',.07,.2);
    updateHud();
    if(lives<=0) {
      running=false;showOverlay('GAME OVER',fmt(score)+' POINTS',`You reached wave ${wave}. Best score: ${fmt(best)}. Give the garden another go.`, 'PLAY AGAIN');
    }
  }
  function moveChains() {
    for(const chain of chains) {
      if(!chain.parts.length) continue;
      const head=chain.parts[0], next=head.x+chain.dir;
      let x=next,y=head.y;
      if(next<0||next>=COLS||mushroomAt(next,head.y)) {
        x=head.x;y=head.y+chain.vertical;chain.dir*=-1;
        if(y>=14){chain.vertical=-1;y=13;} else if(y<=10&&chain.vertical<0){chain.vertical=1;y=11;}
      }
      chain.parts=[{x,y},...chain.parts.slice(0,-1)];
      const p=coord(x,y);
      if(y>=12&&Math.abs(p.x-playerX)<27&&Math.abs(p.y-(H-48))<27) loseLife();
    }
  }
  function hitSegment(ci,si) {
    const chain=chains[ci], part=chain.parts[si], p=coord(part.x,part.y);
    const before=chain.parts.slice(0,si), after=chain.parts.slice(si+1);
    const next=[];
    if(before.length) next.push({dir:chain.dir,vertical:chain.vertical,parts:before});
    if(after.length) next.push({dir:-chain.dir,vertical:chain.vertical,parts:after});
    chains.splice(ci,1,...next);
    if(!mushroomAt(part.x,part.y)) mushrooms.push({x:part.x,y:part.y,hp:2});
    addPoints(si===0?100:40,p.x,p.y);burst(p.x,p.y,si===0?0xffdf5e:0xa9ff5e,14);
    tone(si===0?570:390,.14,'square',.035,1.6);
    if(!chains.length) scene.time.delayedCall(650,newWave);
  }
  function updateBullets(dt) {
    for(let i=bullets.length-1;i>=0;i--) {
      const b=bullets[i];b.y-=580*dt;
      if(b.y<32){bullets.splice(i,1);continue;}
      if(spider&&Math.hypot(b.x-spider.x,b.y-spider.y)<23){
        spider=null;bullets.splice(i,1);addPoints(250,b.x,b.y);burst(b.x,b.y,0xff5cb4,22);tone(720,.22,'sawtooth',.05,.4);continue;
      }
      let hit=false;
      for(let ci=0;ci<chains.length&&!hit;ci++)for(let si=0;si<chains[ci].parts.length;si++) {
        const p=coord(chains[ci].parts[si].x,chains[ci].parts[si].y);
        if(Math.abs(b.x-p.x)<17&&Math.abs(b.y-p.y)<17){bullets.splice(i,1);hitSegment(ci,si);hit=true;break;}
      }
      if(hit) continue;
      for(let j=mushrooms.length-1;j>=0;j--) {
        const m=mushrooms[j],p=coord(m.x,m.y);
        if(Math.abs(b.x-p.x)<17&&Math.abs(b.y-p.y)<16){
          bullets.splice(i,1);m.hp--;burst(p.x,p.y,0x9e65f9,4);tone(160,.05,'triangle',.017);
          if(m.hp<=0){mushrooms.splice(j,1);addPoints(5,p.x,p.y);}break;
        }
      }
    }
  }
  function background(g) {
    g.fillGradientStyle(0x07132e,0x07132e,0x122849,0x122849).fillRect(0,0,W,H);
    g.lineStyle(1,0x5ad5ff,.08);
    for(let x=LEFT;x<W-LEFT;x+=CELL)g.lineBetween(x,TOP,x,H);
    for(let y=TOP;y<H;y+=CELL)g.lineBetween(LEFT,y,W-LEFT,y);
    g.fillStyle(0x123851,.55).fillRect(0,H-110,W,110);
    g.lineStyle(2,0x6cf9dc,.35).lineBetween(0,H-110,W,H-110);
    for(let i=0;i<50;i++) {
      const x=(i*173+31)%W,y=(i*127+17)%(H-115);
      g.fillStyle(i%3?0x9af6ff:0xffcf76,i%3?.35:.6).fillCircle(x,y,i%7?1:2);
    }
    g.lineStyle(5,0x2cebe4,.45).strokeRect(LEFT-8,TOP-8,W-2*LEFT+16,H-TOP+8);
  }
  function drawMushroom(g,m,t) {
    const p=coord(m.x,m.y), wobble=Math.sin(t/380+m.x)*.7;
    g.fillStyle(0x18394a,.8).fillEllipse(p.x,p.y+14,29,8);
    g.fillStyle(0xe1d5ff).fillRoundedRect(p.x-5,p.y-2,10,16,3);
    g.fillGradientStyle(m.hp===3?0xfa5aaf:0x9e68ea,0xf795d0,0x793ed5,0x57289c)
      .fillEllipse(p.x,p.y-5+wobble,28,20);
    g.fillStyle(0xffe9fc,.9).fillCircle(p.x-7,p.y-8+wobble,3).fillCircle(p.x+6,p.y-5+wobble,2);
  }
  function drawSegment(g,p,head,t,index) {
    const q=coord(p.x,p.y), pulse=Math.sin(t/180+index)*1.2;
    g.fillStyle(head?0xffdf57:0x71ee87,.17).fillCircle(q.x,q.y,21+pulse);
    g.fillStyle(head?0x7d441e:0x187d68).fillCircle(q.x,q.y,16+pulse);
    g.fillStyle(head?0xffc44d:0x7bf4a2).fillCircle(q.x,q.y,13+pulse);
    g.fillStyle(head?0xfff2b1:0xc3ffcf,.8).fillEllipse(q.x-4,q.y-5,8,5);
    if(head) {
      g.fillStyle(0x111a33).fillCircle(q.x-5,q.y-1,2.5).fillCircle(q.x+5,q.y-1,2.5);
      g.lineStyle(2,0xff7d58).lineBetween(q.x-9,q.y-13,q.x-14,q.y-22).lineBetween(q.x+9,q.y-13,q.x+14,q.y-22);
    } else {g.fillStyle(0x1f945f,.8).fillCircle(q.x+5,q.y+5,4);}
  }
  function drawPlayer(g,t) {
    if(invincible>0&&Math.floor(t/100)%2) return;
    const y=H-48;
    g.fillStyle(0x2ceded,.17).fillCircle(playerX,y,30);
    g.fillStyle(0x162f62).fillTriangle(playerX,y-25,playerX-22,y+18,playerX+22,y+18);
    g.fillStyle(0x57eaff).fillTriangle(playerX,y-23,playerX-15,y+13,playerX+15,y+13);
    g.fillStyle(0xffe467).fillRoundedRect(playerX-5,y-16,10,21,3);
    g.fillStyle(0xff5cba).fillTriangle(playerX-9,y+15,playerX,y+28+Math.sin(t/70)*3,playerX+9,y+15);
  }
  function render(t) {
    const g=scene.world;g.clear();background(g);
    for(const m of mushrooms)drawMushroom(g,m,t);
    for(const chain of chains)chain.parts.forEach((p,i)=>drawSegment(g,p,i===0,t,i));
    for(const b of bullets){g.fillStyle(0x80ffff,.2).fillRoundedRect(b.x-6,b.y-17,12,25,5);g.fillStyle(0xffffff).fillRoundedRect(b.x-2,b.y-13,4,16,2);}
    if(spider){
      g.fillStyle(0xff3c98,.2).fillCircle(spider.x,spider.y,29);
      g.lineStyle(4,0xc643a8);for(let d of [-1,1])for(let i=0;i<3;i++)g.lineBetween(spider.x+d*10,spider.y-4+i*6,spider.x+d*23,spider.y-9+i*9);
      g.fillStyle(0x872462).fillCircle(spider.x,spider.y,16);g.fillStyle(0xff57b4).fillCircle(spider.x,spider.y-3,13);
      g.fillStyle(0xffffff).fillCircle(spider.x-5,spider.y-5,3).fillCircle(spider.x+5,spider.y-5,3);
    }
    drawPlayer(g,t);
  }
  function update(time,delta) {
    if(!scene)return;
    if(!running||paused){render(time);return;}
    const dt=Math.min(delta/1000,.06);
    invincible=Math.max(0,invincible-dt);
    if(targetX!==null)playerX+=clamp(targetX-playerX,-600*dt,600*dt);
    else playerX+=((keys.right?1:0)-(keys.left?1:0))*490*dt;
    playerX=clamp(playerX,LEFT+14,W-LEFT-14);
    cooldown-=dt;
    if((keys.fire||firing)&&cooldown<=0){bullets.push({x:playerX,y:H-73});cooldown=.14;tone(880,.035,'square',.009,.7);}
    stepClock+=dt;
    const step=Math.max(.055,.16-wave*.008);
    while(stepClock>=step){stepClock-=step;moveChains();}
    if(!spider&&Math.random()<dt*.24){const fromLeft=Math.random()<.5;spider={x:fromLeft?-30:W+30,y:random(H-180,H-100),vx:fromLeft?145:-145,age:0};}
    if(spider){spider.age+=dt;spider.x+=spider.vx*dt;spider.y+=Math.sin(spider.age*8)*1.9;
      if(spider.x<-45||spider.x>W+45)spider=null;
      else if(Math.hypot(spider.x-playerX,spider.y-(H-48))<27)loseLife();}
    updateBullets(dt);render(time);
  }
  const game=new Phaser.Game({type:Phaser.CANVAS,parent:'centipede-stage',width:W,height:H,
    backgroundColor:'#07132e',scale:{mode:Phaser.Scale.FIT,autoCenter:Phaser.Scale.CENTER_BOTH,width:W,height:H},
    scene:{create(){scene=this;this.world=this.add.graphics();},update}});
  $('cg-start').addEventListener('click',()=>{if(paused){paused=false;overlay.hidden=true;$('cg-pause').textContent='PAUSE';}else startGame();});
  $('cg-pause').addEventListener('click',()=>{if(!running)return;paused=!paused;$('cg-pause').textContent=paused?'RESUME':'PAUSE';
    if(paused)showOverlay('PAUSED','TAKE A BREATH','Your garden is waiting.','RESUME');else overlay.hidden=true;});
  $('cg-sound').addEventListener('click',()=>{soundOn=!soundOn;$('cg-sound').textContent=soundOn?'SOUND ON':'SOUND OFF';$('cg-sound').setAttribute('aria-pressed',String(soundOn));});
  function bindHold(id,key){const el=$(id);el.addEventListener('pointerdown',e=>{e.preventDefault();el.setPointerCapture(e.pointerId);keys[key]=true;});
    for(const event of ['pointerup','pointercancel','lostpointercapture'])el.addEventListener(event,()=>keys[key]=false);}
  bindHold('cg-left','left');bindHold('cg-right','right');bindHold('cg-fire','fire');
  const stage=$('centipede-stage');
  stage.addEventListener('pointermove',e=>{if(e.pointerType==='mouse'||e.buttons){const rect=stage.getBoundingClientRect();targetX=(e.clientX-rect.left)/rect.width*W;}});
  stage.addEventListener('pointerdown',e=>{e.preventDefault();const rect=stage.getBoundingClientRect();targetX=(e.clientX-rect.left)/rect.width*W;firing=true;});
  window.addEventListener('pointerup',()=>firing=false);
  window.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight',' ','a','d','A','D'].includes(e.key))e.preventDefault();
    if(e.key==='ArrowLeft'||e.key.toLowerCase()==='a'){keys.left=true;targetX=null;}
    if(e.key==='ArrowRight'||e.key.toLowerCase()==='d'){keys.right=true;targetX=null;}
    if(e.key===' ')keys.fire=true;
    if(e.key.toLowerCase()==='p'&&running)$('cg-pause').click();});
  window.addEventListener('keyup',e=>{if(e.key==='ArrowLeft'||e.key.toLowerCase()==='a')keys.left=false;
    if(e.key==='ArrowRight'||e.key.toLowerCase()==='d')keys.right=false;if(e.key===' ')keys.fire=false;});
  window.addEventListener('blur',()=>{keys.left=keys.right=keys.fire=firing=false;});
  updateHud();
})();
