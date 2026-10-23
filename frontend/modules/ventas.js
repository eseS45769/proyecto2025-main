import {id,operation,lines,dates,note,check,query} from './fields.js';
export default {slug:'ventas',icon:'◈',description:'Ventas confirmadas con precios históricos y saldos de cobro.',operations:[
operation('Registrar venta',[id('pedidos','Pedido de origen (opcional)','pedido_id',false),id('clientes','Cliente de venta directa','cliente_id',false),lines()],{write:true,help:'Si elegís un pedido, se usan sus líneas y su cliente. La venta consume la reserva y registra una sola salida.'}),
operation('Ver detalle de venta',[id('ventas','Venta','id')],{source:'ventas'}),
operation('Listar ventas',[...dates(),query(),id('clientes','Cliente','cliente_id',false)],{source:'ventas'}),
operation('Anular venta',[id('ventas','Venta'),note(),note('evidencia_devolucion','Evidencia de devolución física o de no despacho'),check('devolucion_recibida','Recibí físicamente la devolución (si hubo entrega)'),check()],{write:true,source:'ventas',help:'Los pagos deben estar resueltos. No se repone stock sin evidencia de devolución o de no despacho.'})]};
