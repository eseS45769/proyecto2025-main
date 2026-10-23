import {id,operation,dates,choices} from './fields.js';
export default {slug:'reportes',icon:'▥',description:'Resultados de ventas, cobros, productos y frecuencia de clientes.',operations:[
operation('Generar reporte de ventas',[...dates(),id('clientes','Cliente','cliente_id',false),id('productos','Alfombra','producto_id',false)],{export:true}),
operation('Generar reporte financiero',[...dates(),choices('metodo','Método',['Efectivo','Transferencia','QR'],false)],{export:true}),
operation('Ver productos más vendidos',[...dates(),id('categorias','Categoría','categoria_id',false)],{export:true,help:'Clasificación por unidades de ventas vigentes en el periodo seleccionado.'}),
operation('Ver clientes frecuentes',dates(),{export:true,help:'Frecuencia = número de ventas vigentes. El importe comprado se muestra por separado.'})]};
