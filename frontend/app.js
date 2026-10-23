import finanzas from './modules/finanzas.js';
import reportes from './modules/reportes.js';
import administracion from './modules/administracion.js';
import reclamos from './modules/reclamos.js';
import pagos from './modules/pagos.js';
import pedidos from './modules/pedidos.js';
import ventas from './modules/ventas.js';
import clientes from './modules/clientes.js';
import inventario from './modules/inventario.js';
import productos from './modules/productos.js';
import proveedores from './modules/proveedores.js';
import marketing from './modules/marketing.js';
import envios from './modules/envios.js';
import compras from './modules/compras.js';
import {createPanelUI,panelConfig,icon} from './panels.js';

const definitions=[finanzas,reportes,administracion,reclamos,pagos,pedidos,ventas,clientes,inventario,productos,proveedores,marketing,envios,compras];
const app=document.querySelector('#app');
let session=null, refs={}, current=null, selected=null, epoch=0, lastQuery={}, result=null, routeParams=new URLSearchParams();
const e=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const bs=v=>new Intl.NumberFormat('es-BO',{style:'currency',currency:'BOB'}).format(Number(v??0)/100);
const labels={id:'ID',sku:'SKU',nombre:'Nombre',estado:'Estado',numero:'Número',referencia:'Referencia',stock_fisico:'Físico',reservado:'Reservado',disponible:'Disponible',stock_minimo:'Mínimo',precio_actual:'Precio',total:'Total',saldo:'Saldo',monto:'Monto',verificado:'Cobrado',pendiente:'Por verificar',fecha:'Fecha',fecha_registro:'Registro',cantidad:'Unidades',precio_unitario:'Precio unitario',costo_unitario:'Costo unitario',saldo_resultante:'Saldo físico',variacion:'Variación',cliente_id:'Cliente',pedido_id:'Pedido',venta_id:'Venta',producto_id:'Producto',proveedor_id:'Proveedor',usuario_id:'Usuario',rol_id:'Rol',responsable_id:'Responsable',pago_id:'Pago',frecuencia:'Ventas vigentes',unidades:'Unidades vendidas',importe:'Importe',fecha_apertura:'Apertura',fecha_resolucion:'Resolución',tipo:'Tipo',telefono:'Teléfono',direccion:'Dirección',descripcion:'Descripción',numero_guia:'Guía',fecha_despacho:'Despacho',fecha_entrega:'Entrega',evidencia_devolucion:'Evidencia de devolución',enlace_externo:'Enlace',contenido:'Contenido',fecha_emision:'Emisión',fecha_publicacion:'Publicación',observacion:'Observación',motivo:'Motivo',usuario:'Usuario',categoria:'Categoría',metodo:'Método',canal:'Canal',campania:'Campaña',vistas:'Vistas',likes:'Me gusta',comentarios:'Comentarios',fuente:'Fuente',operacion:'Operación',modulo:'Módulo',detalle:'Detalle',estado_anterior:'Estado anterior',estado_nuevo:'Estado nuevo',evidencia_entrega:'Evidencia de entrega',receptor:'Receptor',incidencia:'Incidencia'};
const moneyKeys=new Set(['monto','total','precio_actual','precio_unitario','costo_unitario','importe','saldo','verificado','pendiente','costo','ventas_vigentes','cobros_verificados','saldos_pendientes','pagos_por_verificar','total_vigente','total_anulado']);
const panelUI=createPanelUI({e,bs,format,table,permitted});
Object.assign(labels,{cliente:'Cliente',ultimo_acceso:'Último acceso',rol:'Rol',compras:'Compras',fecha_medicion:'Medición',fecha_estimada:'Entrega estimada',direccion_entrega:'Dirección de entrega',ventas_vigentes:'Ventas vigentes',cobros_verificados:'Cobros verificados',saldos_pendientes:'Saldo por cobrar',pagos_por_verificar:'Por verificar'});

