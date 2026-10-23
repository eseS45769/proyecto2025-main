// Distribución de las interfaces P del documento: indicadores, tablas y panel lateral.
export const panelConfig={
  administracion:{title:'Usuarios',source:'usuarios',primary:1,primaryLabel:'Nuevo usuario',columns:['usuario','nombre','rol','estado','ultimo_acceso'],edit:1,select:true},
  clientes:{title:'Directorio de clientes',source:'clientes',primary:1,primaryLabel:'Nuevo cliente',columns:['nombre','telefono','correo','compras','fecha_registro'],edit:3,detail:4,detailKey:'cliente_id',side:'Detalles del cliente'},
  productos:{title:'Catálogo de alfombras',source:'productos',primary:1,primaryLabel:'Nuevo producto',columns:['sku','nombre','categoria','precio_actual','disponible','estado'],edit:2,side:'Detalles del producto'},
  proveedores:{title:'Directorio de proveedores',source:'proveedores',primary:1,primaryLabel:'Nuevo proveedor',columns:['nombre','telefono','rubro','disponibilidad','estado'],edit:2,detail:4,side:'Detalle del proveedor'},
  compras:{title:'Compras recibidas',source:'compras',primary:1,primaryLabel:'Registrar compra',columns:['referencia','proveedor','fecha','total','estado'],detail:2},
  pedidos:{title:'Listado de pedidos',source:'pedidos',primary:1,primaryLabel:'Registrar pedido',columns:['numero','cliente','canal','total','estado','fecha'],detail:2,edit:3},
  ventas:{title:'Últimas transacciones',source:'ventas',primary:1,primaryLabel:'Registrar venta',columns:['numero','cliente','fecha','total','saldo','estado'],detail:2,quick:1,chart:true},
  pagos:{title:'Últimos registros',source:'pagos',primary:1,primaryLabel:'Registrar pago',columns:['referencia','fecha','metodo','monto','estado'],edit:2,quick:1},
  reclamos:{title:'Registro de reclamos',source:'reclamos',primary:1,primaryLabel:'Registrar reclamo',columns:['numero','cliente','motivo','estado','fecha'],detail:2,edit:3,side:'Detalle del reclamo'},
  inventario:{title:'Existencias de alfombras',source:'productos',primary:2,primaryLabel:'Actualizar stock',columns:['sku','nombre','stock_fisico','reservado','disponible','stock_minimo'],detail:4},
  finanzas:{title:'Últimos movimientos',source:'pagos',primary:1,primaryLabel:'Registrar ingreso',columns:['referencia','fecha','metodo','monto','estado'],quick:1},
  reportes:{title:'Reporte de ventas',source:'ventas',primary:1,primaryLabel:'Generar reporte',columns:['numero','cliente','fecha','total','saldo','estado'],detail:1},
  marketing:{title:'Publicaciones recientes',source:'publicaciones',primary:1,primaryLabel:'Publicar en TikTok',columns:['id','canal','campania','contenido','estado','fecha'],detail:4},
  envios:{title:'Listado de envíos',source:'envios',primary:1,primaryLabel:'Registrar envío',columns:['numero','pedido','cliente','transporte','numero_guia','estado','fecha_estimada'],edit:2,side:'Seguimiento del envío'},
};

