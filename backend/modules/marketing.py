from backend.business import *
WRITES={1,2,3}

def publish(c,u,d,channel):
    ids=d.get('productos')
    if not isinstance(ids,list) or not ids or len(ids)>100:
        raise Error('Seleccioná al menos un producto activo.')
    ids=list(dict.fromkeys(integer(p) for p in ids))
    for pid in ids:
        if get(c,'productos',pid)['estado']!='Activo':
            raise Error('El catálogo y las publicaciones solo admiten productos activos.')
    evidence=url(d,'enlace_externo')
    content=text(d,'contenido',maximum=2000)
    state='Publicada' if evidence and d.get('difusion_confirmada') is True else 'Preparada'
    if channel=='WhatsApp' and state=='Publicada' and not d.get('difusion_confirmada'):
        raise Error('Confirmá el envío real en WhatsApp.')
    pid=integer(d['publicacion_id']) if d.get('publicacion_id') else None
    data=dict(canal=channel,contenido=content,campania=text(d,'campania',False,120),material_url=url(d,'material_url'),enlace_externo=evidence,estado=state,fecha_publicacion=now() if state=='Publicada' else None)
    if pid:
        previous=get(c,'publicaciones',pid)
        if previous['canal']!=channel:
            raise Error('La publicación pertenece a otro canal.')
        update(c,'publicaciones',pid,data)
        c.execute('DELETE FROM publicaciones_productos WHERE publicacion_id=?',(pid,))
    else:
        pid=insert(c,'publicaciones',dict(**data,responsable_id=u['id'],fecha=now()))
    for product in ids:
        insert(c,'publicaciones_productos',dict(publicacion_id=pid,producto_id=product))
    metrics=d.get('metricas')
    if metrics:
        if state!='Publicada':
            raise Error('Registrá evidencia de publicación antes de cargar métricas.')
        measurement=text(metrics,'fecha_medicion',False) or now()
        try:
            datetime.fromisoformat(measurement)
        except ValueError:
            raise Error('La fecha de medición no es válida.')
        for indicator in ('vistas','likes','comentarios'):
            c.execute('''INSERT INTO metricas_publicacion(publicacion_id,indicador,valor,fuente,fecha_medicion) VALUES(?,?,?,?,?)
                ON CONFLICT(publicacion_id,indicador,fecha_medicion,fuente) DO UPDATE SET valor=excluded.valor''',
                (pid,indicator,integer(metrics.get(indicator,0),0),text(metrics,'fuente'),measurement))
    audit(c,u,'marketing','Preparar o confirmar publicación',pid,entity='publicaciones')
    result=get(c,'publicaciones',pid)
    result['productos']=[r for r in inventory(c) if r['id'] in ids]
    if channel=='WhatsApp':
        from urllib.parse import quote
        result['compartir_url']='https://wa.me/?text='+quote(content)
    return result

def handle(c,u,op,d):
    if op in (1,2):
        return publish(c,u,d,'TikTok' if op==1 else 'WhatsApp')
    if op==3:
        if d.get('consulta_id'):
            q=get(c,'consultas_marketing',d['consulta_id'])
            qid=q['id']
        else:
            qid=insert(c,'consultas_marketing',dict(cliente_id=integer(d['cliente_id']) if d.get('cliente_id') else None,publicacion_id=integer(d['publicacion_id']) if d.get('publicacion_id') else None,contacto=text(d,'contacto'),canal=choice(d,'canal',['TikTok','WhatsApp','Directo']),pregunta=text(d,'pregunta'),fecha=now()))
        response=text(d,'respuesta')
        evidence=text(d,'evidencia',False)
        sent=d.get('envio_confirmado') is True
        if sent and not evidence:
            raise Error('Registrá evidencia para confirmar que la respuesta fue enviada.')
        rid=insert(c,'respuestas_consulta',dict(consulta_id=qid,responsable_id=u['id'],respuesta=response,estado='Enviada' if sent else 'Preparada',evidencia=evidence,fecha=now(),fecha_envio=now() if sent else None))
        update(c,'consultas_marketing',qid,dict(estado='Respondida' if sent else 'Pendiente'))
        audit(c,u,'marketing','Responder consulta',qid,entity='consultas_marketing')
        return get(c,'respuestas_consulta',rid)
    period(d)
    records=rows(c,'SELECT m.*,p.canal,p.campania FROM metricas_publicacion m JOIN publicaciones p ON p.id=m.publicacion_id ORDER BY m.fecha_medicion DESC,m.id DESC')
    records=[r for r in records if (not d.get('desde') or r['fecha_medicion'][:10]>=d['desde']) and (not d.get('hasta') or r['fecha_medicion'][:10]<=d['hasta']) and (not d.get('canal') or r['canal']==d['canal']) and (not d.get('campania') or r['campania']==d['campania'])]
    # Un corte acumulado por publicación e indicador; no sumar cortes superpuestos ni fuentes duplicadas.
    latest={}
    for r in records:
        latest.setdefault((r['publicacion_id'],r['indicador']),r)
    return dict(registros=records,estado='Con datos' if records else 'Sin datos',**{indicator:sum(r['valor'] for r in latest.values() if r['indicador']==indicator) for indicator in ('vistas','likes','comentarios')},nota='Totales del último corte por publicación e indicador dentro del periodo; los cortes anteriores se conservan como evidencia.')
