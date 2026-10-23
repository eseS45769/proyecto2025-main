"""Consultas de apoyo autorizadas. Nunca modifican documentos."""
from backend.business import *
from backend.modules.administracion import public_backup

def reference(c,u,kind):
    codes=permissions(c,u)
    def allowed(*slugs):
        if not any(code.split('.')[0] in slugs for code in codes):
            raise Error('No tenés acceso a estos registros.',403)
    if kind=='clientes':
        allowed('clientes','pedidos','ventas','pagos','reclamos','marketing','finanzas','reportes','administracion')
        if get(c,'roles',u['rol_id'])['nombre']=='Cliente':
            return rows(c,'SELECT id,nombre,direccion,referencia FROM clientes WHERE usuario_id=?',(u['id'],))
        return rows(c,'SELECT id,nombre,telefono,correo,direccion,referencia,usuario_id FROM clientes ORDER BY nombre')
    if kind=='productos':
        allowed('productos','inventario','pedidos','ventas','compras','proveedores','marketing','reportes')
        return inventory(c)
    if kind=='categorias':
        allowed('productos','reportes','inventario')
        return rows(c,"SELECT * FROM categorias WHERE estado='Activo'")
    if kind in ('pedidos','ventas','reclamos','compras'):
        maps={'pedidos':('pedidos','ventas','pagos','envios','reclamos'),'ventas':('ventas','pagos','finanzas','reportes','reclamos'),'reclamos':('reclamos',),'compras':('compras','proveedores')}
        allowed(*maps[kind])
        return filtered(c,u,kind,{})
    if kind=='pagos':
        allowed('pagos','finanzas')
        result=rows(c,'SELECT * FROM pagos ORDER BY id DESC')
        if get(c,'roles',u['rol_id'])['nombre']=='Cliente':
            client=one(c,'SELECT id FROM clientes WHERE usuario_id=?',(u['id'],))
            result=[p for p in result if get(c,'pedidos' if p['pedido_id'] else 'ventas',p['pedido_id'] or p['venta_id'])['cliente_id']==(client['id'] if client else -1)]
        return result
    if kind=='proveedores':
        allowed('proveedores','compras')
        return rows(c,'SELECT * FROM proveedores ORDER BY nombre')
    if kind=='envios':
        allowed('envios')
        return rows(c,'SELECT * FROM envios ORDER BY id DESC')
    if kind=='transportistas':
        allowed('envios')
        return rows(c,'SELECT * FROM transportistas ORDER BY nombre')
    if kind in ('publicaciones','consultas_marketing'):
        allowed('marketing','productos')
        return rows(c,f'SELECT * FROM {kind} ORDER BY id DESC')
    if kind in ('usuarios','roles','permisos','roles_permisos','respaldos','auditorias','restauraciones'):
        allowed('administracion')
        if kind=='usuarios':
            return rows(c,'SELECT u.id,u.nombre,u.usuario,u.rol_id,u.estado,u.ultimo_acceso,cl.id cliente_id FROM usuarios u LEFT JOIN clientes cl ON cl.usuario_id=u.id ORDER BY u.id DESC')
        if kind=='respaldos':
            return [public_backup(r) for r in rows(c,'SELECT * FROM respaldos ORDER BY id DESC')]
        return rows(c,f'SELECT * FROM {kind} ORDER BY id DESC')
    raise Error('Consulta no encontrada.',404)

def dashboard(c,u):
    codes=permissions(c,u)
    cards=[]
    if any(k.startswith('pedidos.') for k in codes):
        cards.append(dict(label='Pedidos activos',valor=len([r for r in filtered(c,u,'pedidos',{}) if r['estado'] not in ('Cancelado','Entregado')]),ruta='pedidos'))
    if 'inventario.1' in codes:
        cards.append(dict(label='Alfombras disponibles',valor=sum(r['disponible'] for r in inventory(c)),ruta='inventario'))
        cards.append(dict(label='Alertas de stock',valor=c.execute("SELECT COUNT(*) FROM alertas_stock WHERE estado='Activa'").fetchone()[0],ruta='inventario'))
    if 'finanzas.4' in codes:
        f=financial(c,u,{})
        cards.append(dict(label='Cobros verificados',valor=f['cobros_verificados'],moneda=True,ruta='finanzas'))
    if 'envios.1' in codes:
        cards.append(dict(label='Envíos en tránsito',valor=c.execute("SELECT COUNT(*) FROM envios WHERE estado='En transito'").fetchone()[0],ruta='envios'))
    return dict(indicadores=cards,actividad=rows(c,'SELECT modulo,operacion,fecha,detalle FROM auditorias WHERE usuario_id=? ORDER BY id DESC LIMIT 8',(u['id'],)))
