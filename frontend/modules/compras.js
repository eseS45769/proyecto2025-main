import {id,operation,dates,purchase} from './fields.js';
export default {slug:'compras',icon:'▤',description:'Recepciones de mercadería y detalle de las entradas al almacén.',related:{slug:'proveedores',label:'Volver a Proveedores'},operations:[
purchase(),
operation('Consultar compras',[...dates(),id('proveedores','Proveedor','proveedor_id',false),id('compras','Detalle de compra','id',false)],{source:'compras'}),
operation('Actualizar stock por compra',[id('compras','Compra recibida','id',false)],{auto:true,help:'La entrada se ejecutó al confirmar la compra, desde Compras o Proveedores. Consultar su resultado no vuelve a ingresar mercadería.'})]};
