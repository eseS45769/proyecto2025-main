"""Reglas compartidas de documentos, dinero y existencias; sin commits internos."""
from backend.core import *

def stock(c, pid):
    return one(c, '''SELECT e.*,COALESCE((SELECT SUM(r.cantidad) FROM reservas r
        JOIN detalles_pedido d ON d.id=r.detalle_pedido_id WHERE d.producto_id=e.producto_id AND r.estado='Vigente'),0) reservado
        FROM existencias e WHERE producto_id=?''', (pid,))

def inventory(c):
    return rows(c, '''SELECT p.*,cat.nombre categoria,e.stock_fisico,e.stock_minimo,
        COALESCE(r.reservado,0) reservado,e.stock_fisico-COALESCE(r.reservado,0) disponible
        FROM productos p JOIN categorias cat ON cat.id=p.categoria_id JOIN existencias e ON e.producto_id=p.id
        LEFT JOIN (SELECT d.producto_id,SUM(r.cantidad) reservado FROM reservas r JOIN detalles_pedido d ON d.id=r.detalle_pedido_id
        WHERE r.estado='Vigente' GROUP BY d.producto_id) r ON r.producto_id=p.id ORDER BY p.id DESC''')

def alert(c, pid):
    s = stock(c, pid)
    active = one(c, "SELECT id FROM alertas_stock WHERE producto_id=? AND estado='Activa'", (pid,))
    if s['stock_fisico'] - s['reservado'] <= s['stock_minimo']:
        if not active:
            insert(c, 'alertas_stock',dict(producto_id=pid,estado='Activa',fecha_apertura=now()))
    elif active:
        update(c, 'alertas_stock', active['id'], dict(estado='Resuelta',fecha_resolucion=now()))

def move(c, u, pid, delta, kind, source, source_id):
    s = stock(c, pid)
    physical = s['stock_fisico'] + delta
    if physical < s['reservado'] or physical < 0:
        raise Error('La operación dejaría el stock físico por debajo de las reservas vigentes.')
    update(c, 'existencias', s['id'],dict(stock_fisico=physical,version=s['version']+1))
    insert(c, 'movimientos_inventario',dict(producto_id=pid,responsable_id=u['id'],variacion=delta,saldo_resultante=physical,tipo=kind,fecha=now(),**{source:source_id}))
    alert(c, pid)

def adjustment(c, u, d, opening=False):
    pid = integer(d.get('producto_id'))
    get(c, 'productos', pid)
    try:
        delta = int(str(d.get('variacion')))
    except (ValueError, TypeError):
        raise Error('La variación debe ser un entero con signo.')
    if not delta:
        raise Error('La variación no puede ser cero.')
    aid = insert(c, 'ajustes_inventario',dict(producto_id=pid,responsable_id=u['id'],variacion=delta,motivo=text(d,'motivo'),evidencia_url=url(d,'evidencia_url'),fecha=now()))
    move(c, u, pid, delta, 'Apertura' if opening else 'Ajuste', 'ajuste_id', aid)
    audit(c,u,'inventario','Actualizar stock',aid,text(d,'motivo'))
    return get(c,'ajustes_inventario',aid)

def lines(c, d, cost=False, old=None):
    result = []
    seen = set()
    raw = d.get('lineas')
    if not isinstance(raw, list) or not raw or len(raw)>100:
        raise Error('Agregá entre una y cien líneas de productos.')
    for line in raw:
        if not isinstance(line, dict):
            raise Error('Línea de producto inválida.')
        pid = integer(line.get('producto_id'))
        p = get(c, 'productos',pid)
        if p['estado'] != 'Activo':
            raise Error(f'{p["nombre"]} está desactivado.')
        if pid in seen:
            raise Error('Cada producto debe aparecer una sola vez en el documento.')
        seen.add(pid)
        qty = integer(line.get('cantidad'))
        price = money(line.get('costo_unitario')) if cost else (old.get(pid,p['precio_actual']) if old else p['precio_actual'])
        if not cost and line.get('precio_unitario') is not None:
            price = money(line['precio_unitario'])
        result.append(dict(producto_id=pid,cantidad=qty,**{'costo_unitario' if cost else 'precio_unitario':price}))
    return result

