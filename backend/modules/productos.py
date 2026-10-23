from backend.business import *
WRITES={1,2,3,4}
def handle(c,u,op,d):
    if op in (1,2):
        cat=get(c,'categorias',d.get('categoria_id'))
        if cat['estado']!='Activo':
            raise Error('La categoría no está activa.')
        dimensions={}
        for key in ('ancho_cm','largo_cm'):
            value=money(d.get(key))
            dimensions[key]=str(Decimal(value)/100)
        data=dict(categoria_id=cat['id'],sku=text(d,'sku',maximum=30).upper(),nombre=text(d,'nombre',maximum=120),descripcion=text(d,'descripcion',maximum=500),precio_actual=money(d.get('precio_actual')),imagen_url=url(d,'imagen_url'),**dimensions)
        if op==1:
            ident=insert(c,'productos',data)
            insert(c,'existencias',dict(producto_id=ident,stock_fisico=0,stock_minimo=integer(d.get('stock_minimo',2),0)))
            opening=integer(d.get('stock_inicial') or 0,0)
            if opening:
                authorize(c,u,'inventario.2')
                adjustment(c,u,dict(producto_id=ident,variacion=opening,motivo=text(d,'motivo_apertura')),opening=True)
            alert(c,ident)
        else:
            ident=get(c,'productos',d.get('id'))['id']
            update(c,'productos',ident,data)
            s=stock(c,ident)
            if 'stock_minimo' in d:
                update(c,'existencias',s['id'],dict(stock_minimo=integer(d['stock_minimo'],0)))
                alert(c,ident)
        audit(c,u,'productos','Registrar producto' if op==1 else 'Actualizar producto',ident)
        return get(c,'productos',ident)
    if op==3:
        confirm(d)
        p=get(c,'productos',d.get('id'))
        update(c,'productos',p['id'],dict(estado='Inactivo'))
        audit(c,u,'productos','Desactivar producto',p['id'],text(d,'motivo'))
        return get(c,'productos',p['id'])
    from backend.modules.marketing import publish
    return publish(c,u,d,'Catalogo')