async function api(path,data){
  const options=data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':session?.csrf||''},body:JSON.stringify(data)};
  const r=await fetch(path,options);
  const value=await r.json();
  if(!r.ok){if(r.status===401 && path!='/api/login'){session=null;login();}throw new Error(value.error||'No se pudo completar la operación.');}
  return value;
}
function toast(message,error=false){const el=document.querySelector('#toast');el.textContent=message;el.className=error?'show error':'show';clearTimeout(el.timer);el.timer=setTimeout(()=>el.className='',5000);}
function permitted(slug,op){return session?.permisos.includes(`${slug}.${op}`);}
function goto(slug,op){location.hash=slug?(op?`#/${slug}/${op}`:`#/${slug}`):'#/';}
function login(){
  app.innerHTML=`<main class="login"><section class="login-story"><a class="brand" href="#/"><span class="brand-mark">S</span><span>SAIQUE<small>TIENDA DE ALFOMBRAS</small></span></a><div><span class="eyebrow">GESTIÓN DEL NEGOCIO</span><h1>Cada alfombra.<br>Cada pedido.<br>Todo conectado.</h1><p>Del primer contacto a la entrega, mantené tus operaciones en un solo lugar.</p><div class="woven" aria-hidden="true"></div></div><span class="location">Tarija, Bolivia · Sistema de gestión</span></section><section class="login-form"><div class="login-box"><span class="eyebrow">BIENVENIDO</span><h2>Ingresá a tu cuenta</h2><p class="muted">Usá el usuario que te asignó el administrador.</p><form id="login-form"><label>Usuario<input name="usuario" autocomplete="username" required autofocus></label><label>Contraseña<input name="password" type="password" autocomplete="current-password" required></label><p class="form-error" role="alert"></p><button class="primary" type="submit">Iniciar sesión</button></form><p class="login-foot">Tu acceso depende de los permisos de tu rol.</p></div></section></main>`;
  document.querySelector('#login-form').addEventListener('submit',async ev=>{
    ev.preventDefault();const form=ev.currentTarget;const button=form.querySelector('button');button.disabled=true;button.textContent='Ingresando…';
    try {await api('/api/login',Object.fromEntries(new FormData(form)));await boot();}
    catch(err){form.querySelector('.form-error').textContent=err.message;}
    finally{button.disabled=false;button.textContent='Iniciar sesión';}
  });
}
function shell(){
  const available=session.modulos.map(m=>({...definitions.find(d=>d.slug===m.slug),...m}));
  const order=['finanzas','reportes','administracion','reclamos','pagos','pedidos','ventas','clientes','inventario','productos','proveedores','compras','marketing','envios'];
  const navigation=order.map(slug=>available.find(m=>m.slug===slug)).filter(Boolean);
  app.innerHTML=`<div class="workspace"><aside class="sidebar"><a class="brand" href="#/"><span class="brand-mark">S</span><span class="brand-text">SISTEMA DE<br>GESTIÓN<small>Tienda Online de Alfombras</small></span></a><a class="nav-link" data-nav="inicio" href="#/">${icon('inicio')}Inicio</a><div class="nav-group">${navigation.map(m=>`<a class="nav-link" data-nav="${m.slug}" href="#/${m.slug}">${icon(m.slug)}<span class="nav-title">${e(m.title)}</span></a>`).join('')}</div><div class="sidebar-bottom"><span class="avatar">${e(session.usuario.nombre[0])}</span><div><strong>${e(session.usuario.nombre)}</strong><small>${e(session.usuario.rol)}</small></div></div></aside><div class="main"><header class="topbar"><button class="icon-button menu-toggle" id="menu-toggle" aria-label="Abrir menú">${icon('menu')}</button><span class="topbar-left">Saique · Gestión de alfombras</span><div class="topbar-right"><span class="date">${e(new Intl.DateTimeFormat('es-BO',{dateStyle:'long',timeZone:'America/La_Paz'}).format(new Date()))}</span><span class="role-badge">${e(session.usuario.rol)}</span><button class="text-button" id="logout">Cerrar sesión</button><span class="avatar" title="${e(session.usuario.nombre)}">${e(session.usuario.nombre[0])}</span></div></header><main id="content" tabindex="-1"></main><footer>Saique · Tienda Online de Alfombras<span>Bolivianos (Bs) · Tarija, Bolivia</span></footer></div></div>`;
  document.querySelector('#logout').addEventListener('click',async()=>{try{await api('/api/logout',{});session=null;refs={};login();}catch(err){toast(err.message,true);}});
  document.querySelector('#menu-toggle').addEventListener('click',()=>document.querySelector('.sidebar').classList.toggle('open'));
}
async function boot(){
  try{session=await api('/api/session');refs={};shell();await route();}
  catch{if(!session)login();}
}
async function loadRefs(sources){
  const results=await Promise.allSettled([...new Set(sources)].filter(Boolean).filter(s=>!refs[s]).map(async source=>{refs[source]=await api(`/api/referencias/${source}`);}));
  const failed=results.find(r=>r.status==='rejected');
  if(failed)throw failed.reason;
}
async function route(){
  if(!session)return;
  const turn=++epoch;const [routePath,queryString='']=location.hash.replace(/^#\/?/,'').split('?');const [slug,rawOp]=routePath.split('/');routeParams=new URLSearchParams(queryString);
  document.querySelector('.sidebar')?.classList.remove('open');
  document.querySelectorAll('[data-nav]').forEach(a=>a.classList.toggle('active',a.dataset.nav===(slug||'inicio')));
  const content=document.querySelector('#content');content.innerHTML='<div class="loading" role="status">Cargando información…</div>';
  result=null;selected=null;lastQuery={};
  try{
    if(!slug){current=null;const d=await api('/api/dashboard');if(turn!==epoch)return;home(d);return;}
    const def=definitions.find(m=>m.slug===slug),spec=session.modulos.find(m=>m.slug===slug);
    if(!def||!spec)throw new Error('Tu rol no tiene acceso a este módulo.');
    current={...def,...spec};
    if(!rawOp){await parent(turn);return;}
    const op=Number(rawOp);if(!permitted(slug,op)||!def.operations[op-1])throw new Error('No tenés permiso para esta operación.');
    selected={...def.operations[op-1],op};
    const sources=selected.fields.map(f=>f.source).filter(Boolean);
    if(selected.fields.some(f=>f.type==='lines'))sources.push('productos');
    if(selected.fields.some(f=>f.type==='permissions'))sources.push('permisos','roles_permisos');
    if(selected.source)sources.push(selected.source);
    await loadRefs(sources);if(turn!==epoch)return;
    child();
    const form=document.querySelector('#operation-form');
    const record=routeParams.get('registro');
    if(record&&form.elements.id){form.elements.id.value=record;await prefill();}
    for(const [key,value] of routeParams){if(key!=='registro'&&form.elements[key]){form.elements[key].value=value;form.elements[key].dispatchEvent(new Event('change',{bubbles:true}));}}
    if(!selected.write&&(!selected.fields.some(f=>f.required)||record||routeParams.size))await runQuery(values(form),turn);
  }catch(err){if(turn===epoch&&session)content.innerHTML=`<section class="empty"><h2>No se pudo abrir esta pantalla</h2><p>${e(err.message)}</p><a class="button" href="#/">Volver al inicio</a></section>`;}
}
function home(data){
  document.querySelector('#content').innerHTML=`<div class="page-heading"><div><h1>Panel principal</h1><p class="muted">Resumen de la actividad de tu tienda.</p></div>${permitted('administracion',1)?'<a class="button" href="#/administracion/1?nuevo=1">+ Nuevo usuario</a>':''}</div>${panelUI.homeBody(data,session.modulos)}`;
}
function breadcrumbs(title){return `<nav class="breadcrumbs" aria-label="Ruta"><a href="#/">Inicio</a><span>/</span><a href="#/${current.slug}">${e(current.title)}</a>${title?`<span>/</span><strong>${e(title)}</strong>`:''}</nav>`;}
async function parent(turn=epoch){
  const spec=current, cfg=panelConfig[spec.slug];
  const data=await api(`/api/panel/${spec.slug}`);
  if(turn!==epoch)return;
  let quick='';
  if(cfg.quick&&permitted(spec.slug,cfg.quick)){
    selected={...spec.operations[cfg.quick-1],op:cfg.quick,compact:true};
    const sources=selected.fields.map(f=>f.source).filter(Boolean);
    if(selected.fields.some(f=>f.type==='lines'))sources.push('productos');
    await loadRefs(sources);if(turn!==epoch)return;
    quick=`<section class="panel quick-panel"><div class="panel-heading"><h2>${e(selected.title)}</h2></div>${operationForm()}<p class="notice">${e(selected.help||'Confirmá los datos para guardar la operación.')}</p></section>`;
  }
  document.querySelector('#content').innerHTML=`<div class="page-heading"><div><h1>${e(spec.title)}</h1><p class="muted">${e(spec.description)}</p></div><div class="actions">${spec.related&&session.modulos.some(m=>m.slug===spec.related.slug)?`<a class="button" href="#/${spec.related.slug}">${e(spec.related.label)}</a>`:''}${spec.slug!=='administracion'?panelUI.link(spec.slug,cfg.primary,'+ '+cfg.primaryLabel,'primary','?nuevo=1'):''}</div></div>${panelUI.operations(spec)}${panelUI.parentBody(spec,data,quick)}${spec.slug==='administracion'&&permitted('administracion',1)?'<details class="module-shortcuts"><summary>Auditoría de operaciones</summary><div class="panel-heading"><h2>Historial de cambios</h2><button class="button" id="audit">Consultar auditoría</button></div><div id="audit-result"></div></details>':''}`;
  if(quick)bindOperationForm();
  const applyFilters=()=>{
    const q=(document.querySelector('#panel-search')?.value||'').toLocaleLowerCase();
    const state=document.querySelector('#panel-state')?.value||'';
    const from=document.querySelector('#panel-from')?.value||'';
    const to=document.querySelector('#panel-to')?.value||'';
    const records=data.registros.filter(r=>(!q||Object.values(r).join(' ').toLocaleLowerCase().includes(q))&&(!state||r.estado===state)&&(!from||(r.fecha||r.fecha_registro||'').slice(0,10)>=from)&&(!to||(r.fecha||r.fecha_registro||'').slice(0,10)<=to));
    document.querySelector('#panel-records').innerHTML=panelUI.recordsTable(records,spec);
  };
  document.querySelectorAll('#panel-search,#panel-state,#panel-from,#panel-to').forEach(el=>el.addEventListener('input',applyFilters));
  document.querySelector('#panel-records')?.addEventListener('click',ev=>{
    const button=ev.target.closest('[data-inspect]');if(!button)return;
    const record=data.registros.find(r=>r.id===Number(button.dataset.inspect));
    document.querySelector('#panel-side').innerHTML=panelUI.sideDetail(spec,record);
  });
  document.querySelector('#audit')?.addEventListener('click',async()=>{try{document.querySelector('#audit-result').innerHTML=table(await api('/api/referencias/auditorias'));}catch(err){toast(err.message,true);}});
}
function interfaceCode(m,op){
  if(m.slug==='compras')return ['P.11.3','P.11.5','P.11.6'][op-1];
  return `${m.p}.${op}`;
}
function operationForm(){
  const o=selected;
  const label=o.write?(current.slug==='administracion'&&o.op===1?'Guardar usuario':current.slug==='administracion'&&o.op===2?'Guardar permisos':o.title.replace(/^Registrar /,'Guardar ')):'Consultar';
  return `<form id="operation-form">${current.slug==='administracion'&&o.op===1?'<div class="user-mode-actions"><button type="button" class="button" id="new-user">+ Nuevo usuario</button><span class="muted" id="user-mode-label">Crear o editar una cuenta</span></div>':''}<div class="form-grid">${o.fields.map(fieldHTML).join('')}</div><p class="form-error" role="alert"></p><div class="form-actions"><button class="primary" type="submit">${e(label)}</button><button class="button" type="button" id="cancel">${o.write?'Cancelar':'Limpiar filtros'}</button></div></form>`;
}
function child(){
  const o=selected;
  document.querySelector('#content').innerHTML=`
    ${breadcrumbs(o.title)}
    <div class="page-heading"><div><span class="eyebrow">CU${current.cu}.${o.op} · ${e(interfaceCode(current,o.op))}</span><h1>${e(o.title)}</h1></div><a class="button" href="#/${current.slug}">Volver al módulo</a></div>
    ${panelUI.operations(current,o.op)}
    <div class="child-layout">
      <section class="panel form-panel"><div class="form-topline"><h2>${o.write?'Datos de la operación':'Filtros de consulta'}</h2><span>${o.write?'* Campos obligatorios':'Consultas sin modificar registros'}</span></div>${operationForm()}</section>
      <aside class="operation-help"><h3>${o.auto?'Resultado automático':'Información de la operación'}</h3><p>${e(o.help||current.description)}</p><p>${o.write?'Revisá los datos antes de guardar. Cancelar no confirma la operación.':'Consultá los documentos registrados y seleccioná los filtros que necesitás.'}</p><a class="button" href="#/${current.slug}">Volver a ${e(current.title.replace('Gestionar ',''))}</a></aside>
    </div>
    <section class="panel result-panel" ${o.write?'hidden':''}><div class="panel-heading"><div><h2>${o.write?'Operación registrada':'Resultados de la consulta'}</h2><p class="muted" id="result-meta"></p></div><div class="actions" id="result-actions"></div></div><div id="result">${empty('Seleccioná los filtros y consultá los registros.')}</div></section>
    ${o.source&&o.write?`<section class="panel source-panel"><div class="panel-heading"><h2>${current.slug==='administracion'&&o.op===1?'Usuarios registrados':'Registros disponibles'}</h2><span class="muted">Seleccioná un registro para editar o continuar</span></div><div id="source-table">${table(refs[o.source]||[],{source:true})}</div></section>`:''}`;
  bindOperationForm();
  if(current.slug==='administracion'&&o.op===1){
    const form=document.querySelector('#operation-form');
    form.elements.estado.value='Activo';
    document.querySelector('#new-user')?.addEventListener('click',()=>{form.reset();form.elements.id.value='';form.elements.estado.value='Activo';document.querySelector('#user-mode-label').textContent='Nuevo usuario';form.elements.nombre.focus();});
    if(routeParams.has('nuevo'))document.querySelector('#new-user').click();
  }
}
function bindOperationForm(){
  const o=selected;
  const form=document.querySelector('#operation-form');
  form.querySelectorAll('[data-lines]').forEach(group=>addLine(group));
  form.querySelectorAll('[data-add-line]').forEach(button=>button.addEventListener('click',()=>addLine(button.closest('[data-lines]'))));
  form.querySelectorAll('[data-asset]').forEach(input=>input.addEventListener('change',upload));
  form.querySelector('[name=id]')?.addEventListener('change',prefill);
  form.querySelector('[name=rol_id]')?.addEventListener('change',fillPermissions);
  form.querySelector('[name=cliente_id]')?.addEventListener('change',()=>{const client=refs.clientes?.find(r=>r.id===Number(form.elements.cliente_id.value));if(client&&current.slug==='pedidos'){form.elements.direccion_entrega.value=client.direccion||'';form.elements.referencia_entrega.value=client.referencia||'';}});
  form.querySelector('[name=pedido_id]')?.addEventListener('change',()=>{const order=refs.pedidos?.find(r=>r.id===Number(form.elements.pedido_id.value));if(current.slug==='ventas'){const group=form.querySelector('[data-lines]');group.hidden=Boolean(order);group.querySelectorAll('input,select').forEach(el=>el.disabled=Boolean(order));}if(order&&current.slug==='envios'){form.elements.direccion.value=order.direccion_entrega;form.elements.referencia.value=order.referencia_entrega||'';}});
  form.addEventListener('submit',submit);
  document.querySelector('#cancel')?.addEventListener('click',()=>{if(o.compact){form.reset();form.querySelectorAll('[data-lines] .line-rows').forEach(el=>el.innerHTML='');form.querySelectorAll('[data-lines]').forEach(addLine);}else if(o.write)goto(current.slug);else{form.reset();document.querySelector('#result').innerHTML=empty('Filtros limpiados. Podés realizar otra consulta.');}});
  document.querySelector('#source-table')?.addEventListener('click',async ev=>{const b=ev.target.closest('[data-record]');if(!b)return;const value=b.dataset.record;const picker=form.elements.id||form.elements.pago_id||form.elements.respaldo_id||form.elements.rol_id;if(picker){picker.value=value;await prefill();fillPermissions();form.scrollIntoView({behavior:'smooth',block:'start'});}});
  if(o.fields.some(f=>f.type==='permissions'))fillPermissions();
}
function optionLabel(row,source){
  if(source==='productos')return `${row.sku} · ${row.nombre} · ${bs(row.precio_actual)} · ${row.disponible} disp.`;
  if(source==='pagos')return `PG-${row.id} · ${bs(row.monto)} · ${row.estado} · ${row.referencia}`;
  return `${row.numero||row.nombre||row.contacto||'#'+row.id}${row.referencia&&source==='compras'?' · '+row.referencia:''}${row.estado?' · '+row.estado:''}`;
}
function fieldHTML(field){
  const required=field.required?' required':'';
  const name=e(field.name);
  const cls=['textarea','lines','multiselect','permissions'].includes(field.type)?'full':'';
  let input='';
  if(field.type==='select')input=`<select name="${name}"${required}><option value="">${field.required?'Seleccionar…':'Todos / sin selección'}</option>${field.source?(refs[field.source]||[]).map(r=>`<option value="${r.id}">${e(optionLabel(r,field.source))}</option>`).join(''):field.options.map(v=>`<option value="${e(v)}">${e(v)}</option>`).join('')}</select>`;
  else if(field.type==='textarea')input=`<textarea name="${name}" rows="3"${required}></textarea>`;
  else if(field.type==='checkbox')return `<label class="check-field full"><input name="${name}" type="checkbox"> <span>${e(field.label)}</span></label>`;
  else if(field.type==='lines')return `<div class="lines-field full" data-lines data-cost="${field.cost?'1':'0'}"><div class="line-heading"><h3>${e(field.label)}</h3><button class="button small" type="button" data-add-line>Agregar alfombra</button></div><div class="line-rows"></div><p class="muted line-total">Total estimado: ${bs(0)}</p></div>`;
  else if(field.type==='multiselect')input=`<div class="check-grid">${(refs[field.source]||[]).filter(r=>r.estado==='Activo').map(r=>`<label class="check-field"><input type="checkbox" name="${name}" value="${r.id}"><span>${e(optionLabel(r,field.source))}</span></label>`).join('')||'<p class="muted">No hay productos activos. Registrá una alfombra primero.</p>'}</div>`;
  else if(field.type==='permissions')input=`<div class="permission-grid">${(refs.permisos||[]).map(p=>`<label class="check-field"><input type="checkbox" name="permisos" value="${e(p.codigo)}"><span><small>${e(p.codigo)}</small>${e(p.descripcion)}</span></label>`).join('')}</div>`;
  else if(field.type==='asset')input=`<input name="${name}" type="text" placeholder="https://… o cargá un archivo"><input type="file" data-asset="${name}" accept="image/png,image/jpeg,image/webp,application/pdf,video/mp4"><small class="muted">PNG, JPG, WebP, PDF o MP4 · hasta 8 MB</small>`;
  else input=`<input name="${name}" type="${e(field.type)}"${required}${field.min!==undefined?` min="${field.min}"`:''}${field.step?` step="${field.step}"`:''}${field.default!==undefined?` value="${e(field.default)}"`:''}${field.type==='password'?' autocomplete="new-password"':''}>`;
  return `<label class="field ${cls}"><span>${e(field.label)}${field.required?'<span class="required"> *</span>':''}</span>${input}</label>`;
}
function addLine(group,values={}){
  const cost=group.dataset.cost==='1';
  const row=document.createElement('div');row.className='line-row';
  row.innerHTML=`<label>Alfombra<select data-product required><option value="">Seleccionar alfombra…</option>${(refs.productos||[]).filter(p=>p.estado==='Activo'||p.id===values.producto_id).map(p=>`<option value="${p.id}">${e(optionLabel(p,'productos'))}</option>`).join('')}</select></label><label>Unidades<input data-quantity type="number" min="1" step="1" required value="${e(values.cantidad||1)}"></label><label>${cost?'Costo':'Precio'} (Bs)<input data-price type="number" min="0.01" step=".01" required value="${values.precio_unitario?values.precio_unitario/100:values.costo_unitario?values.costo_unitario/100:''}"></label><button type="button" class="icon-button remove-line" aria-label="Quitar alfombra">×</button>`;
  group.querySelector('.line-rows').append(row);
  const select=row.querySelector('[data-product]');select.value=values.producto_id||'';
  select.addEventListener('change',()=>{const p=refs.productos.find(p=>p.id===Number(select.value));if(p&&!cost)row.querySelector('[data-price]').value=(p.precio_actual/100).toFixed(2);lineTotal(group);});
  row.addEventListener('input',()=>lineTotal(group));
  row.querySelector('.remove-line').addEventListener('click',()=>{row.remove();lineTotal(group);});
  lineTotal(group);
}
function lineTotal(group){const total=[...group.querySelectorAll('.line-row')].reduce((sum,row)=>sum+Number(row.querySelector('[data-quantity]').value)*Number(row.querySelector('[data-price]').value),0);group.querySelector('.line-total').textContent='Total estimado: '+bs(Math.round(total*100));}
async function upload(ev){
  const file=ev.target.files[0];if(!file)return;
  if(file.size>8_000_000){toast('El archivo debe pesar hasta 8 MB.',true);return;}
  const field=ev.target.dataset.asset;const target=ev.target.closest('form').elements[field];ev.target.disabled=true;
  try{const raw=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=reject;reader.readAsDataURL(file);});const extension=file.name.split('.').pop().toLowerCase().replace('jpeg','jpg');const data=await api('/api/archivo',{contenido:raw,extension});target.value=data.url;toast('Archivo cargado. Confirmá el formulario para vincularlo.');}catch(err){toast(err.message,true);}finally{ev.target.disabled=false;}
}
async function prefill(){
  const form=document.querySelector('#operation-form');const picker=form?.elements.id;
  if(!selected?.prefill||!picker?.value)return;
  const turn=epoch;
  try{
    let data=refs[selected.source]?.find(r=>r.id===Number(picker.value));
    if(current.slug==='pedidos')data=(await api(`/api/pedidos/2?id=${picker.value}`))[0];
    if(current.slug==='productos'){await loadRefs(['categorias']);data={...data,...(await api('/api/referencias/productos')).find(r=>r.id===Number(picker.value))};}
    if(turn!==epoch||!data)return;
    for(const field of selected.fields){const input=form.elements[field.name];if(!input||field.name==='id'||field.type==='password'||field.type==='lines')continue;if(data[field.name]!==undefined)input.value=moneyKeys.has(field.name)?Number(data[field.name])/100:data[field.name]??'';}
    if(data.lineas){const group=form.querySelector('[data-lines]');group.querySelector('.line-rows').innerHTML='';data.lineas.forEach(l=>addLine(group,l));}
  }catch(err){toast(err.message,true);}
}
function fillPermissions(){
  const form=document.querySelector('#operation-form');if(!form||!selected.fields.some(f=>f.type==='permissions'))return;
  const rid=Number(form.elements.rol_id.value);const ids=(refs.roles_permisos||[]).filter(r=>r.rol_id===rid).map(r=>r.permiso_id);const codes=(refs.permisos||[]).filter(p=>ids.includes(p.id)).map(p=>p.codigo);
  form.querySelectorAll('[name=permisos]').forEach(el=>el.checked=codes.includes(el.value));
}
function values(form){
  const d={};
  for(const field of selected.fields){
    if(field.type==='lines'){
      if(current.slug==='ventas'&&form.elements.pedido_id.value)continue;
      const group=form.querySelector('[data-lines]');d.lineas=[...group.querySelectorAll('.line-row')].map(row=>({producto_id:row.querySelector('[data-product]').value,cantidad:row.querySelector('[data-quantity]').value,[field.cost?'costo_unitario':'precio_unitario']:row.querySelector('[data-price]').value}));
    }else if(field.type==='checkbox')d[field.name]=form.elements[field.name].checked;
    else if(['permissions','multiselect'].includes(field.type))d[field.name]=[...form.querySelectorAll(`[name="${field.name}"]:checked`)].map(x=>x.value);
    else{const value=form.elements[field.name]?.value?.trim();if(value!==''&&value!==undefined)d[field.name]=value;}
  }
  if(current.slug==='envios'&&selected.op===2&&d.transporte_nombre)d.nuevo_transportista={nombre:d.transporte_nombre,telefono:d.transporte_telefono};
  if(current.slug==='marketing'&&[1,2].includes(selected.op)&&d.metrica_fuente)d.metricas={vistas:d.metrica_vistas||0,likes:d.metrica_likes||0,comentarios:d.metrica_comentarios||0,fuente:d.metrica_fuente};
  return d;
}
async function submit(ev){
  ev.preventDefault();const form=ev.currentTarget;const button=form.querySelector('[type=submit]');const turn=epoch;form.querySelector('.form-error').textContent='';
  const group=form.querySelector('[data-lines]');if(group?.hidden){group.querySelectorAll('input,select').forEach(el=>el.required=false);}
  button.disabled=true;const original=button.textContent;button.textContent=selected.write?'Guardando…':'Consultando…';
  try{
    const d=values(form);
    if(selected.write){
      const slug=current.slug,op=selected.op;const out=await api(`/api/${slug}/${op}`,d);
      if(turn!==epoch)return;
      if(selected.compact){refs={};await parent(turn);toast('Operación completada.');return;}
      showResult(out);toast('Operación completada.');refs={};
      if(out.reiniciar_sesion){session=null;login();toast(out.mensaje);return;}
      const sources=selected.fields.map(f=>f.source).filter(Boolean);if(selected.source)sources.push(selected.source);if(selected.fields.some(f=>f.type==='lines'))sources.push('productos');if(selected.fields.some(f=>f.type==='permissions'))sources.push('permisos','roles_permisos');await loadRefs(sources);
      if(selected.source&&document.querySelector('#source-table'))document.querySelector('#source-table').innerHTML=table(refs[selected.source],{source:true});
      if(slug==='administracion'&&op===2){await boot();}
    }else await runQuery(d,turn);
  }catch(err){if(turn===epoch){form.querySelector('.form-error').textContent=err.message;toast(err.message,true);}}
  finally{if(turn===epoch){button.disabled=false;button.textContent=original;}}
}
async function runQuery(d,turn=epoch){
  const el=document.querySelector('#result');el.innerHTML='<div class="loading" role="status">Consultando registros…</div>';
  try{const out=await api(`/api/${current.slug}/${selected.op}?${new URLSearchParams(d)}`);if(turn!==epoch)return;lastQuery=d;showResult(out);}
  catch(err){if(turn===epoch){el.innerHTML=`<div class="empty"><h3>No se pudo completar la consulta</h3><p>${e(err.message)}</p><button class="button" id="retry">Reintentar</button></div>`;document.querySelector('#retry').onclick=()=>runQuery(d);throw err;}}
}
function empty(message){return `<div class="empty"><span class="empty-icon">▤</span><h3>${e(message)}</h3></div>`;}
function format(key,value){
  if(value===null||value===undefined||value==='')return '<span class="muted">—</span>';
  if(moneyKeys.has(key))return e(bs(value));
  if(key==='estado'||key==='estado_nuevo'||key==='estado_anterior')return `<span class="status ${['Verificado','Vigente','Activo','Entregado','Solucionado','Resuelta','Recibida','Disponible'].includes(value)?'positive':['Cancelado','Anulada','Anulado','Rechazado','Inactivo'].includes(value)?'negative':'pending'}">${e(String(value).replace('verificacion','verificación').replace('revision','revisión').replace('transito','tránsito'))}</span>`;
  if(key.endsWith('_id')){const sources={cliente_id:'clientes',producto_id:'productos',pedido_id:'pedidos',venta_id:'ventas',proveedor_id:'proveedores',rol_id:'roles',usuario_id:'usuarios',responsable_id:'usuarios',pago_id:'pagos',transportista_id:'transportistas'};const r=refs[sources[key]]?.find(r=>r.id===Number(value));if(r)return e(r.nombre||r.numero||'#'+value);}
  if(key==='imagen_url'&&/^https?:|^\/archivos\//.test(value))return `<img class="product-thumbnail" src="${e(value)}" alt="Imagen de la alfombra" loading="lazy">`;
  if((key.endsWith('_url')||key==='enlace_externo')&&/^https?:|^\/archivos\/|^\/api\//.test(value))return `<a href="${e(value)}" target="_blank" rel="noopener">Ver archivo / enlace</a>`;
  if((key.startsWith('fecha')||key==='ultimo_acceso')&&String(value).includes('T'))return e(new Intl.DateTimeFormat('es-BO',{dateStyle:'short',timeStyle:'short',timeZone:'America/La_Paz'}).format(new Date(value)));
  return e(value);
}
function table(records,options={}){
  if(!records?.length)return empty('Sin registros para mostrar.');
  const skip=new Set(['password_hash','archivo','ubicacion','sha256','checksum','version','creador_id','registrador_id','verificador_id','rol_estado']);
  let keys=[...new Set(records.flatMap(r=>Object.keys(r).filter(k=>r[k]===null||typeof r[k]!=='object'))) ].filter(k=>!skip.has(k));
  if(options.source)keys=keys.filter(k=>['id','numero','nombre','usuario','rol_id','sku','estado','referencia','monto','precio_actual','stock_fisico','reservado','disponible','fecha','telefono','rubro','canal','contenido'].includes(k));
  const preferred=['id','numero','sku','nombre','cliente','telefono','estado'];if(options.columns)keys=options.columns;else keys.sort((a,b)=>(preferred.includes(a)?preferred.indexOf(a):50)-(preferred.includes(b)?preferred.indexOf(b):50));
  const pageSize=20,tableId='t'+Math.random().toString(36).slice(2);
  setTimeout(()=>{const wrap=document.getElementById(tableId);if(!wrap)return;let page=0;const count=Math.ceil(records.length/pageSize);const draw=()=>{wrap.querySelectorAll('tbody tr').forEach((row,i)=>row.hidden=i<page*pageSize||i>=(page+1)*pageSize);wrap.querySelector('[data-page-label]').textContent=`${page+1} / ${count}`;wrap.querySelector('[data-prev]').disabled=page===0;wrap.querySelector('[data-next]').disabled=page===count-1;};wrap.querySelector('[data-prev]').onclick=()=>{page--;draw();};wrap.querySelector('[data-next]').onclick=()=>{page++;draw();};draw();},0);
  return `<div class="data-table" id="${tableId}"><div class="table-scroll"><table><thead><tr>${keys.map(k=>`<th>${e(labels[k]||k.replaceAll('_',' '))}</th>`).join('')}${options.source||options.actions?'<th>Acción</th>':''}</tr></thead><tbody>${records.map(r=>`<tr>${keys.map(k=>`<td>${format(k,r[k])}</td>`).join('')}${options.actions?`<td>${options.actions(r)}</td>`:options.source?`<td><button type="button" class="text-button" data-record="${r.id}">Seleccionar</button>${current?.slug==='administracion'&&selected?.source==='respaldos'&&permitted('administracion',3)?` <a class="text-button" href="/api/respaldo/${r.id}">Descargar</a>`:''}</td>`:''}</tr>`).join('')}</tbody></table></div><div class="pagination"><span>${records.length} registros</span><div><button class="button small" data-prev>Anterior</button><span data-page-label></span><button class="button small" data-next>Siguiente</button></div></div></div>`;
}
function renderData(data,depth=0){
  if(Array.isArray(data)){
    if(data.length===1&&data[0]?.lineas)return renderData(data[0],depth);
    return table(data);
  }
  if(!data||typeof data!=='object')return `<p>${e(data)}</p>`;
  const scalar=Object.entries(data).filter(([k,v])=>v===null||typeof v!=='object');
  const summaries=scalar.filter(([k])=>['ventas_vigentes','cobros_verificados','saldos_pendientes','pagos_por_verificar','total_vigente','total_anulado','vistas','likes','comentarios'].includes(k));
  let out=summaries.length?`<div class="result-stats">${summaries.map(([k,v])=>`<div><span>${e(labels[k]||k.replaceAll('_',' '))}</span><strong>${moneyKeys.has(k)?bs(v):e(v)}</strong></div>`).join('')}</div>`:'';
  const summaryKeys=new Set(summaries.map(([k])=>k));
  const fields=scalar.filter(([k])=>!summaryKeys.has(k)&&!['nota','mensaje','reiniciar_sesion','compartir_url','archivo_url','password_hash','sha256','checksum','ubicacion'].includes(k));
  if(fields.length)out+=`<dl class="detail-grid">${fields.map(([k,v])=>`<div><dt>${e(labels[k]||k.replaceAll('_',' '))}</dt><dd>${format(k,v)}</dd></div>`).join('')}</dl>`;
  if(data.nota)out+=`<p class="notice">${e(data.nota)}</p>`;
  if(data.mensaje)out+=`<p class="notice">${e(data.mensaje)}</p>`;
  const nestedTitles={lineas:'Alfombras del documento',cuenta:'Cuenta del documento',pagos:'Pagos asociados',envios:'Seguimiento de envíos',movimientos:'Movimientos de inventario',historial:'Historial de atención',asignaciones:'Historial de transporte',cuentas:'Cuentas por cobrar',ingresos:'Ingresos reconocidos',registros:'Registros',cliente:'Cliente',pedidos:'Pedidos',ventas:'Ventas',compras:'Compras',productos:'Productos del catálogo'};
  for(const [k,v] of Object.entries(data).filter(([,v])=>v!==null&&typeof v==='object'))out+=`<section class="nested-data"><h3>${e(nestedTitles[k]||k)}</h3>${renderData(v,depth+1)}</section>`;
  if(data.compartir_url)out+=`<a class="button" href="${e(data.compartir_url)}" target="_blank" rel="noopener">Compartir en WhatsApp</a><p class="muted">Confirmá el envío en WhatsApp. Luego registrá su evidencia aquí.</p>`;
  if(data.archivo_url?.startsWith('/api/comprobante/'))out+=`<a class="button" href="${e(data.archivo_url)}" target="_blank" rel="noopener">Abrir comprobante / guardar PDF</a>`;
  if(current?.slug==='administracion'&&selected?.op===3&&data.id)out+=`<a class="button" href="/api/respaldo/${data.id}">Descargar respaldo verificado</a>`;
  return out||empty('Sin registros para mostrar.');
}
function showResult(data){
  document.querySelector('.result-panel')?.removeAttribute('hidden');
  result=data;document.querySelector('#result').innerHTML=renderData(data);document.querySelector('#result-meta').textContent=selected.auto?'Consulta del resultado automático':'Información obtenida del sistema';
  const actions=document.querySelector('#result-actions');actions.innerHTML=selected.export?'<button class="button small" id="pdf-export">Imprimir / PDF</button><button class="button small" id="excel-export">Excel</button>':'';
  document.querySelector('#pdf-export')?.addEventListener('click',()=>window.print());
  document.querySelector('#excel-export')?.addEventListener('click',()=>{location.href=`/api/${current.slug}/${selected.op}?${new URLSearchParams({...lastQuery,formato:'xlsx'})}`;});
  if(selected.related&&permitted(selected.related.slug,selected.related.op))actions.insertAdjacentHTML('beforeend',`<a class="button small" href="#/${selected.related.slug}/${selected.related.op}">${e(selected.related.label)}</a>`);
}
window.addEventListener('hashchange',route);
boot();
