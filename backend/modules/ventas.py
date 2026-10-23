from backend.business import *
WRITES={1,4}
def handle(c,u,op,d):
    if op==1:
        return sale(c,u,d)
    if op==4:
        return void_sale(c,u,d)
    return filtered(c,u,'ventas',d)
