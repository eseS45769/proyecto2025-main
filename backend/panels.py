"""Modelos de lectura para las interfaces P: indicadores y documentos reales."""
from backend.business import *
from backend.catalog import MODULES
from backend.queries import reference


def metric(label, value, money=False, tone='neutral'):
    return dict(label=label, valor=value, moneda=money, tono=tone)


def sales_series(c, u, days=7):
    today=datetime.fromisoformat(now()).date()
    dates=[(today-timedelta(days=offset)).isoformat() for offset in range(days-1,-1,-1)]
    totals={date:0 for date in dates}
    for v in filtered(c,u,'ventas',dict(desde=dates[0],hasta=dates[-1],estado='Vigente')):
        totals[v['fecha'][:10]]+=balance(c,venta_id=v['id'])['total']
    return [dict(fecha=date,valor=totals[date]) for date in dates]


def commercial_rows(c,u,kind):
    records=filtered(c,u,kind,{})
    for r in records:
        r['cliente']=get(c,'clientes',r['cliente_id'])['nombre']
        b=balance(c,pedido_id=r['id'] if kind=='pedidos' else None,venta_id=r['id'] if kind=='ventas' else None)
        r.update(total=b['total'],saldo=b['saldo'])
    return records


def home(c,u):
    codes=permissions(c,u)
    out=dict(indicadores=[],serie=[],mas_vendidos=[],alertas=[],pedidos=[],actividad=[])
    if 'ventas.3' in codes or 'reportes.1' in codes:
        serie=sales_series(c,u)
        out['serie']=serie
        out['indicadores'].append(metric('Ventas del día',serie[-1]['valor'],True,'sand'))
        from backend.modules.reportes import handle
        out['mas_vendidos']=handle(c,u,3,{})[:4]
    if any(k.startswith('pedidos.') for k in codes):
        orders=commercial_rows(c,u,'pedidos')
        out['pedidos']=orders[:6]
        out['indicadores'].append(metric('Pedidos pendientes',sum(r['estado'] in ('Reservado','Pendiente stock') for r in orders),tone='sage'))
    if 'inventario.1' in codes:
        low=[r for r in inventory(c) if r['disponible']<=r['stock_minimo']]
        out['indicadores'].append(metric('Stock bajo',len(low),tone='sand'))
        out['alertas']=[dict(titulo='Stock bajo · '+p['sku'],detalle=p['nombre']+f' · {p["disponible"]} disponibles',ruta='inventario/3',tono='sand') for p in low[:3]]
    if 'pagos.2' in codes:
        pending=rows(c,"SELECT monto FROM pagos WHERE estado='Pendiente verificacion'")
        out['indicadores'].append(metric('Pagos pendientes',sum(p['monto'] for p in pending),True,'rose'))
        if pending:
            out['alertas'].append(dict(titulo='Pagos por verificar',detalle=f'{len(pending)} registros esperan confirmación',ruta='pagos/2',tono='rose'))
    if 'envios.1' in codes and len(out['indicadores'])<4:
        out['indicadores'].append(metric('Envíos en tránsito',c.execute("SELECT COUNT(*) FROM envios WHERE estado='En transito'").fetchone()[0],tone='sage'))
    out['actividad']=rows(c,'SELECT modulo,operacion,fecha FROM auditorias WHERE usuario_id=? ORDER BY id DESC LIMIT 5',(u['id'],))
    return out


