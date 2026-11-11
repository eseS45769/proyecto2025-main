// Decorative pointer response; no framework, no permanent animation loop.
export function mountMagicScene(root){
  const scene=root.querySelector('.magic-scene');
  const layer=scene?.querySelector('.carpet-depth');
  const toggle=root.querySelector('.motion-toggle');
  if(!scene||!layer||!toggle)return;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  let paused=reduced.matches, frame=0, tx=0, ty=0, x=0, y=0;
  function settle(){
    frame=0;
    if(!scene.isConnected||paused)return;
    x+=(tx-x)*.12;y+=(ty-y)*.12;
    layer.style.transform=`rotateX(${-y*6}deg) rotateY(${x*9}deg) translate3d(${x*10}px,${y*6}px,30px)`;
    if(Math.abs(tx-x)+Math.abs(ty-y)>.005)frame=requestAnimationFrame(settle);
  }
  function update(){
    root.classList.toggle('motion-paused',paused);
    toggle.textContent=paused?'Activar animación':'Pausar animación';
    toggle.setAttribute('aria-pressed',String(paused));
    if(paused){cancelAnimationFrame(frame);frame=0;layer.style.transform='none';x=y=tx=ty=0;}
  }
  function syncPreference(){paused=reduced.matches;update();}
  reduced.addEventListener('change',syncPreference);
  const observer=new MutationObserver(()=>{
    if(!root.isConnected){cancelAnimationFrame(frame);reduced.removeEventListener('change',syncPreference);observer.disconnect();}
  });
  observer.observe(root.parentNode,{childList:true});
  scene.addEventListener('pointermove',event=>{
    if(paused||event.pointerType!=='mouse')return;
    const bounds=scene.getBoundingClientRect();
    tx=((event.clientX-bounds.left)/bounds.width-.5)*2;
    ty=((event.clientY-bounds.top)/bounds.height-.5)*2;
    if(!frame)frame=requestAnimationFrame(settle);
  });
  scene.addEventListener('pointerleave',()=>{tx=ty=0;if(!frame&&!paused)frame=requestAnimationFrame(settle);});
  toggle.addEventListener('click',()=>{paused=!paused;update();});
  update();
}