const paths={
 inicio:'M3 10 12 3l9 7M5 9v12h5v-7h4v7h5V9',
 finanzas:'M3 6h18v13H3zM7 3h14v3M8 12h.01M16 12h.01M14 12a2 2 0 1 1-4 0 2 2 0 0 1 4 0',
 reportes:'M4 3h16v18H4zM8 16v-3M12 16V8M16 16v-6',
 administracion:'m12 3 2 3 3-1 1 4 3 1-2 3 1 3-4 1-1 3-3-2-3 1-1-4-3-1 2-3-1-3 4-1 1-3M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0',
 reclamos:'M4 14v-3a8 8 0 0 1 16 0v3M4 12H2v6h4v-6M20 12h2v6h-4v-6M18 18v3h-6',
 pagos:'M3 4h18v13H3zM3 8h18M14 19l3 3 5-6',
 pedidos:'M2 3h3l3 13h11l3-10H6M10 21h.01M18 21h.01',
 ventas:'M3 3h9l9 9-9 9-9-9zM7 7h.01',
 clientes:'M9 8a3 3 0 1 1 6 0 3 3 0 0 1-6 0M5 21v-2a7 7 0 0 1 14 0v2M3 7a2 2 0 0 1 0 4M21 7a2 2 0 0 0 0 4M2 20v-3M22 20v-3',
 inventario:'M3 3h18v5H3zM5 8v13h14V8M9 12h6',
 productos:'m12 2 5 8H7zM3 15h6v6H3zM15 18a3 3 0 1 1 6 0 3 3 0 0 1-6 0',
 proveedores:'M2 6h12v12H2zM14 10h5l3 4v4h-8M5 18v3M18 18v3',
 compras:'M4 3h16v18H4zM8 7h8M8 11h8M8 15h4',
 marketing:'M3 10h5l11-6v16L8 14H3zM7 14l2 7h3l-2-6M22 8v8',
 envios:'m3 7 9-4 9 4v12l-9 4-9-4zM3 7l9 4 9-4M12 11v12M7 5l10 4',
 plus:'M12 5v14M5 12h14',logout:'M9 4H3v16h6M14 7l5 5-5 5M8 12h11',bell:'M6 17V9a6 6 0 0 1 12 0v8l2 2H4zM10 22h4',search:'M16 16l5 5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0',user:'M8 6a4 4 0 1 1 8 0 4 4 0 0 1-8 0M4 22v-2a8 8 0 0 1 16 0v2',backup:'M7 17H5a4 4 0 1 1 0-8 7 7 0 0 1 14-1 5 5 0 0 1 0 10h-2M12 11v11M8 15l4-4 4 4',alert:'m12 3 10 18H2zM12 9v5M12 18h.01',edit:'m3 16 12-12 5 5L8 21H3zM13 6l5 5',arrow:'m9 5 7 7-7 7',check:'m4 12 5 5L20 6',menu:'M3 6h18M3 12h18M3 18h18'
};
export function icon(name){return `<svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${paths[name]||paths.productos}"/></svg>`;}

