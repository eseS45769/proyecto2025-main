"""Run the project's regression suite in a brand-new PostgreSQL schema only."""
import os,sys,uuid,unittest,json,base64,urllib.request,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
if not os.environ.get('DATABASE_URL'):
    raise SystemExit('Esta prueba requiere DATABASE_URL para una base de pruebas.')
import psycopg
schema='saique_test_'+uuid.uuid4().hex[:12]
with psycopg.connect(os.environ['DATABASE_URL'],sslmode='require',autocommit=True) as raw:
    raw.execute('CREATE SCHEMA '+schema)
os.environ['SAIQUE_PG_SCHEMA']=schema
os.environ['SAIQUE_ADMIN_PASSWORD']='PruebasSaique2026!'
from test_consistencia import Consistency
from backend.core import *
from backend.business import *
from backend.cloud_backups import TABLES
from backend.cloud_seed import bulk
from backend.catalog import MODULES
from backend.storage import save_file,read_file
init()
with connect() as c:
    seeds={t:rows(c,'SELECT * FROM '+t) for t in TABLES}

class PostgreSQLConsistency(Consistency):
    def setUp(self):
        with connect() as c:
            assert c.execute('SELECT current_schema()').fetchone()[0]==schema
            c.execute('TRUNCATE '+','.join(TABLES)+',archivos_contenido,respaldos_contenido,restauraciones_externas RESTART IDENTITY')
            for t,records in seeds.items():
                if records:bulk(c,t,list(records[0]),[tuple(r.values()) for r in records])
            for t in ['roles','usuarios','permisos','roles_permisos','categorias']:
                c.execute("SELECT setval(pg_get_serial_sequence(?, 'id'), (SELECT MAX(id) FROM "+t+"))",(t,))
        super().setUp()

    def test_PR02_fallo_movimiento_revierte_compra(self):
        from unittest.mock import patch
        with patch('backend.business.move',side_effect=sqlite3.IntegrityError('Fallo simulado')):
            with self.assertRaises(sqlite3.IntegrityError):self.buy()
        self.assertEqual(stock(self.c,self.product)['stock_fisico'],0)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM compras').fetchone()[0],0)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM detalles_compra').fetchone()[0],0)

    def test_PR12_respaldo_restauracion_tablas_archivos(self):
        self.buy();name='ab'*24+'.pdf';original=b'%PDF-1.4 archivo de prueba'
        save_file(self.c,name,original);self.c.commit()
        saved=self.call('administracion',3,dict(nombre='Estado inicial PostgreSQL',confirmar=True))
        self.buy(qty=5,ref='CP-002');save_file(self.c,name,b'%PDF-1.4 modificado');self.c.commit()
        out=self.call('administracion',4,dict(respaldo_id=saved['id'],confirmar=True))
        self.assertTrue(out['reiniciar_sesion'])
        self.assertEqual(stock(self.c,self.product)['stock_fisico'],10)
        self.assertEqual(read_file(self.c,name),original)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM sesiones').fetchone()[0],0)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM restauraciones_externas').fetchone()[0],1)
        self.assertTrue(get(self.c,'respaldos',out['copia_previa']))

    def test_paneles_consultan_sin_modificar_documentos(self):
        from backend.panels import panel,home
        order,payment,sale=self.paid_sale()
        before={t:rows(self.c,'SELECT * FROM '+t+' ORDER BY '+('token_hash' if t=='sesiones' else 'id')) for t in TABLES}
        for module in MODULES:
            with self.subTest(module=module['slug']):
                data=panel(self.c,self.u,module['slug'])
                self.assertIn('registros',data)
                self.assertIn('indicadores',data)
        summary=home(self.c,self.u)
        self.assertEqual(summary['serie'][-1]['valor'],54000)
        self.assertEqual(summary['pedidos'][0]['id'],order['id'])
        after={t:rows(self.c,'SELECT * FROM '+t+' ORDER BY '+('token_hash' if t=='sesiones' else 'id')) for t in TABLES}
        self.assertEqual(before,after)

    def test_http_sesion_archivos_y_health_postgresql(self):
        from backend.server import Handler,ThreadingHTTPServer
        from http.cookiejar import CookieJar
        srv=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        worker=threading.Thread(target=srv.serve_forever,daemon=True);worker.start()
        root='http://127.0.0.1:'+str(srv.server_port)
        client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        def req(path,body=None,csrf=None):
            headers={'Content-Type':'application/json'}
            if csrf:headers['X-CSRF-Token']=csrf
            data=json.dumps(body).encode() if body is not None else None
            return client.open(urllib.request.Request(root+path,data=data,headers=headers),timeout=30)
        try:
            self.assertEqual(json.load(req('/health'))['database'],'postgresql')
            self.assertTrue(json.load(req('/api/login',{'usuario':'admin','password':'PruebasSaique2026!'}))['ok'])
            session=json.load(req('/api/session'));self.assertEqual(session['usuario']['usuario'],'admin')
            content=b'%PDF-1.4 persistencia PostgreSQL'
            uploaded=json.load(req('/api/archivo',{'extension':'pdf','contenido':base64.b64encode(content).decode()},session['csrf']))
            self.assertEqual(req(uploaded['url']).read(),content)
        finally:
            srv.shutdown();srv.server_close();worker.join()

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(PostgreSQLConsistency)
    selected=os.environ.get('SAIQUE_TEST_NAMES')
    if selected:
        wanted=set(selected.split(','));suite=unittest.TestSuite(t for t in suite if t._testMethodName in wanted)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'schema':schema,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'success':result.wasSuccessful(),'selected':selected or 'all'}
    Path('test-results').mkdir(exist_ok=True)
    Path('test-results/'+('postgresql-targeted.json' if selected else 'postgresql.json')).write_text(json.dumps(report,indent=2),encoding='utf8')
    raise SystemExit(0 if result.wasSuccessful() else 1)

