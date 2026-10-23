from backend.business import *
WRITES={1,3}
def handle(c,u,op,d):
    if op in (1,3):
        data=dict(nombre=text(d,'nombre',maximum=120),telefono=phone(d),direccion=text(d,'direccion',maximum=255),referencia=text(d,'referencia',False,255),correo=text(d,'correo',False,254))
        if data['correo'] and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',data['correo']):
            raise Error('Ingresá un correo válido.')
        duplicate=one(c,'SELECT id FROM clientes WHERE lower(nombre)=lower(?) AND telefono=? AND id<>?',(data['nombre'],data['telefono'],d.get('id',0)))
        if duplicate:
            raise Error('Ya existe un cliente con ese nombre y teléfono. Consultá su ficha.',409)
        if op==1:
            ident=insert(c,'clientes',dict(**data,fecha_registro=now()))
        else:
            current=get(c,'clientes',d.get('id'))
            owner(c,u,current['id'])
            ident=current['id']
            update(c,'clientes',ident,data)
        audit(c,u,'clientes','Registrar cliente' if op==1 else 'Actualizar datos',ident)
        return get(c,'clientes',ident)
    if op==4:
        client=get(c,'clientes',d.get('cliente_id'))
        owner(c,u,client['id'])
        return dict(cliente=client,pedidos=filtered(c,u,'pedidos',{'cliente_id':client['id']}),ventas=filtered(c,u,'ventas',{'cliente_id':client['id']}),nota='Historial derivado de los documentos; se vincula automáticamente.')
    result=rows(c,'SELECT * FROM clientes ORDER BY id DESC')
    if get(c,'roles',u['rol_id'])['nombre']=='Cliente':
        result=[r for r in result if r['usuario_id']==u['id']]
    q=str(d.get('q') or '').casefold()
    return [r for r in result if q in (r['nombre']+' '+r['telefono']).casefold()]
