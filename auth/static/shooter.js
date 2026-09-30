(() => {
  'use strict';
  const W=840,H=620,$=id=>document.getElementById(id),slug='ctrl-alt-defeat';
  const ui={overlay:$('shooter-overlay'),kicker:$('sh-overlay-kicker'),title:$('sh-overlay-title'),copy:$('sh-overlay-copy'),
    answers:$('sh-answers'),feedback:$('sh-feedback'),action:$('sh-action'),message:$('sh-message'),timer:$('sh-timer')};
  const held={left:false,right:false,fire:false};
  let scene,player,stars=[],enemies,playerShots,enemyShots,phase='intro',paused=false,runId=null,challenge=null;
  let wave=1,marks=0,best=Number($('sh-best').textContent.split('/')[0])||0,arcadeScore=0,lives=3,shield=0,weapon=1;
  let elapsed=0,spawnClock=0,shotClock=0,enemyShotClock=0,invincible=0,waveKills=0,targetX=null,pointerFire=false;
  let soundOn=true,audio;
  const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
  function tone(frequency,length=.08,type='square',volume=.025,slide=1){
    if(!soundOn)return;
    try{audio ||=new(window.AudioContext||window.webkitAudioContext)();if(audio.state==='suspended')audio.resume();
      const osc=audio.createOscillator(),gain=audio.createGain(),now=audio.currentTime;
      osc.type=type;osc.frequency.setValueAtTime(frequency,now);osc.frequency.exponentialRampToValueAtTime(Math.max(35,frequency*slide),now+length);
      gain.gain.setValueAtTime(volume,now);gain.gain.exponentialRampToValueAtTime(.0001,now+length);
      osc.connect(gain);gain.connect(audio.destination);osc.start(now);osc.stop(now+length+.01);
    }catch(_){/* Game remains playable without audio. */}
  }
  function hud(){
    $('sh-kills').textContent=String(arcadeScore).padStart(6,'0');$('sh-marks').textContent=`${marks}/100`;
    $('sh-wave').textContent=`${wave}/10`;$('sh-lives').textContent='♥ '.repeat(lives).trim()||'—';
    $('sh-shield').textContent='● '.repeat(shield)+'○ '.repeat(Math.max(0,2-shield));
    $('sh-best').textContent=`${best}/100`;
  }
  async function post(action,body={}){
    const response=await fetch(`/api/games/${slug}/${action}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data=await response.json().catch(()=>({error:'The game server did not respond as expected.'}));
    if(!response.ok)throw new Error(data.error||'Could not save your game.');
    return data;
  }
  function show(kicker,title,copy,button){
    ui.kicker.textContent=kicker;ui.title.textContent=title;ui.copy.textContent=copy;
    ui.action.textContent=button||'';ui.action.hidden=!button;ui.feedback.textContent='';
    ui.overlay.hidden=false;
  }
  function clearField(){
    enemies?.clear(true,true);playerShots?.clear(true,true);enemyShots?.clear(true,true);
  }
  function spark(x,y,color,count=12){
    for(let i=0;i<count;i++){
      const dot=scene.add.circle(x,y,Phaser.Math.Between(2,5),color).setDepth(8);
      scene.tweens.add({targets:dot,x:x+Phaser.Math.Between(-55,55),y:y+Phaser.Math.Between(-55,55),alpha:0,scale:0,
        duration:Phaser.Math.Between(220,520),onComplete:()=>dot.destroy()});
    }
  }
  function floatingScore(x,y,value){
    const label=scene.add.text(x,y,`+${value}`,{fontFamily:'monospace',fontSize:'18px',fontStyle:'bold',color:'#ffef8b'}).setOrigin(.5).setDepth(9);
    scene.tweens.add({targets:label,y:y-35,alpha:0,duration:550,onComplete:()=>label.destroy()});
  }
  function rewardFor(n){return n%3===1?'SHIELD':n%3===2?'TWIN LASERS':'EXTRA LIFE';}
  function grantReward(n){
    const reward=rewardFor(n);
    if(reward==='SHIELD')shield=Math.min(2,shield+1);
    else if(reward==='TWIN LASERS')weapon=Math.min(3,weapon+1);
    else lives=Math.min(5,lives+1);
    hud();tone(420,.24,'triangle',.05,2);
    return reward;
  }
  function startWave(){
    clearField();elapsed=0;spawnClock=.25;enemyShotClock=.9;shotClock=0;waveKills=0;targetX=null;
    phase='wave';paused=false;ui.overlay.hidden=true;ui.message.textContent=`WAVE ${wave} · DEFEND THE CORE`;
    ui.timer.textContent='12s';$('sh-pause').textContent='PAUSE';scene.physics.resume();hud();
    tone(300,.2,'sawtooth',.025,1.6);
  }
  async function startGame(){
    if(!scene)return;
    phase='loading';ui.action.disabled=true;ui.message.textContent='CONNECTING TO MISSION CONTROL';
    try{
      const data=await post('start');runId=data.run_id;challenge=data.challenge;wave=1;marks=0;arcadeScore=0;lives=3;shield=0;weapon=1;
      player.x=W/2;player.setVisible(true);invincible=0;hud();startWave();
    }catch(error){phase='intro';show('CONNECTION ERROR','MISSION PAUSED',error.message,'TRY AGAIN');}
    finally{ui.action.disabled=false;}
  }
  function toQuiz(){
    if(phase!=='wave')return;
    phase='quiz';scene.physics.pause();clearField();ui.timer.textContent='';
    ui.message.textContent=`WAVE ${wave} CLEARED · REPAIR YOUR SHIP`;
    show(challenge.category||'RETRIEVAL ROUND',challenge.prompt,`Correct answer earns ${rewardFor(wave)}. This answer counts towards your recorded mark.`,null);
    ui.answers.replaceChildren();ui.answers.hidden=false;
    challenge.choices.forEach((choice,index)=>{
      const button=document.createElement('button');button.type='button';button.textContent=`${index+1}. ${choice}`;
      button.addEventListener('click',()=>answer(choice));ui.answers.append(button);
    });
    tone(540,.14,'triangle',.025,1.4);
  }
  async function answer(choice){
    if(phase!=='quiz')return;
    phase='marking';[...ui.answers.children].forEach(button=>button.disabled=true);
    ui.feedback.textContent='Checking answer…';
    try{
      const result=await post('answer',{run_id:runId,answer:choice});marks=result.score;
      if(result.correct){const reward=grantReward(wave);ui.feedback.textContent=`CORRECT · ${reward} AWARDED. ${result.explanation}`;}
      else{tone(180,.2,'sawtooth',.035,.55);ui.feedback.textContent=`NO UPGRADE. ${result.explanation}`;}
      best=Math.max(best,result.best||0);hud();
      if(result.finished){best=result.best;setTimeout(()=>finish(true),1600);return;}
      challenge=result.next;wave=result.round+1;
      setTimeout(()=>{ui.answers.hidden=true;startWave();},1600);
    }catch(error){phase='quiz';[...ui.answers.children].forEach(button=>button.disabled=false);ui.feedback.textContent=error.message;}
  }
  function finish(completed){
    phase='over';paused=false;scene.physics.pause();clearField();hud();
    ui.answers.hidden=true;ui.message.textContent=completed?'MISSION COMPLETE':'SYSTEM BREACH';ui.timer.textContent='';
    show(completed?'MISSION COMPLETE':'GAME OVER',completed?'CORE DEFENDED':'SYSTEM BREACH',
      `${arcadeScore} arcade points · ${marks}/100 recorded marks · reached wave ${wave}. Best mark: ${best}/100.`, 'PLAY AGAIN');
    tone(completed?660:125,.5,'sawtooth',.05,completed?1.5:.4);
  }
  async function loseLife(){
    if(phase!=='wave'||invincible>0)return;
    if(shield>0){shield--;invincible=.8;ui.message.textContent='SHIELD ABSORBED THE HIT';tone(330,.16,'triangle',.045,.7);}
    else{lives--;invincible=1.4;ui.message.textContent='HULL BREACH · KEEP FIGHTING';tone(150,.3,'sawtooth',.05,.45);}
    spark(player.x,player.y,0xff4ca4,20);hud();
    if(lives<=0){
      phase='ending';scene.physics.pause();ui.message.textContent='SAVING YOUR MARK…';
      try{const result=await post('abort',{run_id:runId});marks=result.score;best=result.best;}
      catch(error){ui.message.textContent=`SAVE FAILED: ${error.message}`;}
      finish(false);
    }
  }
  function spawnEnemy(){
    const x=Phaser.Math.Between(50,W-50),frame=Phaser.Math.Between(1,3),enemy=enemies.create(x,-35,'ships',frame);
    enemy.setScale(1.8).setDepth(4).setVelocity(Phaser.Math.Between(-28,28),90+wave*13);
    enemy.body.setSize(23,23);enemy.setData('value',wave%3===0?45:25);
    enemy.setTint([0xff87a7,0xff6bbb,0xe791ff][frame-1]);
  }
  function playerFire(){
    if(phase!=='wave')return;
    const offsets=weapon===1?[0]:weapon===2?[-14,14]:[-22,0,22];
    for(const offset of offsets){
      const bullet=playerShots.create(player.x+offset,player.y-26,'laser');bullet.setVelocityY(-610).setDepth(5);
    }
    tone(760,.035,'square',.01,.7);
  }
  function enemyFire(){
    const active=enemies.getChildren().filter(e=>e.active&&e.y>25&&e.y<H-170);
    if(!active.length)return;
    const source=Phaser.Utils.Array.GetRandom(active);
    const shot=enemyShots.create(source.x,source.y+16,'malware-shot');shot.setVelocity(0,255+wave*13).setDepth(4);
  }
  const phaser=new Phaser.Game({type:Phaser.AUTO,parent:'shooter-stage',width:W,height:H,backgroundColor:'#07162f',
    render:{pixelArt:true},scale:{mode:Phaser.Scale.FIT,autoCenter:Phaser.Scale.CENTER_BOTH,width:W,height:H},
    physics:{default:'arcade',arcade:{debug:false}},scene:{
      preload(){this.load.spritesheet('ships','/static/arcade-art/shmup-ships.png',{frameWidth:32,frameHeight:32});},
      create(){
        scene=this;
        const bg=this.add.graphics();bg.fillGradientStyle(0x071431,0x071431,0x15275b,0x15275b).fillRect(0,0,W,H);
        bg.lineStyle(1,0x54cefa,.12);for(let x=0;x<W;x+=40)bg.lineBetween(x,0,x,H);for(let y=0;y<H;y+=40)bg.lineBetween(0,y,W,y);
        bg.fillStyle(0x162e60,.85).fillRect(0,H-38,W,38);bg.lineStyle(3,0x61f7f0,.8).lineBetween(0,H-38,W,H-38);
        stars=Array.from({length:70},()=>this.add.circle(Phaser.Math.Between(0,W),Phaser.Math.Between(0,H),Phaser.Math.Between(1,2),0xb2f8ff,Math.random()*.65+.15));
        const graphics=this.make.graphics({x:0,y:0});graphics.fillStyle(0xaaffff).fillRoundedRect(3,0,6,24,3);graphics.generateTexture('laser',12,25);
        graphics.clear().fillStyle(0xff5a9c).fillCircle(7,7,6);graphics.generateTexture('malware-shot',14,14);graphics.destroy();
        player=this.physics.add.sprite(W/2,H-76,'ships',0).setScale(2.2).setDepth(6).setCollideWorldBounds(true);
        player.body.setSize(20,24);
        enemies=this.physics.add.group();playerShots=this.physics.add.group();enemyShots=this.physics.add.group();
        this.physics.add.overlap(playerShots,enemies,(shot,enemy)=>{
          if(phase!=='wave')return;
          shot.destroy();const value=enemy.getData('value')||25,x=enemy.x,y=enemy.y;enemy.destroy();
          waveKills++;arcadeScore+=value;spark(x,y,0xff5aa8,11);floatingScore(x,y,value);hud();tone(330,.085,'sawtooth',.025,1.4);
          if(waveKills>=8+wave)toQuiz();
        });
        this.physics.add.overlap(enemyShots,player,(shot)=>{if(phase!=='wave')return;shot.destroy();loseLife();});
        this.physics.add.overlap(enemies,player,(ship)=>{if(phase!=='wave')return;ship.destroy();loseLife();});
        this.physics.pause();
      },
      update(time,delta){
        stars.forEach((star,index)=>{star.y+=(index%3+1)*delta*.015;if(star.y>H)star.y=0;});
        if(phase!=='wave'||paused)return;
        const dt=Math.min(delta/1000,.06);elapsed+=dt;spawnClock-=dt;shotClock-=dt;enemyShotClock-=dt;invincible=Math.max(0,invincible-dt);
        const direction=(held.right?1:0)-(held.left?1:0);
        if(targetX!==null)player.x+=clamp(targetX-player.x,-560*dt,560*dt);else player.x+=direction*470*dt;
        player.x=clamp(player.x,28,W-28);player.setAlpha(invincible>0&&Math.floor(time/90)%2?.35:1);
        if((held.fire||pointerFire)&&shotClock<=0){playerFire();shotClock=weapon>1?.11:.16;}
        if(spawnClock<=0){spawnEnemy();spawnClock=Math.max(.35,.76-wave*.035);}
        if(enemyShotClock<=0){enemyFire();enemyShotClock=Math.max(.7,1.8-wave*.08);}
        for(const enemy of enemies.getChildren())if(enemy.active&&enemy.y>H+30){enemy.destroy();}
        for(const bullet of playerShots.getChildren())if(bullet.active&&bullet.y<0)bullet.destroy();
        for(const bullet of enemyShots.getChildren())if(bullet.active&&bullet.y>H+20)bullet.destroy();
        ui.timer.textContent=`${Math.max(0,Math.ceil(12-elapsed))}s TO REPAIR BAY`;
        if(elapsed>=12)toQuiz();
      }
    }});
  ui.action.addEventListener('click',()=>{if(paused){paused=false;phase='wave';ui.overlay.hidden=true;scene.physics.resume();$('sh-pause').textContent='PAUSE';}else startGame();});
  $('sh-pause').addEventListener('click',()=>{
    if(phase!=='wave'&&phase!=='paused')return;
    if(!paused){paused=true;phase='paused';scene.physics.pause();show('PAUSED','TAKE A BREATH','Your ship is safe until you resume.','RESUME');$('sh-pause').textContent='RESUME';}
    else{paused=false;phase='wave';scene.physics.resume();ui.overlay.hidden=true;$('sh-pause').textContent='PAUSE';}
  });
  $('sh-sound').addEventListener('click',()=>{soundOn=!soundOn;$('sh-sound').textContent=soundOn?'SOUND ON':'SOUND OFF';$('sh-sound').setAttribute('aria-pressed',String(soundOn));});
  function hold(id,key){const element=$(id);element.addEventListener('pointerdown',e=>{e.preventDefault();element.setPointerCapture(e.pointerId);held[key]=true;targetX=null;});
    for(const event of ['pointerup','pointercancel','lostpointercapture'])element.addEventListener(event,()=>held[key]=false);}
  hold('sh-left','left');hold('sh-right','right');hold('sh-fire','fire');
  const stage=$('shooter-stage');
  stage.addEventListener('pointermove',e=>{if(e.pointerType==='mouse'||e.buttons){const box=stage.getBoundingClientRect();targetX=(e.clientX-box.left)/box.width*W;}});
  stage.addEventListener('pointerdown',e=>{e.preventDefault();const box=stage.getBoundingClientRect();targetX=(e.clientX-box.left)/box.width*W;pointerFire=true;});
  window.addEventListener('pointerup',()=>pointerFire=false);
  window.addEventListener('keydown',e=>{if(e.target.matches('input,textarea,select'))return;
    if(['ArrowLeft','ArrowRight',' ','a','d','A','D'].includes(e.key))e.preventDefault();
    if(e.key==='ArrowLeft'||e.key.toLowerCase()==='a'){held.left=true;targetX=null;}
    if(e.key==='ArrowRight'||e.key.toLowerCase()==='d'){held.right=true;targetX=null;}
    if(e.key===' ')held.fire=true;
    if(phase==='quiz'&&/^[1-4]$/.test(e.key))ui.answers.children[Number(e.key)-1]?.click();
    if(e.key.toLowerCase()==='p')$('sh-pause').click();});
  window.addEventListener('keyup',e=>{if(e.key==='ArrowLeft'||e.key.toLowerCase()==='a')held.left=false;
    if(e.key==='ArrowRight'||e.key.toLowerCase()==='d')held.right=false;if(e.key===' ')held.fire=false;});
  window.addEventListener('blur',()=>{held.left=held.right=held.fire=pointerFire=false;});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&phase==='wave'&&!paused)$('sh-pause').click();});
  hud();
})();