def reserve(c, oid, order_lines):
    enough = all(stock(c,l['producto_id'])['stock_fisico']-stock(c,l['producto_id'])['reservado'] >= l['cantidad'] for l in order_lines)
    for line in order_lines:
        if enough:
            existing = one(c,'SELECT id FROM reservas WHERE detalle_pedido_id=?',(line['id'],))
            if existing:
                update(c,'reservas',existing['id'],dict(cantidad=line['cantidad'],estado='Vigente',fecha=now()))
            else:
                insert(c,'reservas',dict(detalle_pedido_id=line['id'],cantidad=line['cantidad'],estado='Vigente',fecha=now()))
        alert(c,line['producto_id'])
    update(c,'pedidos',oid,dict(estado='Reservado' if enough else 'Pendiente stock'))

def order_create(c,u,d):
    cid=integer(d.get('cliente_id'))
    client=get(c,'clientes',cid)
    owner(c,u,cid)
    ls=lines(c,d)
    oid=insert(c,'pedidos',dict(cliente_id=cid,creador_id=u['id'],numero=number(c,'pedidos','PD'),canal=choice(d,'canal',['TikTok','WhatsApp','Directo']),direccion_entrega=text(d,'direccion_entrega') or client['direccion'],referencia_entrega=text(d,'referencia_entrega',False),estado='Pendiente stock',fecha=now()))
    for l in ls:
        insert(c,'detalles_pedido',dict(pedido_id=oid,**l))
    reserve(c,oid,rows(c,'SELECT * FROM detalles_pedido WHERE pedido_id=?',(oid,)))
    audit(c,u,'pedidos','Registrar pedido',oid)
    return document(c,u,'pedidos',oid)

def order_update(c,u,d):
    oid=integer(d.get('id'))
    order=get(c,'pedidos',oid)
    owner(c,u,order['cliente_id'])
    if order['estado'] not in ('Reservado','Pendiente stock') or one(c,'SELECT id FROM ventas WHERE pedido_id=?',(oid,)):
        raise Error('Solo se puede editar antes de confirmar una venta o despachar.')
    old=rows(c,'SELECT * FROM detalles_pedido WHERE pedido_id=?',(oid,))
    ls=lines(c,d,old={l['producto_id']:l['precio_unitario'] for l in old})
    account=balance(c,pedido_id=oid)
    if sum(l['cantidad']*l['precio_unitario'] for l in ls) < account['verificado']+account['pendiente']:
        raise Error('El nuevo total no puede ser menor que los pagos vigentes y pendientes.')
    c.execute("UPDATE reservas SET estado='Liberada' WHERE detalle_pedido_id IN (SELECT id FROM detalles_pedido WHERE pedido_id=?)",(oid,))
    keep={l['producto_id'] for l in ls}
    for l in old:
        if l['producto_id'] not in keep:
            c.execute('DELETE FROM reservas WHERE detalle_pedido_id=?',(l['id'],))
            c.execute('DELETE FROM detalles_pedido WHERE id=?',(l['id'],))
    for l in ls:
        prev=next((x for x in old if x['producto_id']==l['producto_id']),None)
        if prev:
            update(c,'detalles_pedido',prev['id'],l)
        else:
            insert(c,'detalles_pedido',dict(pedido_id=oid,**l))
    update(c,'pedidos',oid,dict(direccion_entrega=text(d,'direccion_entrega'),referencia_entrega=text(d,'referencia_entrega',False)))
    reserve(c,oid,rows(c,'SELECT * FROM detalles_pedido WHERE pedido_id=?',(oid,)))
    for l in old:
        alert(c,l['producto_id'])
    audit(c,u,'pedidos','Actualizar pedido',oid)
    return document(c,u,'pedidos',oid)

