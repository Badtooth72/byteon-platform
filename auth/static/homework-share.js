document.addEventListener('click',async event=>{
  const button=event.target.closest('[data-copy-homework-link]');
  if(!button)return;
  const input=document.getElementById(button.dataset.copyHomeworkLink);
  const status=button.closest('.homework-share')?.querySelector('.homework-copy-status');
  if(!input)return;
  try{
    if(navigator.clipboard?.writeText){await navigator.clipboard.writeText(input.value);}
    else{input.focus();input.select();if(!document.execCommand('copy'))throw new Error('copy unavailable');}
    if(status)status.textContent='Link copied. Paste it into SatchelOne.';
  }catch(_){input.focus();input.select();if(status)status.textContent='Select and copy the highlighted link.';}
});