export function createPanelUI({e,bs,format,table,permitted}){
  const link=(slug,op,label,classes='button',query='')=>permitted(slug,op)?`<a class="${classes}" href="#/${slug}/${op}${query}">${e(label)}</a>`:'';
  function cards(items=[]){return `<div class="stats compact-stats">${items.map((m,i)=>`<div class="stat tone-${e(m.tono||'neutral')}"><div class="stat-icon">${icon(['ventas','pedidos','inventario','pagos'][i%4])}</div><span>${e(m.label)}</span><strong>${m.moneda?bs(m.valor):e(m.valor)}</strong></div>`).join('')}</div>`;}
  function chart(series=[],title='Ventas generales'){
    const max=Math.max(1,...series.map(p=>p.valor));
    return `<section class="panel chart-panel"><div class="panel-heading"><h2>${e(title)}</h2><span class="outline-tag">Últimos 7 días</span></div><div class="chart-body"><div class="bar-chart" role="img" aria-label="Ventas de los últimos siete días en bolivianos">${series.map(p=>{const day=new Date(p.fecha+'T12:00:00');const height=Math.round(p.valor/max*150);return `<div class="bar-column"><span class="bar-value">${bs(p.valor)}</span><svg viewBox="0 0 70 160" preserveAspectRatio="none" aria-hidden="true"><rect x="8" y="${160-height}" width="54" height="${Math.max(2,height)}" rx="2" fill="currentColor"/></svg><span>${e(new Intl.DateTimeFormat('es-BO',{weekday:'short'}).format(day))}</span></div>`;}).join('')}</div>${series.some(p=>p.valor)?'':'<p class="chart-empty">Sin ventas registradas en este periodo</p>'}</div></section>`;
  }
  function bestSellers(items=[]){return `<section class="panel"><div class="panel-heading"><h2>Productos más vendidos</h2></div><div class="ranking-list">${items.map((p,i)=>`<div class="ranking-row"><span class="rank">${i+1}</span><div><strong>${e(p.nombre)}</strong><small>${p.unidades} unidades vendidas</small></div><span>${bs(p.importe)}</span></div>`).join('')||'<p class="quiet-empty">Todavía no hay ventas registradas.</p>'}</div></section>`;}
  function alerts(items=[]){return `<section class="panel"><div class="panel-heading"><h2>${icon('alert')} Alertas</h2></div><div class="alerts-list">${items.map(a=>`<a class="alert-item tone-${e(a.tono)}" href="#/${e(a.ruta)}">${icon('alert')}<div><strong>${e(a.titulo)}</strong><span>${e(a.detalle)}</span></div></a>`).join('')||'<p class="quiet-empty">Sin alertas pendientes.</p>'}</div></section>`;}
  function operations(m,active=0){return `<nav class="operation-tabs" aria-label="Operaciones de ${e(m.title)}">${m.operations.map((o,i)=>permitted(m.slug,i+1)?`<a class="operation-tab ${active===i+1?'active':''}" href="#/${m.slug}/${i+1}" title="CU${m.cu}.${i+1}">${e(o.title)}${o.auto?'<span class="automatic-mark" title="Resultado automático">A</span>':''}</a>`:'').join('')}</nav>`;}
  function miniFields(r,keys){return `<dl class="compact-details">${keys.filter(k=>r[k]!==undefined&&r[k]!==null&&r[k]!=='').map(k=>`<div><dt>${e(({precio_actual:'Precio',stock_fisico:'Físico',stock_minimo:'Mínimo',disponible:'Disponible',direccion_entrega:'Dirección de entrega',numero_guia:'Guía',fecha_estimada:'Fecha estimada',referencia:'Referencia',telefono:'Teléfono',correo:'Correo',nombre:'Nombre',descripcion:'Descripción',direccion:'Dirección',estado:'Estado',motivo:'Motivo',cliente:'Cliente',representante:'Representante',disponibilidad:'Atención',ancho_cm:'Ancho (cm)',largo_cm:'Largo (cm)',transporte:'Transporte'})[k]||k.replaceAll('_',' '))}</dt><dd>${format(k,r[k])}</dd></div>`).join('')}</dl>`;}
  function sideDetail(m,r){
    const cfg=panelConfig[m.slug];
    if(!r)return `<section class="panel side-detail"><div class="panel-heading"><h2>${e(cfg.side)}</h2></div><div class="quiet-empty">Seleccioná un registro de la tabla para ver sus datos.</div></section>`;
    const keys={clientes:['nombre','telefono','correo','direccion','referencia'],productos:['sku','nombre','categoria','descripcion','ancho_cm','largo_cm','precio_actual','disponible','estado'],proveedores:['nombre','telefono','direccion','representante','rubro','disponibilidad'],reclamos:['numero','cliente','motivo','descripcion','estado'],envios:['numero','pedido','cliente','transporte','numero_guia','direccion','fecha_estimada','estado','incidencia']}[m.slug]||Object.keys(r);
    const image=m.slug==='productos'&&r.imagen_url?`<div class="detail-product-image">${format('imagen_url',r.imagen_url)}</div>`:'';
    let extras='';
    if(m.slug==='envios')extras=`<div class="tracking-steps">${['Preparado','En transito','Entregado'].map((state,i)=>`<span class="${['Preparado','En transito','Entregado'].indexOf(r.estado)>=i?'done':''}">${icon(i===2?'check':'envios')}${e(state)}</span>`).join('')}</div><div class="side-actions">${link('envios',3,'Registrar guía','button',`?registro=${r.id}`)}${link('envios',4,'Confirmar entrega','primary',`?registro=${r.id}`)}</div>`;
    if(m.slug==='clientes')extras=`<div class="detail-note"><span>Historial de compras</span><strong>${r.compras||0} ventas vigentes</strong></div>${link('clientes',4,'Consultar historial','button wide',`?cliente_id=${r.id}`)}`;
    if(m.slug==='proveedores')extras=`<div class="side-actions">${link('proveedores',3,'Registrar compra','primary',`?proveedor_id=${r.id}`)}${link('compras',2,'Consultar compras','button',`?proveedor_id=${r.id}`)}</div>`;
    return `<section class="panel side-detail"><div class="panel-heading"><h2>${e(cfg.side)}</h2>${icon(m.slug)}</div>${image}${miniFields(r,keys)}<div class="side-actions">${cfg.edit?link(m.slug,cfg.edit,'Editar datos','primary',`?registro=${r.id}`):''}${cfg.detail&&m.slug!=='clientes'?link(m.slug,cfg.detail,'Ver detalle','button',`?registro=${r.id}`):''}</div>${extras}</section>`;
  }
  function adminSide(data){return `<section class="panel"><div class="panel-heading"><h2>${icon('administracion')} Roles y permisos</h2></div><div class="role-list">${(data.roles||[]).map(r=>`<a href="#/administracion/2?rol_id=${r.id}"><span>${e(r.nombre)}</span><small>${r.operaciones} permisos</small>${icon('arrow')}</a>`).join('')||'<p class="quiet-empty">Sin acceso a la matriz de permisos.</p>'}</div></section><section class="panel"><div class="panel-heading"><h2>${icon('backup')} Copias de seguridad</h2></div><div class="backup-summary"><span>ÚLTIMO RESPALDO</span>${data.respaldo?`<strong>${e(data.respaldo.nombre)}</strong><small>${format('fecha',data.respaldo.fecha)}</small>${format('estado',data.respaldo.estado)}`:'<p>No hay respaldos registrados.</p>'}</div><div class="side-actions vertical">${link('administracion',3,'Generar backup','button')}${link('administracion',4,'Restaurar backup','button danger-soft')}</div></section>`;}
  function filterbar(records,m){return `<div class="panel-filters"><label class="search-control">${icon('search')}<input id="panel-search" type="search" placeholder="Buscar en ${e(panelConfig[m.slug].title.toLowerCase())}" aria-label="Buscar registros"></label><label><span class="sr-only">Estado</span><select id="panel-state"><option value="">Todos los estados</option>${[...new Set(records.map(r=>r.estado).filter(Boolean))].map(state=>`<option>${e(state)}</option>`).join('')}</select></label>${records.some(r=>r.fecha)?'<label class="date-filter"><span>Desde</span><input type="date" id="panel-from" aria-label="Desde"></label><label class="date-filter"><span>Hasta</span><input type="date" id="panel-to" aria-label="Hasta"></label>':''}</div>`;}
  function recordsTable(records,m){
    const cfg=panelConfig[m.slug];
    return table(records,{columns:cfg.columns,actions:r=>`<div class="row-actions">${cfg.side?`<button type="button" class="text-button" data-inspect="${r.id}" aria-label="Ver detalle del registro ${r.id}">Ver</button>`:''}${cfg.edit&&permitted(m.slug,cfg.edit)?link(m.slug,cfg.edit,'Editar','text-button',`?registro=${r.id}`):''}${cfg.detail&&permitted(m.slug,cfg.detail)?link(m.slug,cfg.detail,m.slug==='clientes'?'Historial':'Detalle','text-button',`?${cfg.detailKey||'registro'}=${r.id}`):''}</div>`});
  }
  function parentBody(m,data,quickHTML=''){
    const cfg=panelConfig[m.slug];
    let content='',side='';
    if(m.slug==='administracion')side=adminSide(data);
    else if(cfg.side)side=sideDetail(m,data.registros[0]);
    else if(m.slug==='inventario')side=alerts(data.alertas);
    else if(quickHTML)side=quickHTML;
    if(m.slug==='reportes')content+=`<div class="report-overview"><section class="panel"><div class="panel-heading"><h2>Resumen financiero</h2>${link('reportes',2,'Ver reporte','text-button')}</div>${miniFields(Object.fromEntries(data.indicadores.map((m,i)=>[['ventas_vigentes','cobros_verificados','saldos_pendientes','pagos_por_verificar'][i],m.valor])),['ventas_vigentes','cobros_verificados','saldos_pendientes','pagos_por_verificar'])}</section>${bestSellers(data.mas_vendidos)}</div>`;
    if(cfg.chart)content+=chart(data.serie,'Tendencia de ventas');
    if(m.slug==='envios')content+=`<section class="panel shipment-flow"><div class="panel-heading"><h2>Flujo de envío</h2></div><div class="tracking-steps">${data.estados.map(s=>`<span>${icon('envios')}<strong>${s.total}</strong>${e(s.label)}</span>`).join('')}</div></section>`;
    content+=`<section class="panel directory-panel"><div class="panel-heading"><h2>${m.slug==='administracion'?icon('clientes'):''}${e(cfg.title)}</h2>${m.slug==='administracion'?link(m.slug,1,'+ Nuevo usuario','primary', '?nuevo=1'):''}</div>${filterbar(data.registros,m)}<div id="panel-records">${recordsTable(data.registros,m)}</div></section>`;
    if(m.slug==='marketing')content=`<div class="report-overview">${content}<section class="panel"><div class="panel-heading"><h2>Consultas recientes</h2>${link('marketing',3,'Responder','text-button')}</div>${table(data.consultas,{columns:['contacto','canal','pregunta','estado','fecha']})}</section></div>`;
    return cards(data.indicadores)+`<div class="module-workspace ${side?'with-side':''}"><div class="module-primary">${content}</div>${side?`<aside class="module-side" id="panel-side">${side}</aside>`:''}</div>`;
  }
  function homeBody(data,modules){return cards(data.indicadores)+`<div class="dashboard-workspace"><div>${data.serie.length?chart(data.serie):`<section class="panel"><div class="panel-heading"><h2>Mi actividad</h2></div>${table(data.actividad,{columns:['modulo','operacion','fecha']})}</section>`}</div><aside>${data.serie.length?bestSellers(data.mas_vendidos):''}${alerts(data.alertas)}</aside></div>${data.pedidos.length||permitted('pedidos',2)?`<section class="panel"><div class="panel-heading"><h2>Pedidos recientes</h2>${link('pedidos',2,'Ver todos','text-button')}</div>${table(data.pedidos,{columns:['numero','cliente','canal','total','estado','fecha']})}</section>`:''}<details class="module-shortcuts"><summary>Todos los módulos <span>${modules.length}</span></summary><div class="module-grid">${modules.map(m=>`<a class="module-card" href="#/${m.slug}">${icon(m.slug)}<div><strong>${e(m.title)}</strong><small>${m.operaciones.length} operaciones</small></div></a>`).join('')}</div></details>`;}
  return {cards,chart,alerts,operations,parentBody,recordsTable,homeBody,sideDetail,link};
}
