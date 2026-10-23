import {f,id,operation,docFields,note,choices,check,query} from './fields.js';
export default {slug:'reclamos',icon:'◌',description:'Atención postventa, respuestas y resolución de cada caso.',operations:[
operation('Registrar reclamo',[id('clientes','Cliente','cliente_id'),...docFields(),f('motivo','Motivo','text',{required:true}),note('descripcion','Descripción del problema')],{write:true}),
operation('Consultar reclamo',[query(),id('reclamos','Ficha del reclamo','id',false)],{source:'reclamos'}),
operation('Actualizar estado de reclamo',[id('reclamos','Reclamo'),choices('estado','Nuevo estado',['En revision','Solucionado']),note('observacion','Respuesta y observación')],{write:true,source:'reclamos',help:'Cada cambio conserva el responsable. Seguí la secuencia Pendiente → En revisión → Solucionado.'}),
operation('Cerrar reclamo',[id('reclamos','Reclamo'),note('solucion','Solución documentada'),check()],{write:true,source:'reclamos',help:'Solo se cierra un reclamo solucionado. El cierre no cambia dinero ni stock.'})]};
