import {f,id,operation,query} from './fields.js';
const data=()=>[f('nombre','Nombre completo','text',{required:true}),f('telefono','Teléfono','tel',{required:true}),f('direccion','Dirección','text',{required:true}),f('referencia','Referencia de entrega'),f('correo','Correo electrónico','email')];
export default {slug:'clientes',icon:'◎',description:'Datos de contacto e historial de cada comprador.',operations:[
operation('Registrar cliente',data(),{write:true}),
operation('Consultar clientes',[query()],{source:'clientes'}),
operation('Actualizar datos',[id('clientes','Cliente'),...data()],{write:true,source:'clientes',prefill:true}),
operation('Registrar historial de compra',[id('clientes','Cliente','cliente_id')],{help:'El historial se vincula automáticamente al registrar pedidos y ventas. Esta pantalla consulta esos documentos.'})]};
