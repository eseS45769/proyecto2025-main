from backend.business import *
WRITES={1,2,3,4}

def eligible(c,e):
    o=get(c,'pedidos',e['pedido_id'])
    v=one(c,"SELECT * FROM ventas WHERE pedido_id=? AND estado='Vigente'",(o['id'],))
    if o['estado']!='Confirmado' or not v or balance(c,venta_id=v['id'])['saldo']!=0:
        raise Error('El envío exige pedido confirmado, venta vigente y saldo cero por pagos verificados.')

def handle(c,u,op,d):
    if op==1:
        o=get(c,'pedidos',d.get('pedido_id'))
        owner(c,u,o['cliente_id'])
        eligible(c,dict(pedido_id=o['id']))
        ident=insert(c,'envios',dict(pedido_id=o['id'],responsable_id=u['id'],numero=number(c,'envios','EN'),direccion=text(d,'direccion'),referencia=text(d,'referencia',False),costo=money(d.get('costo',0),False),fecha_estimada=text(d,'fecha_estimada',False),estado='Preparado'))
    else:
        e=get(c,'envios',d.get('id'))
        ident=e['id']
        if op==2:
            if e['estado']!='Preparado':
                raise Error('Solo se asigna transporte antes del despacho.')
            if d.get('nuevo_transportista'):
                t=d['nuevo_transportista']
                tid=insert(c,'transportistas',dict(nombre=text(t,'nombre',maximum=150),telefono=phone(t)))
            else:
                tid=integer(d.get('transportista_id'))
            carrier=get(c,'transportistas',tid)
            if carrier['estado']!='Disponible':
                raise Error('El transporte no está disponible.')
            c.execute('UPDATE asignaciones_transporte SET fecha_fin=? WHERE envio_id=? AND fecha_fin IS NULL',(now(),ident))
            insert(c,'asignaciones_transporte',dict(envio_id=ident,transportista_id=tid,responsable_id=u['id'],fecha=now()))
        elif op==3:
            if e['estado']!='Preparado':
                raise Error('El envío ya fue despachado o cerrado.')
            eligible(c,e)
            assign=one(c,'SELECT * FROM asignaciones_transporte WHERE envio_id=? AND fecha_fin IS NULL',(ident,))
            if not assign:
                raise Error('Primero asigná transporte.')
            guide=text(d,'numero_guia',maximum=80).upper()
            duplicate=one(c,'SELECT e.id FROM envios e JOIN asignaciones_transporte a ON a.envio_id=e.id WHERE e.numero_guia=? AND a.transportista_id=? AND a.fecha_fin IS NULL',(guide,assign['transportista_id']))
            if duplicate:
                raise Error('La guía ya existe para esa empresa de transporte.',409)
            confirm(d)
            update(c,'envios',ident,dict(numero_guia=guide,fecha_despacho=now(),estado='En transito'))
        elif op==4:
            if e['estado']!='En transito':
                raise Error('Solo se confirma entrega de un envío en tránsito.')
            if d.get('incidencia'):
                update(c,'envios',ident,dict(incidencia=text(d,'incidencia')))
            else:
                confirm(d)
                update(c,'envios',ident,dict(estado='Entregado',fecha_entrega=now(),receptor=text(d,'receptor',maximum=120),evidencia_entrega=text(d,'evidencia_entrega',maximum=500),incidencia=''))
                update(c,'pedidos',e['pedido_id'],dict(estado='Entregado'))
    audit(c,u,'envios',f'Operación {op}',ident)
    return document(c,u,'envios',ident)
