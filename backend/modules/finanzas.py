from backend.business import *
WRITES={1}
def handle(c,u,op,d):
    if op==1:
        p=get(c,'pagos',d.get('pago_id'))
        result=recognize(c,u,p)
        audit(c,u,'finanzas','Registrar ingreso por venta',result['id'],'Reconocimiento del mismo pago; sin nuevo cobro')
        return result
    f=financial(c,u,d)
    if op==2:
        return dict(registros=f['ingresos'],total=f['cobros_verificados'])
    if op==3:
        return [a for a in f['cuentas'] if a['saldo']>0 or a['pendiente']>0]
    return f
