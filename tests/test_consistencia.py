"""Escenarios PR01–PR12 del documento, sobre base y archivos temporales."""
import concurrent.futures
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TEMP=tempfile.TemporaryDirectory()
os.environ['SAIQUE_DATA']=TEMP.name
os.environ['SAIQUE_ADMIN_PASSWORD']='PruebasSaique2026!'

from backend.core import *
from backend.business import *
from backend.modules import dispatch
from backend.modules.administracion import handle as admin_handle
from backend.export import xlsx
from backend.catalog import MODULES

class Consistency(unittest.TestCase):
    def setUp(self):
        for name in ('saique.sqlite3','saique.sqlite3-wal','saique.sqlite3-shm'):
            p=Path(TEMP.name)/name
            if p.exists():
                p.unlink()
        init()
        self.c=connect()
        self.u=get(self.c,'usuarios',1)
        self.client=self.call('clientes',1,dict(nombre='Cliente de prueba',telefono='76123456',direccion='Tarija, centro',referencia='Puerta azul'))['id']
        self.supplier=self.call('proveedores',1,dict(nombre='Proveedor de prueba',telefono='76111222',direccion='Tarija',rubro='Alfombras'))['id']
        self.product=self.call('productos',1,dict(sku='ALF-001',nombre='Alfombra moderna',descripcion='Tejido de prueba',categoria_id=1,ancho_cm='120',largo_cm='180',precio_actual='180.00',stock_minimo=2,stock_inicial=0))['id']

    def tearDown(self):
        self.c.close()

    def call(self,slug,op,data=None,user=None):
        from importlib import import_module
        write=op in import_module('backend.modules.'+slug).WRITES
        return dispatch(self.c,user or self.u,slug,op,data or {},'POST' if write else 'GET')

    def buy(self,qty=10,ref='CP-001'):
        return self.call('compras',1,dict(proveedor_id=self.supplier,referencia=ref,lineas=[dict(producto_id=self.product,cantidad=qty,costo_unitario='120.00')]))

    def order(self,qty=3):
        return self.call('pedidos',1,dict(cliente_id=self.client,direccion_entrega='Dirección pactada',canal='WhatsApp',lineas=[dict(producto_id=self.product,cantidad=qty)]))

    def paid_sale(self):
        self.buy()
        o=self.order()
        p=self.call('pagos',1,dict(pedido_id=o['id'],monto='540.00',metodo='QR',referencia='PG-001'))
        self.call('pagos',2,dict(id=p['id'],resultado='Verificado',evidencia='QR cotejado con banco'))
        v=self.call('ventas',1,dict(pedido_id=o['id']))
        return o,p,v

    def dispatched(self):
        o,p,v=self.paid_sale()
        en=self.call('envios',1,dict(pedido_id=o['id'],direccion='Dirección pactada',costo='0'))
        self.call('envios',2,dict(id=en['id'],nuevo_transportista={'nombre':'Transporte prueba','telefono':'76123456'}))
        self.call('envios',3,dict(id=en['id'],numero_guia='GUIA-001',confirmar=True))
        return o,p,v,en

    def test_PR01_recepcion_unica_compartida(self):
        self.buy()
        with self.assertRaises(Error):
            self.call('proveedores',3,dict(proveedor_id=self.supplier,referencia=' cp-001 ',lineas=[dict(producto_id=self.product,cantidad=10,costo_unitario='120')]))
        self.assertEqual(stock(self.c,self.product)['stock_fisico'],10)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM compras').fetchone()[0],1)
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM movimientos_inventario WHERE tipo='Compra'").fetchone()[0],1)

    def test_PR02_fallo_movimiento_revierte_compra(self):
        self.c.execute("CREATE TRIGGER fallo_mov BEFORE INSERT ON movimientos_inventario BEGIN SELECT RAISE(ABORT,'fallo simulado'); END")
        self.c.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            self.buy()
        self.assertEqual(stock(self.c,self.product)['stock_fisico'],0)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM compras').fetchone()[0],0)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM detalles_compra').fetchone()[0],0)

    def test_PR03_reservas_simultaneas(self):
        self.buy(qty=1)
        def worker(_):
            c=connect()
            try:
                return dispatch(c,self.u,'pedidos',1,dict(cliente_id=self.client,direccion_entrega='Tarija',canal='Directo',lineas=[dict(producto_id=self.product,cantidad=1)]),'POST')['estado']
            finally:
                c.close()
        with concurrent.futures.ThreadPoolExecutor(2) as executor:
            result=list(executor.map(worker,range(2)))
        self.assertCountEqual(result,['Reservado','Pendiente stock'])
        self.assertEqual(stock(self.c,self.product)['reservado'],1)

    def test_PR04_venta_consumo_unico(self):
        self.buy()
        o=self.order()
        s=stock(self.c,self.product)
        self.assertEqual((s['stock_fisico'],s['reservado']),(10,3))
        self.call('ventas',1,dict(pedido_id=o['id']))
        with self.assertRaises(Error):
            self.call('ventas',1,dict(pedido_id=o['id']))
        s=stock(self.c,self.product)
        self.assertEqual((s['stock_fisico'],s['reservado']),(7,0))
        self.assertEqual(get(self.c,'pedidos',o['id'])['estado'],'Confirmado')

    def test_PR05_ajuste_protege_reserva(self):
        self.buy()
        self.order()
        with self.assertRaises(Error):
            self.call('inventario',2,dict(producto_id=self.product,variacion=-8,motivo='Conteo físico'))
        self.assertEqual(stock(self.c,self.product)['stock_fisico'],10)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM ajustes_inventario').fetchone()[0],0)

    def test_PR06_pago_ingreso_recibo_idempotentes(self):
        o,p,v=self.paid_sale()
        self.call('pagos',2,dict(id=p['id'],resultado='Verificado',evidencia='Mismo banco'))
        self.call('finanzas',1,dict(pago_id=p['id']))
        a=self.call('pagos',3,dict(id=p['id']))
        b=self.call('pagos',3,dict(id=p['id']))
        self.assertEqual(a['numero'],b['numero'])
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM ingresos').fetchone()[0],1)
        self.assertEqual(balance(self.c,venta_id=v['id'])['saldo'],0)
        self.assertEqual(financial(self.c,self.u,{})['cobros_verificados'],54000)

    def test_PR07_anular_pago_venta(self):
        o,p,v=self.paid_sale()
        with self.assertRaises(Error):
            self.call('ventas',4,dict(id=v['id'],motivo='Cancelación',evidencia_devolucion='No despachado',confirmar=True))
        self.call('pagos',4,dict(id=p['id'],motivo='Devolución a cliente',confirmar=True))
        self.assertEqual(balance(self.c,venta_id=v['id'])['saldo'],54000)
        self.assertEqual(stock(self.c,self.product)['stock_fisico'],7)
        self.call('ventas',4,dict(id=v['id'],motivo='Cancelación',evidencia_devolucion='Almacén confirma no despacho',confirmar=True))
        self.call('ventas',4,dict(id=v['id'],motivo='Reintento',confirmar=True))
        self.assertEqual(stock(self.c,self.product)['stock_fisico'],10)
        self.assertEqual(get(self.c,'pedidos',o['id'])['estado'],'Cancelado')
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM ingresos WHERE estado='Vigente'").fetchone()[0],0)

    def test_PR08_alerta_unica_resolucion(self):
        alert(self.c,self.product)
        alert(self.c,self.product)
        self.c.commit()
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM alertas_stock WHERE estado='Activa'").fetchone()[0],1)
        self.buy()
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM alertas_stock WHERE estado='Activa'").fetchone()[0],0)

    def test_PR09_entrega_no_descuenta(self):
        o,p,v,en=self.dispatched()
        movements=self.c.execute('SELECT COUNT(*) FROM movimientos_inventario').fetchone()[0]
        with self.assertRaises(Error):
            self.call('envios',4,dict(id=en['id'],receptor='Cliente',confirmar=True))
        self.call('envios',4,dict(id=en['id'],incidencia='Cliente ausente'))
        self.assertEqual(get(self.c,'envios',en['id'])['estado'],'En transito')
        self.call('envios',4,dict(id=en['id'],receptor='Cliente',evidencia_entrega='Firma recibida',confirmar=True))
        self.assertEqual(get(self.c,'pedidos',o['id'])['estado'],'Entregado')
        self.assertEqual(stock(self.c,self.product)['stock_fisico'],7)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM movimientos_inventario').fetchone()[0],movements)

    def test_PR10_cliente_no_accede_ajenos(self):
        self.buy()
        o=self.order()
        other=self.call('clientes',1,dict(nombre='Otro cliente',telefono='76123999',direccion='Otra dirección'))
        role=one(self.c,"SELECT id FROM roles WHERE nombre='Cliente'")['id']
        user=self.call('administracion',1,dict(nombre='Cliente externo',usuario='cliente',password='ClaveCliente2026!',rol_id=role,estado='Activo',cliente_id=other['id']))
        with self.assertRaises(Error) as context:
            self.call('pedidos',2,dict(id=o['id']),user)
        self.assertEqual(context.exception.status,403)
        self.assertEqual(self.call('pedidos',2,{},user),[])
        with self.assertRaises(Error):
            self.call('pagos',1,dict(pedido_id=o['id'],monto='10',metodo='Efectivo',referencia='Ajeno'),user)
        with self.assertRaises(Error):
            self.call('inventario',1,{},user)

    def test_PR11_historicos_intactos(self):
        o,p,v=self.paid_sale()
        self.call('productos',2,dict(id=self.product,sku='ALF-001',nombre='Nuevo nombre',descripcion='Nueva descripción',categoria_id=1,ancho_cm='120',largo_cm='180',precio_actual='999.00'))
        self.call('clientes',3,dict(id=self.client,nombre='Cliente de prueba',telefono='76123456',direccion='Nueva dirección'))
        self.assertEqual(balance(self.c,venta_id=v['id'])['total'],54000)
        self.assertEqual(get(self.c,'pedidos',o['id'])['direccion_entrega'],'Dirección pactada')

    def test_PR12_respaldo_restauracion_tablas_archivos(self):
        self.buy()
        filename='ab'*24+'.pdf'
        asset=Path(TEMP.name)/'archivos'/filename
        asset.write_bytes(b'%PDF-1.4 archivo de prueba')
        saved=self.call('administracion',3,dict(nombre='Estado inicial',confirmar=True))
        self.buy(qty=5,ref='CP-002')
        asset.write_bytes(b'%PDF-1.4 archivo modificado')
        out=self.call('administracion',4,dict(respaldo_id=saved['id'],confirmar=True))
        self.assertTrue(out['reiniciar_sesion'])
        self.assertEqual(stock(self.c,self.product)['stock_fisico'],10)
        self.assertEqual(asset.read_bytes(),b'%PDF-1.4 archivo de prueba')
        self.assertTrue((Path(TEMP.name)/'restauraciones.jsonl').is_file())
        self.assertEqual(self.c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
        self.assertFalse(self.c.execute('PRAGMA foreign_key_check').fetchall())

    def test_reclamos_estados_y_cierre(self):
        self.buy()
        o=self.order()
        r=self.call('reclamos',1,dict(cliente_id=self.client,pedido_id=o['id'],motivo='Consulta',descripcion='Problema de atención'))
        with self.assertRaises(Error):
            self.call('reclamos',4,dict(id=r['id'],solucion='Resuelto',confirmar=True))
        self.call('reclamos',3,dict(id=r['id'],estado='En revision',observacion='Revisando'))
        self.call('reclamos',3,dict(id=r['id'],estado='Solucionado',observacion='Respuesta aceptada'))
        final=self.call('reclamos',4,dict(id=r['id'],solucion='Cliente conforme',confirmar=True))
        self.assertEqual(final['estado'],'Cerrado')
        self.assertEqual(len(final['historial']),4)
        self.assertEqual(stock(self.c,self.product)['stock_fisico'],10)

    def test_pagos_no_sobrepasan_saldo(self):
        self.buy()
        o=self.order()
        self.call('pagos',1,dict(pedido_id=o['id'],monto='500',metodo='Efectivo',referencia='PARCIAL'))
        with self.assertRaises(Error):
            self.call('pagos',1,dict(pedido_id=o['id'],monto='50',metodo='QR',referencia='EXCESO'))
        self.assertEqual(balance(self.c,pedido_id=o['id'])['verificado'],0)

    def test_cuenta_pedido_venta_sin_duplicacion(self):
        self.buy()
        order=self.order()
        before=financial(self.c,self.u,{})
        self.assertEqual(len(before['cuentas']),1)
        self.assertEqual(before['ventas_vigentes'],0)
        self.assertEqual(before['saldos_pendientes'],54000)
        self.call('ventas',1,dict(pedido_id=order['id']))
        after=financial(self.c,self.u,{})
        self.assertEqual(len(after['cuentas']),1)
        self.assertEqual(after['ventas_vigentes'],54000)

    def test_metricas_acumuladas_ultimo_corte(self):
        first=self.call('marketing',1,dict(productos=[self.product],contenido='Alfombra',enlace_externo='https://www.tiktok.com/@tienda/video/123',difusion_confirmada=True,metricas=dict(vistas=100,likes=10,comentarios=2,fuente='TikTok',fecha_medicion='2026-10-01T12:00:00-04:00')))
        self.call('marketing',1,dict(publicacion_id=first['id'],productos=[self.product],contenido='Alfombra',enlace_externo='https://www.tiktok.com/@tienda/video/123',difusion_confirmada=True,metricas=dict(vistas=150,likes=15,comentarios=3,fuente='TikTok',fecha_medicion='2026-10-02T12:00:00-04:00')))
        result=self.call('marketing',4,{})
        self.assertEqual(result['vistas'],150)
        self.assertEqual(len(result['registros']),6)

    def test_ultimo_administrador_protegido(self):
        with self.assertRaises(Error):
            self.call('administracion',1,dict(id=1,nombre='Admin',usuario='admin',rol_id=self.u['rol_id'],estado='Inactivo'))
        with self.assertRaises(Error):
            self.call('administracion',2,dict(rol_id=self.u['rol_id'],permisos=[]))
        self.assertEqual(get(self.c,'usuarios',1)['estado'],'Activo')

    def test_marketing_no_simula_metricas(self):
        empty_stats=self.call('marketing',4,{})
        self.assertEqual(empty_stats['estado'],'Sin datos')
        p=self.call('marketing',1,dict(productos=[self.product],contenido='Presentación alfombra'))
        self.assertEqual(p['estado'],'Preparada')
        p=self.call('marketing',1,dict(publicacion_id=p['id'],productos=[self.product],contenido='Presentación',enlace_externo='https://www.tiktok.com/@tienda/video/123',difusion_confirmada=True,metricas=dict(vistas=100,likes=10,comentarios=2,fuente='Registro manual de TikTok')))
        self.assertEqual(p['estado'],'Publicada')
        self.assertEqual(self.call('marketing',4,{})['vistas'],100)

    def test_55_operaciones_14_modulos(self):
        self.assertEqual(len(MODULES),14)
        self.assertEqual(sum(len(m['children']) for m in MODULES),55)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM permisos').fetchone()[0],55)

    def test_paneles_consultan_sin_modificar_documentos(self):
        from backend.panels import panel,home
        order,payment,sale=self.paid_sale()
        changes=self.c.total_changes
        for module in MODULES:
            with self.subTest(module=module['slug']):
                data=panel(self.c,self.u,module['slug'])
                self.assertIn('registros',data)
                self.assertIn('indicadores',data)
        summary=home(self.c,self.u)
        self.assertEqual(summary['serie'][-1]['valor'],54000)
        self.assertEqual(summary['pedidos'][0]['id'],order['id'])
        self.assertEqual(self.c.total_changes,changes)

    def test_panel_cliente_solo_muestra_documentos_propios(self):
        from backend.panels import panel,home
        self.buy()
        self.order()
        other=self.call('clientes',1,dict(nombre='Cliente privado',telefono='76123777',direccion='Otra dirección'))
        role=one(self.c,"SELECT id FROM roles WHERE nombre='Cliente'")['id']
        user=self.call('administracion',1,dict(nombre='Cliente privado',usuario='privado',password='ClaveCliente2026!',rol_id=role,estado='Activo',cliente_id=other['id']))
        self.assertEqual(panel(self.c,user,'pedidos')['registros'],[])
        self.assertEqual(home(self.c,user)['pedidos'],[])
        with self.assertRaises(Error):
            panel(self.c,user,'administracion')

    def test_exportacion_excel_valida(self):
        import io,zipfile,xml.etree.ElementTree as ET
        payload=xlsx({'registros':[dict(numero='VT-001',total=54000,nombre='=HYPERLINK("malicioso")')],'total_vigente':54000})
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            for name in z.namelist():
                if name.endswith('.xml') or name.endswith('.rels'):
                    ET.fromstring(z.read(name))
            sheet=z.read('xl/worksheets/sheet2.xml').decode()
            self.assertIn('<v>540.0</v>',sheet)
            self.assertIn('t="inlineStr"',sheet)
            self.assertNotIn('<f>',sheet)

if __name__=='__main__':
    unittest.main(verbosity=2)
