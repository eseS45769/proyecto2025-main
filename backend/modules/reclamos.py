from backend.business import *
WRITES={1,3,4}
def handle(c,u,op,d):
    if op==2:
        return filtered(c,u,'reclamos',d)
    if op==1:
        cid=integer(d.get('cliente_id'))
        owner(c,u,cid)
        oid=integer(d['pedido_id']) if d.get('pedido_id') else None
        vid=integer(d['venta_id']) if d.get('venta_id') else None
        if bool(oid)==bool(vid):
            raise Error('El reclamo debe asociarse a un pedido o a una venta.')
        doc=get(c,'pedidos' if oid else 'ventas',oid or vid)
        if doc['cliente_id']!=cid:
            raise Error('El documento no pertenece al cliente seleccionado.')
        rid=insert(c,'reclamos',dict(cliente_id=cid,pedido_id=oid,venta_id=vid,numero=number(c,'reclamos','RL'),motivo=text(d,'motivo',maximum=120),descripcion=text(d,'descripcion'),estado='Pendiente',fecha=now()))
        previous=None
        state='Pendiente'
        note=text(d,'descripcion')
    else:
        r=get(c,'reclamos',d.get('id'))
        owner(c,u,r['cliente_id'])
        rid=r['id']
        previous=r['estado']
        state='Cerrado' if op==4 else choice(d,'estado',['En revision','Solucionado'])
        if {'Pendiente':'En revision','En revision':'Solucionado','Solucionado':'Cerrado'}.get(previous)!=state:
            raise Error('Seguí la secuencia Pendiente → En revisión → Solucionado → Cerrado.')
        if op==4:
            confirm(d)
        note=text(d,'solucion' if op==4 else 'observacion')
        update(c,'reclamos',rid,dict(estado=state))
    insert(c,'historial_reclamos',dict(reclamo_id=rid,responsable_id=u['id'],estado_anterior=previous,estado_nuevo=state,observacion=note,fecha=now()))
    audit(c,u,'reclamos',f'Operación {op}',rid,note)
    return document(c,u,'reclamos',rid)