def order_cancel(c,u,d):
    confirm(d)
    o=get(c,'pedidos',d.get('id'))
    owner(c,u,o['cliente_id'])
    if o['estado']=='Cancelado':
        return o
    if o['estado']=='Entregado' or one(c,"SELECT id FROM envios WHERE pedido_id=? AND estado IN ('En transito','Entregado')",(o['id'],)):
        raise Error('El pedido ya fue despachado.')
    if one(c,"SELECT id FROM ventas WHERE pedido_id=? AND estado='Vigente'",(o['id'],)) or one(c,"SELECT id FROM pagos WHERE pedido_id=? AND estado IN ('Verificado','Pendiente verificacion')",(o['id'],)):
        raise Error('Primero resolvé los pagos y la venta vigente mediante su anulación autorizada.')
    update(c,'pedidos',o['id'],dict(estado='Cancelado',motivo_cancelacion=text(d,'motivo')))
    c.execute("UPDATE reservas SET estado='Liberada' WHERE detalle_pedido_id IN (SELECT id FROM detalles_pedido WHERE pedido_id=?)",(o['id'],))
    c.execute("UPDATE envios SET estado='Cancelado' WHERE pedido_id=? AND estado='Preparado'",(o['id'],))
    for l in rows(c,'SELECT producto_id FROM detalles_pedido WHERE pedido_id=?',(o['id'],)):
        alert(c,l['producto_id'])
    audit(c,u,'pedidos','Cancelar pedido',o['id'],text(d,'motivo'))
    return get(c,'pedidos',o['id'])

def purchase(c,u,d):
    supplier=get(c,'proveedores',d.get('proveedor_id'))
    if supplier['estado']!='Activo':
        raise Error('El proveedor no está activo.')
    ref=text(d,'referencia',maximum=60).upper()
    if one(c,'SELECT id FROM compras WHERE proveedor_id=? AND referencia=?',(supplier['id'],ref)):
        raise Error('Ese documento del proveedor ya fue recibido. No se repite la entrada.',409)
    ls=lines(c,d,cost=True)
    date=text(d,'fecha',False) or now()
    try:
        datetime.fromisoformat(date)
    except ValueError:
        raise Error('La fecha de recepción no es válida.')
    ident=insert(c,'compras',dict(proveedor_id=supplier['id'],responsable_id=u['id'],referencia=ref,fecha=date,estado='Recibida',observacion=text(d,'observacion',False)))
    for l in ls:
        lid=insert(c,'detalles_compra',dict(compra_id=ident,**l))
        move(c,u,l['producto_id'],l['cantidad'],'Compra','detalle_compra_id',lid)
    audit(c,u,'compras','Registrar compra',ident)
    return document(c,u,'compras',ident)

def sale(c,u,d):
    oid=integer(d['pedido_id']) if d.get('pedido_id') else None
    if oid:
        o=get(c,'pedidos',oid)
        owner(c,u,o['cliente_id'])
        if one(c,'SELECT id FROM ventas WHERE pedido_id=?',(oid,)):
            raise Error('El pedido ya tiene una venta registrada.',409)
        if o['estado'] not in ('Reservado','Pendiente stock'):
            raise Error('El pedido no está disponible para confirmar venta.')
        cid=o['cliente_id']
        ls=rows(c,'SELECT producto_id,cantidad,precio_unitario FROM detalles_pedido WHERE pedido_id=?',(oid,))
        if o['estado']=='Reservado':
            c.execute("UPDATE reservas SET estado='Consumida' WHERE detalle_pedido_id IN (SELECT id FROM detalles_pedido WHERE pedido_id=?) AND estado='Vigente'",(oid,))
    else:
        cid=integer(d.get('cliente_id'))
        get(c,'clientes',cid)
        owner(c,u,cid)
        ls=lines(c,d)
    for l in ls:
        p=get(c,'productos',l['producto_id'])
        if p['estado']!='Activo':
            raise Error('No se puede vender un producto desactivado.')
        s=stock(c,l['producto_id'])
        if s['stock_fisico']-s['reservado']<l['cantidad']:
            raise Error(f'Stock disponible insuficiente para {p["nombre"]}.')
    vid=insert(c,'ventas',dict(cliente_id=cid,pedido_id=oid,responsable_id=u['id'],numero=number(c,'ventas','VT'),fecha=now(),estado='Vigente'))
    for l in ls:
        lid=insert(c,'detalles_venta',dict(venta_id=vid,**l))
        move(c,u,l['producto_id'],-l['cantidad'],'Venta','detalle_venta_id',lid)
    if oid:
        update(c,'pedidos',oid,dict(estado='Confirmado'))
    audit(c,u,'ventas','Registrar venta',vid)
    return document(c,u,'ventas',vid)

def account_ids(c,pedido_id=None,venta_id=None):
    if venta_id:
        v=get(c,'ventas',venta_id)
        return v['pedido_id'],v['id']
    v=one(c,'SELECT id FROM ventas WHERE pedido_id=?',(pedido_id,))
    return pedido_id,v['id'] if v else None

