from backend.business import *
WRITES={1,2,3,4}
def handle(c,u,op,d):
    return {1:payment,2:verify_payment,3:receipt,4:void_payment}[op](c,u,d)
