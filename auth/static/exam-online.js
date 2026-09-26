const examData=JSON.parse(document.getElementById('exam-attempt-data').textContent),examForm=document.getElementById('online-exam-form');
if(examData.editable){
  let changed=false;
  const draftKey='byteon-exam-draft:'+examData.username+':'+examData.test_id;
  function collect(){const answers={};document.querySelectorAll('[data-qid]').forEach(section=>{
    const answer={},value=section.querySelector('[data-value]'),working=section.querySelector('[data-working]');
    if(value)answer.value=value.value;if(working)answer.working=working.value;
    if(['single_choice','multiple_choice'].includes(section.dataset.kind))answer.choices=[...section.querySelectorAll('[data-choice]:checked')].map(input=>Number(input.dataset.choice)).sort((a,b)=>a-b);
    if(section.dataset.kind==='word_bank')answer.blanks=[...section.querySelectorAll('[data-blank]')].sort((a,b)=>Number(a.dataset.blank)-Number(b.dataset.blank)).map(s=>s.value);
    if(section.dataset.kind==='matching')answer.matches=[...section.querySelectorAll('[data-match]')].map(s=>Number(s.value));
    if(section.dataset.kind==='table'){answer.table={};section.querySelectorAll('[data-table]').forEach(input=>answer.table[input.dataset.table]=input.value);const groups={};section.querySelectorAll('[data-table-choice]:checked').forEach(input=>(groups[input.dataset.tableChoice]||=[]).push(input.value));Object.entries(groups).forEach(([key,values])=>answer.table[key]=values.join('|'));}
    answers[section.dataset.qid]=answer;
  });return answers;}
  function retain(){try{sessionStorage.setItem(draftKey,JSON.stringify({revision:examForm.elements.revision.value,answers:collect()}));}catch(_){} }
  try{const draft=JSON.parse(sessionStorage.getItem(draftKey)||'null');if(draft&&draft.revision===examForm.elements.revision.value){document.querySelectorAll('[data-qid]').forEach(section=>{const a=draft.answers[section.dataset.qid]||{};section.querySelectorAll('[data-value]').forEach(e=>e.value=a.value||'');section.querySelectorAll('[data-working]').forEach(e=>e.value=a.working||'');section.querySelectorAll('[data-choice]').forEach(e=>e.checked=(a.choices||[]).includes(Number(e.dataset.choice)));section.querySelectorAll('[data-blank]').forEach(e=>e.value=(a.blanks||[])[Number(e.dataset.blank)]||'');section.querySelectorAll('[data-match]').forEach((e,i)=>e.value=(a.matches||[])[i]??-1);section.querySelectorAll('[data-table]').forEach(e=>e.value=(a.table||{})[e.dataset.table]||'');section.querySelectorAll('[data-table-choice]').forEach(e=>e.checked=((a.table||{})[e.dataset.tableChoice]||'').split('|').includes(e.value));});changed=true;document.getElementById('exam-save-status').textContent='Recovered unsaved answers from this tab.';}}catch(_){}
  examForm.addEventListener('input',()=>{changed=true;retain();document.getElementById('exam-save-status').textContent='Unsaved answers';});
  examForm.addEventListener('submit',async event=>{event.preventDefault();const action=event.submitter?.value||'save';if(action==='submit'&&!confirm('Submit this test? You will not be able to change your answers afterwards.'))return;const buttons=[...examForm.querySelectorAll('button')];buttons.forEach(b=>b.disabled=true);retain();const body=new FormData(examForm);body.set('action',action);body.set('answers',JSON.stringify(collect()));
    try{const response=await fetch(location.pathname,{method:'POST',body}),result=await editorResponse(response);changed=false;try{sessionStorage.removeItem(draftKey);}catch(_){}examForm.elements.revision.value=result.revision;document.getElementById('exam-save-status').textContent=result.message;if(result.submitted)location.reload();}catch(error){document.getElementById('exam-save-status').textContent=error.message+' Unsaved answers are retained in this tab.';}finally{buttons.forEach(b=>b.disabled=false);}
  });
  window.addEventListener('beforeunload',event=>{if(changed){retain();event.preventDefault();event.returnValue='';}});
}
