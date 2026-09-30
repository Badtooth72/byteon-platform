(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const stations = [
    {name:'PC',x:120,y:125,detail:'NEXT ADDRESS'}, {name:'MAR',x:345,y:125,detail:'MEMORY ADDRESS'},
    {name:'Cache',x:580,y:100,detail:'FAST STORE'}, {name:'RAM',x:835,y:145,detail:'MAIN MEMORY'},
    {name:'MDR',x:595,y:265,detail:'TRANSFER DATA'}, {name:'CU',x:330,y:300,detail:'DECODE + CONTROL'},
    {name:'ALU',x:570,y:430,detail:'CALCULATE'}, {name:'Accumulator',x:840,y:425,detail:'RESULT'}
  ];
  const byName = Object.fromEntries(stations.map(station => [station.name, station]));
  let scene, packet, runId, challenge, route=[], score=0, best=Number($('dispatch-best').textContent.split('/')[0])||0;
  let round=1, seconds=25, timer, phase='intro', soundOn=true, audio;
  function tone(frequency,length=.09){
    if(!soundOn)return;
    try{audio ||= new(window.AudioContext||window.webkitAudioContext)();if(audio.state==='suspended')audio.resume();
      const oscillator=audio.createOscillator(),gain=audio.createGain(),now=audio.currentTime;
      oscillator.type='square';oscillator.frequency.setValueAtTime(frequency,now);
      oscillator.frequency.exponentialRampToValueAtTime(Math.max(40,frequency*.7),now+length);
      gain.gain.setValueAtTime(.035,now);gain.gain.exponentialRampToValueAtTime(.0001,now+length);
      oscillator.connect(gain);gain.connect(audio.destination);oscillator.start(now);oscillator.stop(now+length+.01);
    }catch(_){/* Audio is optional. */}
  }
  function feedback(message,good){const target=$('dispatch-feedback');target.textContent=message;target.className=good===true?'good':good===false?'bad':'';}
  function hud(){
    $('dispatch-round').textContent=`${round}/10`;$('dispatch-score').textContent=`${score}/100`;
    $('dispatch-best').textContent=`${best}/100`;$('dispatch-time').textContent=String(seconds);
    $('dispatch-count').textContent=`${route.length}/${challenge?.route_length||0}`;
    $('dispatch-route').replaceChildren(...route.map(name=>{const item=document.createElement('li');item.textContent=name;return item;}));
    $('dispatch-send').disabled=phase!=='playing'||route.length!==challenge.route_length;
    $('dispatch-undo').disabled=$('dispatch-clear').disabled=phase!=='playing'||route.length===0;
    document.querySelectorAll('[data-station]').forEach(button=>button.disabled=phase!=='playing'||route.length>=challenge.route_length);
  }
  function overlay(kicker,title,copy,action){$('dispatch-kicker').textContent=kicker;$('dispatch-title').textContent=title;$('dispatch-copy').textContent=copy;$('dispatch-action').textContent=action;$('dispatch-overlay').hidden=false;}
  function positionPacket(){if(!packet)return;const target=byName[route.at(-1)];packet.setPosition(target?target.x:55,target?target.y:270);}
  function select(name){
    if(phase!=='playing'||route.length>=challenge.route_length||!byName[name])return;
    route.push(name);const target=byName[name];
    scene.tweens.add({targets:packet,x:target.x,y:target.y,duration:280,ease:'Sine.easeInOut'});
    pulse(target.x,target.y,0x82ecff);tone(320+route.length*85);hud();
    if(route.length===challenge.route_length)feedback('Route complete. Send the packet to check it.');
  }
  function pulse(x,y,colour){
    if(!scene)return;const ring=scene.add.circle(x,y,28).setStrokeStyle(4,colour).setDepth(8);
    scene.tweens.add({targets:ring,scale:2,alpha:0,duration:500,onComplete:()=>ring.destroy()});
  }
  function undo(){if(phase!=='playing'||!route.length)return;route.pop();positionPacket();hud();tone(170);}
  function clear(){if(phase!=='playing')return;route=[];positionPacket();hud();feedback('Route cleared. Select the first component.');}
  async function post(action,body={}){
    const response=await fetch(`/api/games/cpu-dispatch/${action}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data=await response.json().catch(()=>({error:'The game server did not respond as expected.'}));
    if(!response.ok)throw new Error(data.error||'Could not save the packet.');return data;
  }
  function newPacket(next){
    challenge=next;route=[];seconds=25;phase='playing';positionPacket();
    $('dispatch-category').textContent=next.category.toUpperCase();$('dispatch-instruction').textContent=next.instruction;
    $('dispatch-prompt').textContent=next.prompt;
    feedback(`Choose ${next.route_length} components in order. The packet will follow your route.`);
    clearInterval(timer);timer=setInterval(()=>{if(phase!=='playing')return;seconds--;hud();
      if(seconds<=0){clearInterval(timer);send(true);}},1000);hud();
  }
  async function start(){
    if(!scene||phase==='loading')return;phase='loading';$('dispatch-action').disabled=true;$('dispatch-copy').textContent='Starting the processor…';
    try{const data=await post('start');runId=data.run_id;round=1;score=0;$('dispatch-overlay').hidden=true;newPacket(data.challenge);tone(620,.2);}
    catch(error){phase='intro';overlay('CONNECTION ERROR','SYSTEM PAUSED',error.message,'TRY AGAIN');}
    finally{$('dispatch-action').disabled=false;}
  }
  async function send(timedOut=false){
    if(phase!=='playing'||(!timedOut&&route.length!==challenge.route_length))return;
    phase='marking';clearInterval(timer);hud();feedback(timedOut?'Packet timed out. Checking…':'Packet sent. Checking…');
    try{const result=await post('answer',{run_id:runId,answer:timedOut?'TIMEOUT':route.join('>')});
      score=result.score;best=Math.max(best,result.best||0);hud();
      pulse(packet.x,packet.y,result.correct?0xbaff66:0xff64a5);tone(result.correct?740:160,.22);
      feedback(`${result.correct?'Correct route!':'Route missed.'} ${result.explanation}`,result.correct);
      if(result.finished){best=result.best;hud();setTimeout(()=>{phase='over';overlay('RUN COMPLETE','PROCESSOR CLEAR',`${score}/100 recorded marks. Best run: ${best}/100.`,'PLAY AGAIN');},1700);}
      else setTimeout(()=>{round=result.round+1;newPacket(result.next);},result.correct?1250:2100);
    }catch(error){phase='playing';feedback(error.message,false);timer=setInterval(()=>{seconds=Math.max(0,seconds-1);hud();if(!seconds){clearInterval(timer);send(true);}},1000);hud();}
  }
  new Phaser.Game({type:Phaser.AUTO,parent:'dispatch-stage',width:1000,height:540,backgroundColor:'#071831',
    scale:{mode:Phaser.Scale.FIT,autoCenter:Phaser.Scale.CENTER_BOTH,width:1000,height:540},scene:{
      create(){scene=this;const graphics=this.add.graphics();graphics.fillGradientStyle(0x06142d,0x06142d,0x133e73,0x133e73).fillRect(0,0,1000,540);
        for(let x=0;x<1000;x+=50){graphics.lineStyle(1,0x6db9e9,.09).lineBetween(x,0,x,540);}
        for(let y=0;y<540;y+=45){graphics.lineStyle(1,0x6db9e9,.09).lineBetween(0,y,1000,y);}
        const links=[['PC','MAR'],['MAR','Cache'],['MAR','RAM'],['Cache','MDR'],['RAM','MDR'],['MDR','CU'],['CU','ALU'],['ALU','Accumulator'],['CU','PC'],['CU','MAR'],['Accumulator','MDR'],['MDR','RAM']];
        links.forEach(([a,b])=>{graphics.lineStyle(5,0x23b9dc,.22);graphics.lineBetween(byName[a].x,byName[a].y,byName[b].x,byName[b].y);});
        this.add.text(28,22,'INSTRUCTION BUS  /  ROUTE CONTROL',{fontFamily:'monospace',fontSize:'17px',fontStyle:'bold',color:'#8fefff'});
        stations.forEach((station,index)=>{
          const x=station.x,y=station.y,w=station.name==='Accumulator'?170:135;
          const box=this.add.rectangle(x,y,w,77,index%3===0?0x3b286e:0x173f70).setStrokeStyle(3,index%3===0?0xff72c4:0x64e5ff).setInteractive({useHandCursor:true}).setDepth(2);
          this.add.text(x,y-13,station.name,{fontFamily:'system-ui',fontSize:station.name==='Accumulator'?'18px':'22px',fontStyle:'bold',color:'#ffffff'}).setOrigin(.5).setDepth(3);
          this.add.text(x,y+15,station.detail,{fontFamily:'monospace',fontSize:'11px',color:'#b9f5ff'}).setOrigin(.5).setDepth(3);
          this.add.text(x-w/2+8,y-29,String(index+1),{fontFamily:'monospace',fontSize:'12px',color:'#ffed97'}).setDepth(3);
          box.on('pointerdown',()=>select(station.name));
        });
        packet=this.add.container(55,270,[this.add.circle(0,0,16,0xffe66b).setStrokeStyle(3,0xffffff),this.add.text(0,0,'▶',{fontFamily:'monospace',fontSize:'17px',color:'#1b1640'}).setOrigin(.5)]).setDepth(5);
        this.tweens.add({targets:packet,scale:1.1,duration:500,yoyo:true,repeat:-1});
      }
    }});
  $('dispatch-action').addEventListener('click',start);$('dispatch-send').addEventListener('click',()=>send());
  $('dispatch-undo').addEventListener('click',undo);$('dispatch-clear').addEventListener('click',clear);
  $('dispatch-sound').addEventListener('click',()=>{soundOn=!soundOn;$('dispatch-sound').textContent=soundOn?'SOUND ON':'SOUND OFF';$('dispatch-sound').setAttribute('aria-pressed',String(soundOn));});
  document.querySelectorAll('[data-station]').forEach(button=>button.addEventListener('click',()=>select(button.dataset.station)));
  window.addEventListener('keydown',event=>{if(event.target.matches('input,textarea,select,button'))return;
    const digit=Number(event.key);if(digit>=1&&digit<=8){event.preventDefault();select(stations[digit-1].name);}
    else if(event.key==='Backspace'){event.preventDefault();undo();}
    else if(event.key==='Enter'){event.preventDefault();send();}
  });hud();
})();
