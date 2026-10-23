from backend.business import *
WRITES={1}
def handle(c,u,op,d):
    if op==1:
        return purchase(c,u,d)
    if op==2:
        return filtered(c,u,'compras',d)
    if d.get('id'):
        return document(c,u,'compras',d['id'])
    return rows(c,"SELECT m.*,p.sku,p.nombre FROM movimientos_inventario m JOIN productos p ON p.id=m.producto_id WHERE m.tipo='Compra' ORDER BY m.id DESC")
