import {id,operation,dates,choices} from './fields.js';
const filters=()=>[...dates(),choices('metodo','Método',['Efectivo','Transferencia','QR'],false)];
export default {slug:'finanzas',icon:'◐',description:'Ingresos reconocidos y cuentas por cobrar sin duplicar pagos.',operations:[
operation('Registrar ingreso por venta',[id('pagos','Pago verificado','pago_id')],{write:true,source:'pagos',help:'Reconoce o recupera el ingreso del mismo pago verificado; no vuelve a cobrar al cliente.'}),
operation('Consultar ingresos por periodo',filters(),{export:true}),
operation('Controlar cuentas pendientes',[...dates(),id('clientes','Cliente','cliente_id',false)],{export:true,related:{slug:'pagos',op:1,label:'Registrar pago'}}),
operation('Generar resumen financiero',[...filters(),id('clientes','Cliente','cliente_id',false)],{export:true,help:'Ventas, cobros verificados y saldos se muestran por separado. Las compras no se presentan como utilidad.'})]};
