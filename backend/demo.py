"""Carga demostrativa aditiva y atómica: python -m backend.demo."""
import json
from contextlib import ExitStack
from datetime import datetime, timedelta
from importlib import import_module
from unittest.mock import patch

from backend.core import DATA, connect, init, one, rows, now, authorize
from backend.catalog import MODULES
from backend.modules.administracion import backup

MARKER = 'SAIQUE_DEMO_V1'


def populate(c, u):
    """Una sola transacción; los handlers aplican las reglas de producción."""
    modules = {m['slug']: import_module('backend.modules.' + m['slug']) for m in MODULES}
    def call(slug, op, **data):
        authorize(c, u, f'{slug}.{op}')
        return modules[slug].handle(c, u, op, data)

    c.execute('BEGIN IMMEDIATE')
    try:
        if one(c, 'SELECT id FROM auditorias WHERE detalle=?', (MARKER,)):
            c.rollback()
            return {'existente': True}
        clients = []
        for i, name in enumerate(['Lucía Mendoza', 'Diego Rojas', 'Valentina Soto', 'Mateo Vargas', 'Camila Flores', 'Hotel Los Olivos', 'Estudio Casa Norte', 'Sofía Arce']):
            clients.append(call('clientes', 1, nombre=name+' · DEMO', telefono='700010%02d'%i,
                email=f'cliente{i+1}@example.invalid', direccion=f'Tarija · Dirección de prueba {i+1}', referencia='DEMO · Contacto ficticio'))
        suppliers = [call('proveedores', 1, nombre=name+' · DEMO', telefono='700020%02d'%i,
            direccion='Dirección ficticia para demostración', rubro='Alfombras y textiles') for i, name in enumerate(['Textiles Andinos', 'Tejidos del Sur', 'Casa Telar'])]
        cats = rows(c, "SELECT id FROM categorias WHERE estado='Activo'")
        catalog = [('Arena Natural',180,24), ('Olivo Geométrica',260,20), ('Terracota Bohemia',340,18), ('Niebla Suave',420,15), ('Índigo Clásica',560,12), ('Lino Minimal',220,16), ('Rosa Infantil',190,3), ('Ocre Pasillo',150,0)]
        products = []
        for i, (name, price, qty) in enumerate(catalog):
            products.append(call('productos', 1, sku=f'DEMO-ALF-{i+1:03}', nombre=name+' · DEMO',
                descripcion='Colección de demostración. Tejido decorativo para interiores.', categoria_id=cats[i%len(cats)]['id'],
                ancho_cm=120 if i<4 else 160, largo_cm=180 if i<4 else 230, precio_actual=str(price), stock_minimo=3, stock_inicial=0))
        for i, supplier in enumerate(suppliers):
            lines = [dict(producto_id=products[j]['id'],cantidad=item[2],costo_unitario=str(item[1]//2)) for j,item in enumerate(catalog) if j%3==i and item[2]]
            call('compras',1,proveedor_id=supplier['id'],referencia=f'DEMO-CP-{i+1:03}',lineas=lines,observacion='Recepción simulada · DEMO')
        orders, sales, payments, shipments = [], [], [], []
        today = datetime.fromisoformat(now())
        for i in range(12):
            # Fechas coherentes en los documentos de cada escenario simulado.
            stamp = (today-timedelta(days=max(0,6-i))).isoformat(timespec='seconds')
            with ExitStack() as stack:
                for mod in ['backend.business', *[m.__name__ for m in modules.values()]]:
                    stack.enter_context(patch(mod+'.now',return_value=stamp))
                p = products[i%6] if i<10 else products[7 if i==10 else 6]
                client = clients[i%len(clients)]
                order = call('pedidos',1,cliente_id=client['id'],direccion_entrega=client['direccion'],referencia_entrega='Escenario de demostración',
                    canal=['WhatsApp','Directo','TikTok'][i%3],lineas=[dict(producto_id=p['id'],cantidad=2 if i<6 else 1)])
                orders.append(order['id'])
                if i==11:
                    call('pedidos',4,id=order['id'],confirmar=True,motivo='DEMO · Cliente desiste antes del cobro')
                if i>=9:
                    continue
                total = c.execute('SELECT SUM(cantidad*precio_unitario) FROM detalles_pedido WHERE pedido_id=?',(order['id'],)).fetchone()[0]
                amount = total if i!=7 else total//2
                pay = call('pagos',1,pedido_id=order['id'],monto=f'{amount/100:.2f}',metodo=['QR','Transferencia','Efectivo'][i%3],referencia=f'DEMO-PG-{i+1:03}')
                payments.append(pay['id'])
                if i==8:
                    continue
                call('pagos',2,id=pay['id'],resultado='Verificado',evidencia='DEMO · Verificación simulada; no representa un cobro real')
                call('pagos',3,id=pay['id'])
                sale = call('ventas',1,pedido_id=order['id'])
                sales.append(sale['id'])
                if i<6:
                    shipment=call('envios',1,pedido_id=order['id'],direccion=client['direccion'],costo='0',fecha_estimada=today.date().isoformat())
                    shipments.append(shipment['id'])
                    call('envios',2,id=shipment['id'],nuevo_transportista={'nombre':'Logística de muestra · DEMO','telefono':'70003000'})
                    if i<5:
                        call('envios',3,id=shipment['id'],numero_guia=f'DEMO-GUIA-{i+1:03}',confirmar=True)
                    if i<3:
                        call('envios',4,id=shipment['id'],confirmar=True,receptor=client['nombre'],evidencia_entrega='DEMO · Entrega simulada para presentación')
        for i in range(4):
            claim=call('reclamos',1,cliente_id=clients[i]['id'],pedido_id=orders[i],motivo=['Consulta sobre cuidado','Revisión del acabado','Consulta de entrega','Duda sobre medidas'][i],descripcion='DEMO · Caso ficticio de atención posventa.')
            if i>=1:
                call('reclamos',3,id=claim['id'],estado='En revision',observacion='DEMO · Atención asignada al equipo')
            if i>=2:
                call('reclamos',3,id=claim['id'],estado='Solucionado',observacion='DEMO · Se explicó la solución al cliente')
            if i==3:
                call('reclamos',4,id=claim['id'],confirmar=True,solucion='DEMO · Cliente conforme con la explicación')
        call('inventario',2,producto_id=products[5]['id'],variacion=1,motivo='DEMO · Ajuste positivo tras conteo físico de muestra')
        call('productos',4,productos=[p['id'] for p in products[:6]],contenido='DEMO · Colección Hogar en Calma',campania='DEMO · Hogar en Calma')
        for i in range(4):
            publication=call('marketing',1 if i%2==0 else 2,productos=[products[i]['id']],contenido='DEMO · Texturas que transforman tu hogar. Campaña de ejemplo.',campania='DEMO · Hogar en Calma')
            # No se simula una difusión real ni se contacta a personas.
            call('marketing',3,cliente_id=clients[i]['id'],publicacion_id=publication['id'],contacto=clients[i]['nombre'],canal='WhatsApp' if i%2 else 'TikTok',
                pregunta='DEMO · ¿Qué medida recomiendan para una sala?',respuesta='Respuesta preparada: medí el espacio y elegí una alfombra que acompañe tus muebles.')
        from backend.core import audit
        audit(c,u,'demo','Carga de demostración',detail=MARKER)
        if c.execute('PRAGMA foreign_key_check').fetchall():
            raise RuntimeError('Relaciones inconsistentes en la demostración')
        c.commit()
        return dict(clientes=[x['id'] for x in clients],productos=[x['id'] for x in products],pedidos=orders,ventas=sales,pagos=payments,envios=shipments)
    except Exception:
        c.rollback()
        raise


def main():
    init()
    with connect() as c:
        u=one(c,"SELECT u.* FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE r.nombre='Administrador' AND u.estado='Activo' LIMIT 1")
        if not u:
            raise RuntimeError('Se necesita un administrador activo')
        if one(c,'SELECT id FROM auditorias WHERE detalle=?',(MARKER,)):
            print('La demostración ya está cargada. No se duplicaron registros.')
            return
        saved=backup(c,u,'Antes de cargar demostración Saique')
        c.commit()
        result=populate(c,u)
        (DATA/'demo-manifest.json').write_text(json.dumps(dict(respaldo_previo=saved,registros=result),ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:len(v) for k,v in result.items()},ensure_ascii=True))


if __name__=='__main__':
    main()