def balance(c,pedido_id=None,venta_id=None):
    oid,vid=account_ids(c,pedido_id,venta_id)
    if vid:
        ls=rows(c,'SELECT cantidad,precio_unitario FROM detalles_venta WHERE venta_id=?',(vid,))
    else:
        ls=rows(c,'SELECT cantidad,precio_unitario FROM detalles_pedido WHERE pedido_id=?',(oid,))
    ps=rows(c,'SELECT * FROM pagos WHERE pedido_id=? OR venta_id=?',(oid,vid))
    total=sum(l['cantidad']*l['precio_unitario'] for l in ls)
    verified=sum(p['monto'] for p in ps if p['estado']=='Verificado')
    pending=sum(p['monto'] for p in ps if p['estado']=='Pendiente verificacion')
    return dict(total=total,verificado=verified,pendiente=pending,saldo=total-verified,pagos=ps)

def payment(c,u,d):
    oid=integer(d['pedido_id']) if d.get('pedido_id') else None
    vid=integer(d['venta_id']) if d.get('venta_id') else None
    if bool(oid)==bool(vid):
        raise Error('Seleccioná un pedido o una venta, nunca ambos.')
    doc=get(c,'pedidos' if oid else 'ventas',oid or vid)
    owner(c,u,doc['cliente_id'])
    if doc['estado'] in ('Cancelado','Anulada'):
        raise Error('El documento está cancelado o anulado.')
    amount=money(d.get('monto'))
    b=balance(c,oid,vid)
    if amount>b['saldo']-b['pendiente']:
        raise Error('El monto supera el saldo disponible descontando pagos pendientes.')
    pid=insert(c,'pagos',dict(pedido_id=oid,venta_id=vid,registrador_id=u['id'],monto=amount,metodo=choice(d,'metodo',['Efectivo','Transferencia','QR']),referencia=text(d,'referencia',maximum=80).upper(),evidencia_url=url(d,'evidencia_url'),estado='Pendiente verificacion',fecha=now()))
    audit(c,u,'pagos','Registrar pago',pid)
    return get(c,'pagos',pid)

def recognize(c,u,p):
    if p['estado']!='Verificado':
        raise Error('El ingreso requiere un pago verificado.')
    current=one(c,'SELECT * FROM ingresos WHERE pago_id=?',(p['id'],))
    if current:
        return current
    ident=insert(c,'ingresos',dict(pago_id=p['id'],responsable_id=u['id'],fecha_registro=now(),estado='Vigente'))
    return get(c,'ingresos',ident)

def verify_payment(c,u,d):
    p=get(c,'pagos',d.get('id'))
    if p['estado']=='Verificado':
        return p
    if p['estado']!='Pendiente verificacion':
        raise Error('Solo se puede verificar un pago pendiente.')
    result=choice(d,'resultado',['Verificado','Rechazado'])
    evidence=text(d,'evidencia',maximum=500)
    b=balance(c,p['pedido_id'],p['venta_id'])
    if result=='Verificado' and p['monto']>b['saldo']:
        raise Error('El pago supera el saldo actual.')
    update(c,'pagos',p['id'],dict(estado=result,verificador_id=u['id'],fecha_verificacion=now(),motivo=evidence))
    if result=='Verificado':
        recognize(c,u,get(c,'pagos',p['id']))
    audit(c,u,'pagos','Verificar pago',p['id'],evidence)
    return get(c,'pagos',p['id'])

def void_payment(c,u,d):
    confirm(d)
    p=get(c,'pagos',d.get('id'))
    if p['estado']=='Anulado':
        return p
    reason=text(d,'motivo')
    update(c,'pagos',p['id'],dict(estado='Anulado',motivo=reason))
    c.execute("UPDATE ingresos SET estado='Anulado' WHERE pago_id=?",(p['id'],))
    audit(c,u,'pagos','Anular pago',p['id'],reason)
    return get(c,'pagos',p['id'])

