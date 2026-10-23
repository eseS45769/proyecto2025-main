from backend.business import *
WRITES=set()
def handle(c,u,op,d):
    if op==2:
        return financial(c,u,d)
    sales=filtered(c,u,'ventas',d)
    if d.get('producto_id'):
        pid=integer(d['producto_id'])
        sales=[v for v in sales if one(c,'SELECT id FROM detalles_venta WHERE venta_id=? AND producto_id=?',(v['id'],pid))]
    if op==1:
        for v in sales:
            b=balance(c,venta_id=v['id'])
            v['total']=b['total']
            v['saldo']=b['saldo']
        return dict(registros=sales,total_vigente=sum(v['total'] for v in sales if v['estado']=='Vigente'),total_anulado=sum(v['total'] for v in sales if v['estado']=='Anulada'))
    counts={}
    for v in sales:
        if v['estado']!='Vigente':
            continue
        if op==3:
            for l in rows(c,'SELECT d.*,p.nombre,p.sku,p.categoria_id FROM detalles_venta d JOIN productos p ON p.id=d.producto_id WHERE venta_id=?',(v['id'],)):
                if d.get('categoria_id') and l['categoria_id']!=integer(d['categoria_id']):
                    continue
                r=counts.setdefault(l['producto_id'],dict(producto_id=l['producto_id'],nombre=l['nombre'],sku=l['sku'],unidades=0,importe=0))
                r['unidades']+=l['cantidad']
                r['importe']+=l['cantidad']*l['precio_unitario']
        else:
            client=get(c,'clientes',v['cliente_id'])
            r=counts.setdefault(client['id'],dict(cliente_id=client['id'],nombre=client['nombre'],frecuencia=0,importe=0))
            r['frecuencia']+=1
            r['importe']+=balance(c,venta_id=v['id'])['total']
    return sorted(counts.values(),key=lambda r:r['unidades' if op==3 else 'frecuencia'],reverse=True)
