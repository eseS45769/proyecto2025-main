import {f,id,operation,query,purchase} from './fields.js';
const data=()=>[f('nombre','Nombre o razón social','text',{required:true}),f('identificacion','Identificación fiscal / comercial'),f('telefono','Teléfono','tel',{required:true}),f('direccion','Dirección','text',{required:true}),f('representante','Representante'),f('rubro','Rubro','text',{required:true}),f('disponibilidad','Días y horarios de atención')];
export default {slug:'proveedores',icon:'▣',description:'Proveedores y recepción de mercadería.',related:{slug:'compras',label:'Abrir módulo de Compras'},operations:[
operation('Registrar proveedor',data(),{write:true}),
operation('Actualizar proveedor',[id('proveedores','Proveedor'),...data()],{write:true,source:'proveedores',prefill:true}),
{...purchase(),title:'Registrar compra de productos'},
operation('Consultar proveedores',[query(),id('proveedores','Ficha de proveedor','id',false)],{source:'proveedores'})]};
