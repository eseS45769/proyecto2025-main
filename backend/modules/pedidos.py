from backend.business import *
WRITES={1,3,4}
def handle(c,u,op,d):
    return {1:order_create,2:lambda c,u,d:filtered(c,u,'pedidos',d),3:order_update,4:order_cancel}[op](c,u,d)