def panel(c,u,slug):
    codes=permissions(c,u)
    if not any(code.startswith(slug+'.') for code in codes) or slug not in {m['slug'] for m in MODULES}:
        raise Error('Tu rol no tiene acceso a este módulo.',403)
    out=dict(indicadores=[],registros=[],laterales=[],serie=[],estados=[])
    if slug=='administracion':
        if 'administracion.1' in codes:
            out['registros']=rows(c,'''SELECT u.id,u.usuario,u.nombre,r.nombre rol,u.estado,u.ultimo_acceso,
                cl.id cliente_id FROM usuarios u JOIN roles r ON r.id=u.rol_id LEFT JOIN clientes cl ON cl.usuario_id=u.id ORDER BY u.id DESC''')
        if 'administracion.2' in codes:
            out['roles']=rows(c,'SELECT r.id,r.nombre,COUNT(rp.id) operaciones FROM roles r LEFT JOIN roles_permisos rp ON rp.rol_id=r.id GROUP BY r.id')
        if 'administracion.3' in codes or 'administracion.4' in codes:
            out['respaldo']=one(c,'SELECT id,nombre,estado,fecha FROM respaldos ORDER BY id DESC LIMIT 1')
    elif slug in ('pedidos','ventas'):
        rs=commercial_rows(c,u,slug)
        out['registros']=rs
        if slug=='pedidos':
            counts=[('Nuevos',sum(r['fecha'][:10]==now()[:10] for r in rs)),('Pendientes',sum(r['estado'] in ('Reservado','Pendiente stock') for r in rs)),('En preparación',c.execute("SELECT COUNT(*) FROM envios WHERE estado='Preparado' AND pedido_id IN (SELECT id FROM pedidos WHERE estado='Confirmado')").fetchone()[0]),('Entregados',sum(r['estado']=='Entregado' for r in rs)),('Total de pedidos',len(rs))]
            if get(c,'roles',u['rol_id'])['nombre']=='Cliente':
                counts[2]=('Confirmados',sum(r['estado']=='Confirmado' for r in rs))
            out['indicadores']=[metric(k,v,tone='sage' if i==3 else 'neutral') for i,(k,v) in enumerate(counts)]
        else:
            out['serie']=sales_series(c,u)
            today=datetime.fromisoformat(now()).date()
            active=[v for v in rs if v['estado']=='Vigente']
            out['indicadores']=[metric('Ventas del día',sum(v['total'] for v in active if v['fecha'][:10]==today.isoformat()),True,'sand'),metric('Últimos 7 días',sum(v['total'] for v in active if v['fecha'][:10]>=(today-timedelta(days=6)).isoformat()),True,'sage'),metric('Ventas del mes',sum(v['total'] for v in active if v['fecha'][:7]==today.isoformat()[:7]),True)]
    elif slug=='pagos':
        rs=reference(c,u,'pagos')
        out['registros']=rs
        out['indicadores']=[metric('Pagos recibidos',sum(r['monto'] for r in rs if r['estado']=='Verificado'),True,'sand'),metric('Pendientes',sum(r['estado']=='Pendiente verificacion' for r in rs),tone='sand'),metric('Completados',sum(r['estado']=='Verificado' for r in rs),tone='sage'),metric('Anulados',sum(r['estado']=='Anulado' for r in rs),tone='rose')]
    elif slug=='inventario':
        rs=inventory(c)
        out['registros']=rs
        low=[r for r in rs if r['disponible']<=r['stock_minimo']]
        out['indicadores']=[metric('Stock físico',sum(r['stock_fisico'] for r in rs)),metric('Disponible',sum(r['disponible'] for r in rs),tone='sage'),metric('Reservado',sum(r['reservado'] for r in rs),tone='sand'),metric('Alertas activas',len(low),tone='rose')]
        out['alertas']=[dict(titulo=r['sku'],detalle=r['nombre']+f' · {r["disponible"]} disponibles',ruta='inventario/3',tono='sand') for r in low[:6]]
    elif slug=='productos':
        out['registros']=inventory(c)
    elif slug=='clientes':
        out['registros']=rows(c,'SELECT * FROM clientes ORDER BY fecha_registro DESC')
        if get(c,'roles',u['rol_id'])['nombre']=='Cliente':
            out['registros']=[r for r in out['registros'] if r['usuario_id']==u['id']]
        for r in out['registros']:
            r['compras']=c.execute("SELECT COUNT(*) FROM ventas WHERE cliente_id=? AND estado='Vigente'",(r['id'],)).fetchone()[0]
    elif slug=='proveedores':
        out['registros']=rows(c,'SELECT * FROM proveedores ORDER BY nombre')
    elif slug=='compras':
        out['registros']=rows(c,'SELECT c.*,p.nombre proveedor FROM compras c JOIN proveedores p ON p.id=c.proveedor_id ORDER BY c.id DESC')
        for r in out['registros']:
            r['total']=c.execute('SELECT COALESCE(SUM(cantidad*costo_unitario),0) FROM detalles_compra WHERE compra_id=?',(r['id'],)).fetchone()[0]
        out['indicadores']=[metric('Recepciones',len(out['registros'])),metric('Mercadería recibida',sum(r['total'] for r in out['registros']),True,'sand')]
    elif slug=='reclamos':
        out['registros']=filtered(c,u,'reclamos',{})
        for r in out['registros']:
            r['cliente']=get(c,'clientes',r['cliente_id'])['nombre']
    elif slug=='envios':
        rs=rows(c,'''SELECT e.*,p.numero pedido,cl.nombre cliente,t.nombre transporte FROM envios e
            JOIN pedidos p ON p.id=e.pedido_id JOIN clientes cl ON cl.id=p.cliente_id
            LEFT JOIN asignaciones_transporte a ON a.envio_id=e.id AND a.fecha_fin IS NULL
            LEFT JOIN transportistas t ON t.id=a.transportista_id ORDER BY e.id DESC''')
        out['registros']=rs
        out['indicadores']=[metric('Preparados',sum(r['estado']=='Preparado' for r in rs)),metric('En tránsito',sum(r['estado']=='En transito' for r in rs),tone='sand'),metric('Entregados',sum(r['estado']=='Entregado' for r in rs),tone='sage'),metric('Con inconvenientes',sum(bool(r['incidencia']) for r in rs),tone='rose')]
        out['estados']=[dict(label=state,total=sum(r['estado']==state for r in rs)) for state in ('Preparado','En transito','Entregado')]
    elif slug in ('finanzas','reportes'):
        f=financial(c,u,{})
        out['indicadores']=[metric('Ventas vigentes',f['ventas_vigentes'],True,'sand'),metric('Cobros verificados',f['cobros_verificados'],True,'sage'),metric('Saldo por cobrar',f['saldos_pendientes'],True),metric('Por verificar',f['pagos_por_verificar'],True,'rose')]
        out['registros']=f['ingresos'] if slug=='finanzas' else commercial_rows(c,u,'ventas')
        out['cuentas']=f['cuentas']
        if slug=='reportes':
            from backend.modules.reportes import handle
            out['mas_vendidos']=handle(c,u,3,{})[:5]
            out['clientes_frecuentes']=handle(c,u,4,{})[:4]
        else:
            out['serie']=sales_series(c,u)
    elif slug=='marketing':
        from backend.modules.marketing import handle
        stats=handle(c,u,4,{})
        out['registros']=rows(c,'SELECT * FROM publicaciones ORDER BY id DESC')
        out['consultas']=rows(c,'SELECT * FROM consultas_marketing ORDER BY id DESC')
        out['indicadores']=[metric('Publicaciones',len(out['registros'])),metric('Consultas',len(out['consultas'])),metric('Respuestas enviadas',c.execute("SELECT COUNT(*) FROM respuestas_consulta WHERE estado='Enviada'").fetchone()[0],tone='sage'),metric('Vistas registradas',stats['vistas'] if stats['registros'] else 'Sin datos',tone='sand')]
    return out
