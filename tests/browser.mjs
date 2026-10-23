// Prueba de navegación y formularios reales con Chrome headless y CDP, sin dependencias.
import {spawn} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';

const root=process.cwd(), output=path.join(root,'test-results');
await mkdir(output,{recursive:true});
const stamp=Date.now().toString();
const server=spawn('python',['-m','backend.server','--port','8001'],{cwd:root,env:{...process.env,SAIQUE_DATA:path.join(output,'data-'+stamp),SAIQUE_ADMIN_PASSWORD:'BrowserPruebas2026!'},windowsHide:true,stdio:['ignore','pipe','pipe']});
let serverLog='';server.stdout.on('data',d=>serverLog+=d);server.stderr.on('data',d=>serverLog+=d);
const chromePath=process.env.CHROME_PATH||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const browser=spawn(chromePath,['--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--remote-debugging-port=9222',`--user-data-dir=${path.join(output,'chrome-'+stamp)}`,'about:blank'],{windowsHide:true,stdio:'ignore'});
server.on('error',err=>console.error('Servidor:',err.message));browser.on('error',err=>console.error('Chrome:',err.message));
console.log('Iniciando prueba de navegador',server.pid,browser.pid);
let ws;
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(fn,label,ms=10000){const start=Date.now();let last;while(Date.now()-start<ms){try{const value=await fn();if(value)return value;}catch(err){last=err;}await delay(100);}throw new Error(`Tiempo excedido: ${label}. ${last?.message||''}`);}
try{
  await until(async()=>{const r=await fetch('http://127.0.0.1:8001/',{signal:AbortSignal.timeout(2000)});return r.ok;},'servidor');console.log('Servidor listo');
  await until(async()=>{const r=await fetch('http://127.0.0.1:9222/json/version',{signal:AbortSignal.timeout(2000)});return r.ok;},'Chrome');console.log('Chrome listo');
  const target=await (await fetch('http://127.0.0.1:9222/json/new?http://127.0.0.1:8001/',{method:'PUT'})).json();
  ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  let serial=0;const pending=new Map();const errors=[];
  ws.onmessage=event=>{const message=JSON.parse(event.data);if(message.id){const task=pending.get(message.id);if(!task)return;pending.delete(message.id);if(message.error)task.reject(new Error(message.error.message));else task.resolve(message.result);}else if(message.method==='Runtime.exceptionThrown'){errors.push(message.params.exceptionDetails);console.error('Error JS:',JSON.stringify(message.params.exceptionDetails));}else if(message.method==='Log.entryAdded'&&message.params.entry.level==='error')console.error('Navegador:',message.params.entry.text);};
  const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;const timer=setTimeout(()=>{pending.delete(id);reject(new Error('CDP no respondió: '+method));},10000);pending.set(id,{resolve:value=>{clearTimeout(timer);resolve(value);},reject:error=>{clearTimeout(timer);reject(error);}});ws.send(JSON.stringify({id,method,params}));});
  const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw new Error(r.exceptionDetails.text+' '+(r.exceptionDetails.exception?.description||''));return r.result.value;};
  await send('Runtime.enable');await send('Page.enable');await send('Log.enable');
  await until(()=>evaluate('Boolean(document.querySelector("#login-form"))'),'login');
  await evaluate(`document.querySelector('[name=usuario]').value='admin';document.querySelector('[name=password]').value='BrowserPruebas2026!';document.querySelector('#login-form').requestSubmit();`);
  await until(()=>evaluate('Boolean(document.querySelector(".module-grid"))'),'inicio');
  assert.equal(await evaluate('document.querySelectorAll(".module-card").length'),14);
  const titles=await evaluate(`(async()=>{const r=await fetch('/api/session');return (await r.json()).modulos;})()`);
  async function navigate(slug,op){await evaluate(`location.hash='#/${slug}${op?'/'+op:''}'`);await until(()=>evaluate(op?`Boolean(document.querySelector('#operation-form')) && document.querySelector('h1')?.textContent===${JSON.stringify(titles.find(x=>x.slug===slug).children[op-1])}`:`document.querySelector('h1')?.textContent===${JSON.stringify(titles.find(x=>x.slug===slug).title)}`),slug+'.'+op);await delay(150);}
  for(const module of titles){console.log('Revisando',module.slug);await navigate(module.slug);for(let i=1;i<=module.children.length;i++){await navigate(module.slug,i);assert.equal(await evaluate('document.querySelector(".breadcrumbs").textContent.includes(document.querySelector("h1").textContent)'),true);}}
  async function fill(data){await evaluate(`(async()=>{const form=document.querySelector('#operation-form');for(const [name,value] of Object.entries(${JSON.stringify(data)})){const el=form.elements[name];if(!el)throw new Error('Campo ausente '+name);if(el.type==='checkbox')el.checked=Boolean(value);else el.value=value;el.dispatchEvent(new Event('change',{bubbles:true}));} })()`);await delay(250);}
  async function submit(){const invalid=await evaluate(`Array.from(document.querySelectorAll('#operation-form input,#operation-form select,#operation-form textarea')).filter(el=>!el.checkValidity()).map(el=>el.name||el.outerHTML)`);assert.deepEqual(invalid,[],'Campos inválidos');await evaluate('document.querySelector("#operation-form").requestSubmit()');await until(()=>evaluate(`!document.querySelector('#operation-form button[type=submit]')?.disabled`),'guardar');const error=await evaluate(`document.querySelector('#operation-form .form-error')?.textContent`);assert.equal(error,'',error);}
  await navigate('clientes',1);await fill({nombre:'Cliente del navegador',telefono:'76123456',direccion:'Tarija centro',referencia:'Casa verde'});await submit();
  await navigate('proveedores',1);await fill({nombre:'Proveedor del navegador',telefono:'76123457',direccion:'Tarija',rubro:'Alfombras'});await submit();
  await navigate('productos',1);await fill({sku:'ALF-001',nombre:'Alfombra moderna',categoria_id:'1',descripcion:'Alfombra de prueba',ancho_cm:'120',largo_cm:'180',precio_actual:'180',stock_inicial:'0'});await submit();
  await navigate('compras',1);await fill({proveedor_id:'1',referencia:'CP-001'});await evaluate(`document.querySelector('[data-product]').value='1';document.querySelector('[data-quantity]').value='10';document.querySelector('[data-price]').value='120';`);await submit();
  await navigate('pedidos',1);await fill({cliente_id:'1',canal:'WhatsApp'});await evaluate(`document.querySelector('[data-product]').value='1';document.querySelector('[data-product]').dispatchEvent(new Event('change'));document.querySelector('[data-quantity]').value='3';`);await submit();
  await navigate('pagos',1);await fill({pedido_id:'1',monto:'540',metodo:'QR',referencia:'PG-001'});await submit();
  await navigate('pagos',2);await fill({id:'1',resultado:'Verificado',evidencia:'QR cotejado con banco'});await submit();
  await navigate('ventas',1);await fill({pedido_id:'1'});await submit();
  await navigate('pagos',3);await fill({id:'1'});await submit();assert.equal(await evaluate(`Boolean(document.querySelector('#result a[href^="/api/comprobante/"]'))`),true);
  await navigate('envios',1);await fill({pedido_id:'1',costo:'0'});await submit();
  await navigate('envios',2);await fill({id:'1',transporte_nombre:'Transporte QA',transporte_telefono:'76123458'});await submit();
  await navigate('envios',3);await fill({id:'1',numero_guia:'GUIA-001',confirmar:true});await submit();
  await navigate('envios',4);await fill({id:'1',receptor:'Cliente de prueba',evidencia_entrega:'Firma recibida',confirmar:true});await submit();
  await navigate('inventario',1);await until(()=>evaluate(`document.querySelector('#result table')?.textContent.includes('ALF-001')`),'inventario');assert.equal(await evaluate(`document.querySelector('#result').textContent.includes('7')`),true);
  await navigate('pedidos',2);await fill({id:'1'});await submit();assert.equal(await evaluate(`document.querySelector('#result').textContent.includes('Entregado')`),true);
  await navigate('reportes',1);await until(()=>evaluate(`Boolean(document.querySelector('#excel-export'))`),'reporte');const exportStatus=await evaluate(`(async()=>{const r=await fetch('/api/reportes/1?formato=xlsx');return {status:r.status,type:r.headers.get('Content-Type'),size:(await r.arrayBuffer()).byteLength};})()`);assert.equal(exportStatus.status,200);assert.ok(exportStatus.size>1000);
  await navigate('administracion',2);await fill({rol_id:'2'});assert.ok(await evaluate(`document.querySelectorAll('[name=permisos]:checked').length>0`));
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  await navigate('administracion');
  assert.equal(await evaluate(`getComputedStyle(document.querySelector('.sidebar')).backgroundColor`),'rgb(243, 236, 227)');
  assert.equal(await evaluate(`Boolean(document.querySelector('a[href="#/administracion/1?nuevo=1"]'))`),true);
  const adminShot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});await writeFile(path.join(output,'administracion-diseno.png'),Buffer.from(adminShot.data,'base64'));
  await navigate('clientes');await evaluate(`document.querySelector('[data-inspect="1"]').click()`);
  assert.equal(await evaluate(`document.querySelector('#panel-side').textContent.includes('Cliente del navegador')`),true);
  await evaluate(`document.querySelector('#panel-side a[href="#/clientes/3?registro=1"]').click()`);
  await until(()=>evaluate(`document.querySelector('#operation-form [name=nombre]')?.value==='Cliente del navegador'`),'edición desde detalle');
  const childShot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});await writeFile(path.join(output,'formulario-diseno.png'),Buffer.from(childShot.data,'base64'));
  await navigate('finanzas');await fill({pago_id:'1'});await submit();
  assert.equal(await evaluate(`document.querySelector('#panel-records').textContent.includes('PG-001')`),true);
  for(const slug of ['clientes','productos','proveedores','pedidos','pagos','inventario','envios','ventas','reportes','marketing','finanzas']){
    await navigate(slug);
    const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});await writeFile(path.join(output,slug+'-diseno.png'),Buffer.from(shot.data,'base64'));
  }
  await evaluate(`location.hash='#/'`);await until(()=>evaluate(`Boolean(document.querySelector('.module-grid'))`),'dashboard final');
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});await delay(250);
  const desktop=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});await writeFile(path.join(output,'desktop.png'),Buffer.from(desktop.data,'base64'));
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await delay(250);
  assert.equal(await evaluate('document.documentElement.scrollWidth<=window.innerWidth'),true,'Sin desbordamiento horizontal en móvil');
  const mobile=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});await writeFile(path.join(output,'mobile.png'),Buffer.from(mobile.data,'base64'));
  for(const slug of ['administracion','clientes','pagos','inventario']){
    await navigate(slug);
    assert.equal(await evaluate('document.documentElement.scrollWidth<=window.innerWidth'),true,'Móvil sin desbordamiento: '+slug);
  }
  assert.equal(errors.length,0,JSON.stringify(errors));
  const report={estado:'OK',modulos:14,hijos:55,flujo:'cliente → proveedor → producto → compra → pedido → pago → verificación → venta → comprobante → envío → transporte → guía → entrega',stock_final:7,errores_javascript:errors,excel:exportStatus,escritorio:'desktop.png',movil:'mobile.png'};
  await writeFile(path.join(output,'browser.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
}finally{ws?.close();browser.kill();server.kill();await writeFile(path.join(output,'server-test.log'),serverLog);}
