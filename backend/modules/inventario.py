from backend.business import *
WRITES={2}
def handle(c,u,op,d):
    if op==2:
        return adjustment(c,u,d)
    if op==1:
        result=inventory(c)
        q=str(d.get('q') or '').casefold()
        return [r for r in result if q in (r['sku']+' '+r['nombre']+' '+r['categoria']).casefold() and (not d.get('estado') or r['estado']==d['estado'])]
    if op==3:
        return rows(c,'SELECT a.*,p.sku,p.nombre FROM alertas_stock a JOIN productos p ON p.id=a.producto_id ORDER BY a.id DESC')
    return rows(c,'SELECT m.*,p.sku,p.nombre,u.nombre responsable FROM movimientos_inventario m JOIN productos p ON p.id=m.producto_id JOIN usuarios u ON u.id=m.responsable_id ORDER BY m.id DESC')
