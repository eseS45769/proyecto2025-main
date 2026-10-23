from backend.business import *
WRITES={1,2,3}
def handle(c,u,op,d):
    if op==3:
        return purchase(c,u,d)
    if op in (1,2):
        data=dict(nombre=text(d,'nombre',maximum=150),identificacion=text(d,'identificacion',False,30) or None,telefono=phone(d),direccion=text(d,'direccion',maximum=255),representante=text(d,'representante',False,120),rubro=text(d,'rubro',maximum=80),disponibilidad=text(d,'disponibilidad',False,120))
        if one(c,'SELECT id FROM proveedores WHERE lower(nombre)=lower(?) AND telefono=? AND id<>?',(data['nombre'],data['telefono'],d.get('id',0))):
            raise Error('Ya existe un proveedor con ese nombre y teléfono.',409)
        if op==1:
            ident=insert(c,'proveedores',data)
        else:
            ident=get(c,'proveedores',d.get('id'))['id']
            update(c,'proveedores',ident,data)
        audit(c,u,'proveedores','Registrar proveedor' if op==1 else 'Actualizar proveedor',ident)
        return get(c,'proveedores',ident)
    if d.get('id'):
        supplier=get(c,'proveedores',d['id'])
        supplier['compras']=rows(c,'SELECT * FROM compras WHERE proveedor_id=? ORDER BY id DESC',(supplier['id'],))
        return supplier
    result=rows(c,'SELECT * FROM proveedores ORDER BY id DESC')
    q=str(d.get('q') or '').casefold()
    return [r for r in result if q in (r['nombre']+' '+r['rubro']).casefold()]