def receipt(c,u,d):
    p=get(c,'pagos',d.get('id'))
    doc=get(c,'pedidos' if p['pedido_id'] else 'ventas',p['pedido_id'] or p['venta_id'])
    owner(c,u,doc['cliente_id'])
    if p['estado']!='Verificado':
        raise Error('Solo se puede emitir recibo de un pago verificado.')
    r=one(c,'SELECT * FROM comprobantes_pago WHERE pago_id=?',(p['id'],))
    if not r:
        ident=insert(c,'comprobantes_pago',dict(pago_id=p['id'],numero=number(c,'comprobantes_pago','RC'),fecha_emision=now(),archivo_url=f'/api/comprobante/{p["id"]}'))
        r=get(c,'comprobantes_pago',ident)
        audit(c,u,'pagos','Generar comprobante',ident,entity='comprobantes_pago')
    return dict(**r,monto=p['monto'],metodo=p['metodo'],cliente=get(c,'clientes',doc['cliente_id'])['nombre'],tipo='Comprobante interno. No es factura fiscal.')

def void_sale(c,u,d):
    confirm(d)
    v=get(c,'ventas',d.get('id'))
    if v['estado']=='Anulada':
        return v
    b=balance(c,venta_id=v['id'])
    if any(p['estado'] in ('Verificado','Pendiente verificacion') for p in b['pagos']):
        raise Error('Primero anulá o resolvé todos los pagos vigentes y pendientes.')
    delivery=one(c,"SELECT * FROM envios WHERE pedido_id=? AND estado IN ('En transito','Entregado')",(v['pedido_id'],))
    if delivery and delivery['estado']=='En transito':
        raise Error('Existe un despacho en tránsito pendiente de resolución.')
    if delivery and not d.get('devolucion_recibida'):
        raise Error('Confirmá la devolución física de las unidades entregadas.')
    evidence=text(d,'evidencia_devolucion',maximum=500)
    reason=text(d,'motivo')
    for l in rows(c,'SELECT * FROM detalles_venta WHERE venta_id=?',(v['id'],)):
        move(c,u,l['producto_id'],l['cantidad'],'Reversion venta','detalle_venta_id',l['id'])
    update(c,'ventas',v['id'],dict(estado='Anulada',motivo_anulacion=reason,evidencia_devolucion=evidence))
    if v['pedido_id']:
        update(c,'pedidos',v['pedido_id'],dict(estado='Cancelado',motivo_cancelacion=reason))
        c.execute("UPDATE envios SET estado='Cancelado' WHERE pedido_id=? AND estado='Preparado'",(v['pedido_id'],))
    audit(c,u,'ventas','Anular venta',v['id'],reason)
    return get(c,'ventas',v['id'])

def document(c,u,table,ident):
    doc=get(c,table,ident)
    if 'cliente_id' in doc:
        owner(c,u,doc['cliente_id'])
    if table in ('pedidos','ventas','compras'):
        detail,foreign={'pedidos':('detalles_pedido','pedido_id'),'ventas':('detalles_venta','venta_id'),'compras':('detalles_compra','compra_id')}[table]
        doc['lineas']=rows(c,f'SELECT d.*,p.sku,p.nombre FROM {detail} d JOIN productos p ON p.id=d.producto_id WHERE d.{foreign}=?',(doc['id'],))
        if table!='compras':
            doc['cuenta']=balance(c,pedido_id=doc['id'] if table=='pedidos' else None,venta_id=doc['id'] if table=='ventas' else None)
            doc['envios']=rows(c,'SELECT * FROM envios WHERE pedido_id=?',(doc['id'] if table=='pedidos' else doc['pedido_id'],))
        else:
            doc['movimientos']=rows(c,'SELECT m.* FROM movimientos_inventario m JOIN detalles_compra d ON d.id=m.detalle_compra_id WHERE d.compra_id=?',(doc['id'],))
            doc['total']=sum(l['cantidad']*l['costo_unitario'] for l in doc['lineas'])
    if table=='reclamos':
        doc['historial']=rows(c,'SELECT h.*,u.nombre responsable FROM historial_reclamos h JOIN usuarios u ON u.id=h.responsable_id WHERE reclamo_id=? ORDER BY h.id',(doc['id'],))
    if table=='envios':
        p=get(c,'pedidos',doc['pedido_id'])
        owner(c,u,p['cliente_id'])
        doc['asignaciones']=rows(c,'SELECT a.*,t.nombre transporte FROM asignaciones_transporte a JOIN transportistas t ON t.id=a.transportista_id WHERE envio_id=? ORDER BY a.id',(doc['id'],))
    return doc

