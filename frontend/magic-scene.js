// One restrained panoramic motion, suspended when hidden or unmounted.
export function mountMagicScene(root) {
  const layer=root.querySelector('.atelier-landscape');
  const button=root.querySelector('.motion-toggle');
  if(!layer||!button)return;
  const preference=matchMedia('(prefers-reduced-motion: reduce)');
  let paused=preference.matches, frame=0, x=0, y=0, targetX=0, targetY=0;
  function animate(){
    frame=0;
    if(paused||document.hidden||!root.isConnected)return;
    x+=(targetX-x)*.065; y+=(targetY-y)*.065;
    layer.style.transform=`scale(1.045) translate3d(${x*12}px,${y*8}px,0)`;
    if(Math.abs(x-targetX)+Math.abs(y-targetY)>.001)frame=requestAnimationFrame(animate);
  }
  function update(){
    cancelAnimationFrame(frame);frame=0;
    root.classList.toggle('motion-paused',paused);
    button.textContent=paused?'Activar movimiento':'Pausar movimiento';
    button.setAttribute('aria-pressed',String(paused));
    if(paused){layer.style.transform='scale(1.045)';x=y=targetX=targetY=0;}
  }
  const sync=()=>{paused=preference.matches;update();};
  const hidden=()=>{if(document.hidden){cancelAnimationFrame(frame);frame=0;}};
  root.addEventListener('pointermove',event=>{
    if(paused||event.pointerType!=='mouse')return;
    const b=root.getBoundingClientRect();
    targetX=.5-(event.clientX-b.left)/b.width;targetY=.5-(event.clientY-b.top)/b.height;
    if(!frame)frame=requestAnimationFrame(animate);
  });
  root.addEventListener('pointerleave',()=>{targetX=targetY=0;if(!frame&&!paused)frame=requestAnimationFrame(animate);});
  button.addEventListener('click',()=>{paused=!paused;update();});
  preference.addEventListener('change',sync);document.addEventListener('visibilitychange',hidden);
  const observer=new MutationObserver(()=>{if(!root.isConnected){cancelAnimationFrame(frame);preference.removeEventListener('change',sync);document.removeEventListener('visibilitychange',hidden);observer.disconnect();}});
  observer.observe(root.parentNode,{childList:true});update();
}
