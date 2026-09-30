(() => {
  'use strict';
  const $=id=>document.getElementById(id),W=900,H=620,WORLD=2900,FLOOR=2770,STEP=190,LANES=[115,338,562,785];
  const held={left:false,right:false};
  let scene,hero,platforms,floor,labels=[],runId=null,challenge=null,phase='intro',round=1,score=0,best=Number($('tower-best').textContent.split('/')[0])||0;
  let jumps=0,checkpoint={x:W/2,y:FLOOR-55},soundOn=true,audio;
  function tone(frequency,length=.09,volume=.03){
    if(!soundOn)return;
    try{audio ||=new(window.AudioContext||window.webkitAudioContext)();if(audio.state==='suspended')audio.resume();
      const oscillator=audio.createOscillator(),gain=audio.createGain(),now=audio.currentTime;
      oscillator.type='square';oscillator.frequency.setValueAtTime(frequency,now);oscillator.frequency.exponentialRampToValueAtTime(Math.max(40,frequency*.65),now+length);
      gain.gain.setValueAtTime(volume,now);gain.gain.exponentialRampToValueAtTime(.0001,now+length);
      oscillator.connect(gain);gain.connect(audio.destination);oscillator.start(now);oscillator.stop(now+length+.01);
    }catch(_){/* Play remains available without sound. */}
  }
  function hud(){
    $('tower-floor').textContent=`${round}/10`;$('tower-score').textContent=`${score}/100`;$('tower-best').textContent=`${best}/100`;
  }
  function message(text,good){const el=$('tower-feedback');el.textContent=text;el.className=good===true?'good':good===false?'bad':'';}
  function show(kicker,title,copy,action){$('tower-kicker').textContent=kicker;$('tower-title').textContent=title;$('tower-copy').textContent=copy;$('tower-action').textContent=action;$('tower-overlay').hidden=false;}
  function sparks(x,y,colour){
    for(let i=0;i<18;i++){
      const dot=scene.add.circle(x,y,Phaser.Math.Between(2,5),colour).setDepth(8);
      scene.tweens.add({targets:dot,x:x+Phaser.Math.Between(-80,80),y:y+Phaser.Math.Between(-70,20),alpha:0,scale:0,duration:Phaser.Math.Between(250,550),onComplete:()=>dot.destroy()});
    }
  }
  function makeTier(tier,choices){
    const y=FLOOR-STEP*tier;
    choices.forEach((choice,index)=>{
      const platform=platforms.create(LANES[index],y,'tower-platform').setTint([0x50dfff,0xb5ff66,0xffdc6d,0xf68bff][index]);
      platform.refreshBody();platform.body.checkCollision.down=false;platform.body.checkCollision.left=false;platform.body.checkCollision.right=false;
      platform.setData('tier',tier);platform.setData('choice',choice);
      const label=scene.add.text(LANES[index],y-37,`${index+1} · ${choice}`,{
        fontFamily:'system-ui',fontSize:'15px',fontStyle:'bold',color:'#ffffff',align:'center',stroke:'#08172f',strokeThickness:4,
        wordWrap:{width:192,useAdvancedWrap:true}
      }).setOrigin(.5,1).setDepth(4);
      labels.push(label);
    });
  }
  async function post(action,body={}){
    const response=await fetch(`/api/games/cpu-tower/${action}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data=await response.json().catch(()=>({error:'The game server did not respond as expected.'}));
    if(!response.ok)throw new Error(data.error||'Could not save this floor.');
    return data;
  }
  async function start(){
    if(!scene||phase==='loading')return;
    phase='loading';$('tower-action').disabled=true;$('tower-copy').textContent='Starting your climb…';
    try{
      const data=await post('start');runId=data.run_id;challenge=data.challenge;round=1;score=0;jumps=0;
      platforms.clear(true,true);labels.forEach(label=>label.destroy());labels=[];
      checkpoint={x:W/2,y:FLOOR-55};hero.setPosition(checkpoint.x,checkpoint.y).setVelocity(0,0).setVisible(true).setAlpha(1);
      scene.cameras.main.setScroll(0,WORLD-H);makeTier(round,challenge.choices);
      phase='climb';scene.physics.resume();$('tower-overlay').hidden=true;
      $('tower-category').textContent=challenge.category||'CPU';$('tower-prompt').textContent=challenge.prompt;
      message('Move beneath an answer and land on its platform. Use your second jump to reach far platforms.');hud();tone(460,.2,.04);
    }catch(error){phase='intro';show('CONNECTION ERROR','CLIMB PAUSED',error.message,'TRY AGAIN');}
    finally{$('tower-action').disabled=false;}
  }
  async function land(platform){
    if(phase!=='climb'||platform.getData('tier')!==round)return;
    phase='marking';scene.physics.pause();
    const choice=platform.getData('choice');message(`Landed on ${choice}. Checking…`);
    try{
      const result=await post('answer',{run_id:runId,answer:choice});score=result.score;best=Math.max(best,result.best||0);hud();
      sparks(hero.x,hero.y,result.correct?0xb7ff5c:0xff599f);
      message(`${result.correct?'Correct landing!':'Wrong platform.'} ${result.explanation}`,result.correct);
      tone(result.correct?680:180,.25,.05);
      checkpoint={x:platform.x,y:platform.y-48};
      if(result.finished){best=result.best;hud();setTimeout(()=>finish(),1200);return;}
      challenge=result.next;round=result.round+1;makeTier(round,challenge.choices);
      setTimeout(()=>{
        hero.setPosition(checkpoint.x,checkpoint.y).setVelocity(0,0);jumps=0;
        $('tower-category').textContent=challenge.category||'CPU';$('tower-prompt').textContent=challenge.prompt;
        message('Choose an answer platform above, then jump onto it.');
        phase='climb';scene.physics.resume();hud();
      },result.correct?900:1500);
    }catch(error){message(error.message,false);phase='climb';scene.physics.resume();}
  }
  function finish(){
    phase='over';scene.physics.pause();$('tower-prompt').textContent='Tower complete';
    show('RUN COMPLETE','YOU REACHED THE TOP',`${score}/100 recorded marks. Best run: ${best}/100.`, 'CLIMB AGAIN');tone(760,.35,.05);
  }
  function jump(){
    if(phase!=='climb'||jumps>=2)return;
    jumps++;hero.setVelocityY(jumps===1?-735:-690);tone(jumps===1?460:690,.08,.035);
  }
  new Phaser.Game({type:Phaser.AUTO,parent:'tower-stage',width:W,height:H,backgroundColor:'#081632',render:{pixelArt:true},
    scale:{mode:Phaser.Scale.FIT,autoCenter:Phaser.Scale.CENTER_BOTH,width:W,height:H},
    physics:{default:'arcade',arcade:{gravity:{y:1120},debug:false}},scene:{
      preload(){this.load.spritesheet('tower-hero','/static/arcade-art/platform-characters.png',{frameWidth:18,frameHeight:18});},
      create(){
        scene=this;this.physics.world.setBounds(0,0,W,WORLD);this.cameras.main.setBounds(0,0,W,WORLD);
        const back=this.add.graphics().setDepth(-3);
        back.fillGradientStyle(0x07152e,0x07152e,0x17437a,0x17437a).fillRect(0,0,W,WORLD);
        for(let y=0;y<WORLD;y+=42){back.lineStyle(1,0x75d8f7,.12).lineBetween(0,y,W,y);}
        for(let x=0;x<W;x+=50){back.lineStyle(1,0x75d8f7,.09).lineBetween(x,0,x,WORLD);}
        for(let tier=0;tier<=10;tier++){
          const y=FLOOR-STEP*tier;
          back.fillStyle(tier%2?0x283773:0x1b5483,.3).fillRect(0,y+62,W,38);
          this.add.text(16,y-100,`FLOOR ${tier}`,{fontFamily:'monospace',fontSize:'16px',fontStyle:'bold',color:'#7fe6f5'}).setDepth(-1);
        }
        const texture=this.make.graphics({x:0,y:0});texture.fillStyle(0x78e4ff).fillRoundedRect(0,0,172,22,4);
        texture.fillStyle(0xffffff,.5).fillRect(8,3,156,3);texture.fillStyle(0x132a51).fillRect(0,17,172,5);
        texture.generateTexture('tower-platform',172,22);texture.destroy();
        platforms=this.physics.add.staticGroup();floor=this.physics.add.staticImage(W/2,FLOOR+8,'tower-platform').setDisplaySize(W,25).refreshBody().setTint(0x4ce8e5);
        hero=this.physics.add.sprite(W/2,FLOOR-55,'tower-hero',0).setScale(3).setDepth(6).setCollideWorldBounds(true);
        hero.body.setSize(14,16).setOffset(2,2);hero.setMaxVelocity(420,900);
        this.physics.add.collider(hero,floor,()=>{if(hero.body.touching.down)jumps=0;});
        this.physics.add.collider(hero,platforms,(_,platform)=>{
          if(hero.body.touching.down){jumps=0;land(platform);}
        });
        this.cameras.main.startFollow(hero,true,.08,.12,0,110);
        this.physics.pause();
      },
      update(){
        if(phase!=='climb')return;
        hero.setVelocityX(((held.right?1:0)-(held.left?1:0))*410);
        if(hero.y>checkpoint.y+250){hero.setPosition(checkpoint.x,checkpoint.y).setVelocity(0,0);jumps=0;message('Back at the last floor. Try your jump again.');tone(160,.18);}
      }
    }});
  $('tower-action').addEventListener('click',start);
  $('tower-sound').addEventListener('click',()=>{soundOn=!soundOn;$('tower-sound').textContent=soundOn?'SOUND ON':'SOUND OFF';$('tower-sound').setAttribute('aria-pressed',String(soundOn));});
  function hold(id,key){const button=$(id);button.addEventListener('pointerdown',event=>{event.preventDefault();button.setPointerCapture(event.pointerId);held[key]=true;});
    for(const name of ['pointerup','pointercancel','lostpointercapture'])button.addEventListener(name,()=>held[key]=false);}
  hold('tower-left','left');hold('tower-right','right');$('tower-jump').addEventListener('pointerdown',event=>{event.preventDefault();jump();});
  window.addEventListener('keydown',event=>{
    if(event.target.matches('input,textarea,select'))return;
    if(['ArrowLeft','ArrowRight','ArrowUp',' ','a','d','w','A','D','W'].includes(event.key))event.preventDefault();
    if(event.key==='ArrowLeft'||event.key.toLowerCase()==='a')held.left=true;
    if(event.key==='ArrowRight'||event.key.toLowerCase()==='d')held.right=true;
    if(!event.repeat&&['ArrowUp',' ','w','W'].includes(event.key))jump();
  });
  window.addEventListener('keyup',event=>{if(event.key==='ArrowLeft'||event.key.toLowerCase()==='a')held.left=false;if(event.key==='ArrowRight'||event.key.toLowerCase()==='d')held.right=false;});
  window.addEventListener('blur',()=>{held.left=held.right=false;});
  hud();
})();