def filtered(c,u,table,d):
    sql=f'SELECT * FROM {table}'
    conditions=[]
    args=[]
    role=get(c,'roles',u['rol_id'])['nombre']
    if role=='Cliente' and table in ('pedidos','ventas','reclamos'):
        client=one(c,'SELECT id FROM clientes WHERE usuario_id=?',(u['id'],))
        conditions.append('cliente_id=?')
        args.append(client['id'] if client else -1)
    if d.get('id'):
        return [document(c,u,table,d['id'])]
    for key in ('estado','cliente_id','proveedor_id'):
        if d.get(key):
            conditions.append(f'{key}=?')
            args.append(d[key])
    if d.get('desde') or d.get('hasta'):
        period(d)
        if d.get('desde'):
            conditions.append('substr(fecha,1,10)>=?')
            args.append(d['desde'])
        if d.get('hasta'):
            conditions.append('substr(fecha,1,10)<=?')
            args.append(d['hasta'])
    if conditions:
        sql+=' WHERE '+' AND '.join(conditions)
    result=rows(c,sql+' ORDER BY id DESC',args)
    q=str(d.get('q') or '').casefold()
    if q:
        result=[r for r in result if q in ' '.join(str(v) for v in r.values()).casefold()]
    return result

def period(d):
    try:
        for k in ('desde','hasta'):
            if d.get(k):
                datetime.strptime(d[k],'%Y-%m-%d')
        if d.get('desde') and d.get('hasta') and d['desde']>d['hasta']:
            raise ValueError()
    except (ValueError,TypeError):
        raise Error('El periodo de fechas es inválido.')

def financial(c,u,d):
    period(d)
    sales=filtered(c,u,'ventas',d)
    active=[v for v in sales if v['estado']=='Vigente']
    accounts=[]
    for v in active:
        b=balance(c,venta_id=v['id'])
        accounts.append(dict(venta_id=v['id'],pedido_id=v['pedido_id'],numero=v['numero'],cliente=get(c,'clientes',v['cliente_id'])['nombre'],total=b['total'],verificado=b['verificado'],pendiente=b['pendiente'],saldo=b['saldo']))
    sales_total=sum(a['total'] for a in accounts)
    order_filters={k:v for k,v in d.items() if k!='estado'}
    for order in filtered(c,u,'pedidos',order_filters):
        if order['estado'] in ('Cancelado','Entregado') or one(c,'SELECT id FROM ventas WHERE pedido_id=?',(order['id'],)):
            continue
        b=balance(c,pedido_id=order['id'])
        accounts.append(dict(venta_id=None,pedido_id=order['id'],numero=order['numero'],cliente=get(c,'clientes',order['cliente_id'])['nombre'],total=b['total'],verificado=b['verificado'],pendiente=b['pendiente'],saldo=b['saldo']))
    income=rows(c,'''SELECT i.id,p.id pago_id,i.estado,i.fecha_registro fecha,p.monto,p.metodo,p.referencia
        FROM ingresos i JOIN pagos p ON p.id=i.pago_id WHERE i.estado='Vigente' AND p.estado='Verificado' ORDER BY i.id DESC''')
    if d.get('desde'):
        income=[r for r in income if r['fecha'][:10]>=d['desde']]
    if d.get('hasta'):
        income=[r for r in income if r['fecha'][:10]<=d['hasta']]
    if d.get('metodo'):
        income=[r for r in income if r['metodo']==d['metodo']]
    if d.get('cliente_id'):
        selected=integer(d['cliente_id'])
        def client_of_income(r):
            p=get(c,'pagos',r['pago_id'])
            doc=get(c,'pedidos' if p['pedido_id'] else 'ventas',p['pedido_id'] or p['venta_id'])
            return doc['cliente_id']
        income=[r for r in income if client_of_income(r)==selected]
    return dict(ventas_vigentes=sales_total,cobros_verificados=sum(r['monto'] for r in income),saldos_pendientes=sum(a['saldo'] for a in accounts),pagos_por_verificar=sum(a['pendiente'] for a in accounts),cuentas=accounts,ingresos=income,nota='Ventas, cobros y saldos tienen fuentes diferentes. Los pedidos sin venta se muestran una sola vez en cuentas. No representan utilidad.')
