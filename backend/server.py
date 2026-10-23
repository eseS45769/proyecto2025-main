import argparse
import base64
import html
import json
import mimetypes
import secrets
import threading
import time
import traceback
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
from backend.core import *
from backend.catalog import MODULES
from backend.modules import dispatch
from backend.queries import reference,dashboard
from backend.panels import home,panel

LOCK=threading.RLock()
ATTEMPTS={}

class Handler(BaseHTTPRequestHandler):
    server_version='Saique'

    def do_GET(self):
        self.handle_request('GET')

    def do_POST(self):
        self.handle_request('POST')

    def respond(self,data,status=200,content_type='application/json; charset=utf-8',headers=None):
        if content_type.startswith('application/json'):
            data=json.dumps(data,ensure_ascii=False).encode('utf-8')
        elif isinstance(data,str):
            data=data.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','same-origin')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' https: data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'")
        for k,v in (headers or {}).items():
            self.send_header(k,v)
        self.end_headers()
        self.wfile.write(data)

    def json_body(self):
        try:
            size=int(self.headers.get('Content-Length',0))
            if size<0 or size>12_000_000:
                raise Error('El archivo o solicitud supera el tamaño permitido.',413)
            body=json.loads(self.rfile.read(size) or b'{}')
            if not isinstance(body,dict):
                raise ValueError()
            return body
        except (ValueError,UnicodeError):
            raise Error('La solicitud no contiene un objeto JSON válido.',400)

    def session(self,c):
        cookie=SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie',''))
            token=cookie['saique_session'].value if 'saique_session' in cookie else ''
        except Exception:
            token=''
        hashed=hashlib.sha256(token.encode()).hexdigest()
        s=one(c,'SELECT * FROM sesiones WHERE token_hash=? AND expira>?',(hashed,now()))
        if not s:
            raise Error('Iniciá sesión para continuar.',401)
        u=one(c,"SELECT u.*,r.nombre rol,r.estado rol_estado FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE u.id=?",(s['usuario_id'],))
        if not u or u['estado']!='Activo' or u['rol_estado']!='Activo':
            raise Error('La cuenta está desactivada.',401)
        return u,s

    def handle_request(self,method):
        parsed=urlparse(self.path)
        path=parsed.path
        try:
            with LOCK:
                if method=='GET' and not path.startswith(('/api/','/archivos/')):
                    self.static(path)
                    return
                with connect() as c:
                    if path=='/api/login' and method=='POST':
                        self.login(c,self.json_body())
                        return
                    u,s=self.session(c)
                    if method=='POST':
                        if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),s['csrf']):
                            raise Error('La sesión cambió. Recargá la página.',403)
                        origin=self.headers.get('Origin')
                        if origin and urlparse(origin).netloc!=self.headers.get('Host'):
                            raise Error('Origen de la solicitud no autorizado.',403)
                    data=self.json_body() if method=='POST' else {k:v[-1] for k,v in parse_qs(parsed.query).items()}
                    if path=='/api/session' and method=='GET':
                        specs=[m|{'operaciones':[i for i in range(1,len(m['children'])+1) if f'{m["slug"]}.{i}' in permissions(c,u)]} for m in MODULES]
                        self.respond(dict(usuario={k:u[k] for k in ('id','nombre','usuario','rol','rol_id')},csrf=s['csrf'],permisos=permissions(c,u),modulos=[m for m in specs if m['operaciones']]))
                    elif path=='/api/logout' and method=='POST':
                        c.execute('DELETE FROM sesiones WHERE token_hash=?',(s['token_hash'],))
                        self.respond(dict(ok=True),headers={'Set-Cookie':'saique_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'})
                    elif path=='/api/dashboard' and method=='GET':
                        self.respond(home(c,u))
                    elif path.startswith('/api/panel/') and method=='GET':
                        self.respond(panel(c,u,path.split('/')[-1]))
                    elif path.startswith('/api/referencias/') and method=='GET':
                        self.respond(reference(c,u,path.split('/')[-1]))
                    elif path=='/api/archivo' and method=='POST':
                        self.upload(c,u,data)
                    elif path.startswith('/api/comprobante/') and method=='GET':
                        self.print_receipt(c,u,integer(path.split('/')[-1]))
                    elif path.startswith('/api/respaldo/') and method=='GET':
                        authorize(c,u,'administracion.3')
                        r=get(c,'respaldos',path.split('/')[-1])
                        self.respond((DATA/'respaldos'/r['ubicacion']).read_bytes(),content_type='application/zip',headers={'Content-Disposition':f'attachment; filename="saique-respaldo-{r["id"]}.zip"'})
                    elif path.startswith('/archivos/') and method=='GET':
                        name=path.split('/')[-1]
                        if not re.fullmatch(r'[a-f0-9]+\.(png|jpg|webp|pdf|mp4)',name):
                            raise Error('Archivo no encontrado.',404)
                        target=DATA/'archivos'/name
                        if not target.is_file():
                            raise Error('Archivo no encontrado.',404)
                        self.respond(target.read_bytes(),content_type=mimetypes.guess_type(name)[0] or 'application/octet-stream')
                    elif re.fullmatch(r'/api/[a-z]+/\d+',path):
                        _,_,slug,op=path.split('/')
                        value=dispatch(c,u,slug,int(op),data,method)
                        if method=='GET' and data.get('formato')=='xlsx':
                            from backend.export import xlsx
                            self.respond(xlsx(value),content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':f'attachment; filename="saique-{slug}.xlsx"'})
                        else:
                            self.respond(value)
                    else:
                        raise Error('Ruta no encontrada.',404)
        except Error as e:
            self.respond(dict(error=str(e)),e.status)
        except sqlite3.IntegrityError:
            self.respond(dict(error='El registro ya existe o incumple una relación obligatoria. Revisá los datos.'),409)
        except (BrokenPipeError,ConnectionResetError):
            pass
        except Exception:
            traceback.print_exc()
            self.respond(dict(error='No se pudo completar la operación. Los cambios no se confirmaron.'),500)

    def login(self,c,d):
        origin=self.headers.get('Origin')
        if origin and urlparse(origin).netloc!=self.headers.get('Host'):
            raise Error('Origen no autorizado.',403)
        ip=self.client_address[0]
        recent=[t for t in ATTEMPTS.get(ip,[]) if time.monotonic()-t<300]
        ATTEMPTS[ip]=recent
        if len(recent)>=10:
            raise Error('Demasiados intentos. Esperá cinco minutos.',429)
        u=one(c,"SELECT u.*,r.estado rol_estado FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE u.usuario=?",(text(d,'usuario').lower(),))
        if not u or u['estado']!='Activo' or u['rol_estado']!='Activo' or not check_password(text(d,'password'),u['password_hash']):
            ATTEMPTS[ip].append(time.monotonic())
            raise Error('Usuario o contraseña incorrectos.',401)
        ATTEMPTS.pop(ip,None)
        token=secrets.token_urlsafe(32)
        csrf=secrets.token_urlsafe(32)
        insert(c,'sesiones',dict(token_hash=hashlib.sha256(token.encode()).hexdigest(),usuario_id=u['id'],expira=(datetime.now(timezone(timedelta(hours=-4)))+timedelta(hours=8)).isoformat(timespec='seconds'),csrf=csrf))
        update(c,'usuarios',u['id'],dict(ultimo_acceso=now()))
        audit(c,u,'sesion','Inicio de sesión')
        secure='; Secure' if os.environ.get('SAIQUE_SECURE_COOKIE')=='1' else ''
        self.respond(dict(ok=True),headers={'Set-Cookie':f'saique_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800{secure}'})

    def static(self,path):
        target=(ROOT/'frontend'/path.lstrip('/')).resolve() if path not in ('/','') else ROOT/'frontend/index.html'
        if not target.is_relative_to((ROOT/'frontend').resolve()) or not target.is_file():
            raise Error('Página no encontrada.',404)
        mime=mimetypes.guess_type(str(target))[0] or 'application/octet-stream'
        if target.suffix=='.js':
            mime='text/javascript'
        self.respond(target.read_bytes(),content_type=mime+'; charset=utf-8' if target.suffix in ('.html','.js','.css','.svg') else mime)

    def upload(self,c,u,d):
        try:
            raw=base64.b64decode(d.get('contenido',''),validate=True)
        except Exception:
            raise Error('El archivo no es válido.')
        if not raw or len(raw)>8_000_000:
            raise Error('El archivo debe pesar hasta 8 MB.')
        extension=text(d,'extension').lower()
        signatures={'png':raw.startswith(b'\x89PNG\r\n\x1a\n'),'jpg':raw.startswith(b'\xff\xd8\xff'),'webp':raw.startswith(b'RIFF') and raw[8:12]==b'WEBP','pdf':raw.startswith(b'%PDF-'),'mp4':raw[4:8]==b'ftyp'}
        if not signatures.get(extension):
            raise Error('Usá una imagen PNG/JPG/WebP, PDF o video MP4 válido.')
        name=secrets.token_hex(24)+'.'+extension
        (DATA/'archivos'/name).write_bytes(raw)
        audit(c,u,'archivos','Carga de archivo',detail=name)
        self.respond(dict(url='/archivos/'+name))

    def print_receipt(self,c,u,pid):
        authorize(c,u,'pagos.3')
        p=get(c,'pagos',pid)
        doc=get(c,'pedidos' if p['pedido_id'] else 'ventas',p['pedido_id'] or p['venta_id'])
        owner(c,u,doc['cliente_id'])
        r=one(c,'SELECT * FROM comprobantes_pago WHERE pago_id=?',(pid,))
        if not r:
            raise Error('Primero generá el comprobante.',404)
        client=get(c,'clientes',doc['cliente_id'])
        page=f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>{html.escape(r['numero'])}</title>
        <link rel="stylesheet" href="/styles.css"><body class="receipt"><main><h1>Saique · Comprobante interno</h1><p>No es factura fiscal.</p>
        <h2>{html.escape(r['numero'])}</h2><p>Estado del pago: {html.escape(p['estado'])}</p><p>Cliente: {html.escape(client['nombre'])}</p>
        <p>Documento: {html.escape(doc['numero'])}</p><p>Método: {html.escape(p['metodo'])}</p><p>Referencia: {html.escape(p['referencia'])}</p>
        <h2>Bs {p['monto']/100:.2f}</h2><p>Emitido: {html.escape(r['fecha_emision'])}</p><p>Usá Imprimir del navegador para guardar como PDF.</p></main></body></html>'''
        self.respond(page,content_type='text/html; charset=utf-8')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',default=8000,type=int)
    args=parser.parse_args()
    init()
    print(f'Saique disponible en http://{args.host}:{args.port}',flush=True)
    ThreadingHTTPServer((args.host,args.port),Handler).serve_forever()

if __name__=='__main__':
    main()
