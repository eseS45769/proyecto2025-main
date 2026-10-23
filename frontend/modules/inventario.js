import {f,id,operation,query,note} from './fields.js';
export default {slug:'inventario',icon:'▦',description:'Stock físico, reservas y disponibilidad, con cada movimiento documentado.',operations:[
operation('Consultar inventario',[query()],{help:'Disponible = físico − reservas vigentes. Reservar no descuenta unidades físicas.'}),
operation('Actualizar stock',[id('productos','Alfombra','producto_id'),f('variacion','Variación de unidades (+ entrada / − salida)','number',{required:true,step:1}),note(),f('evidencia_url','Evidencia del ajuste','asset')],{write:true,source:'productos',help:'Usá este formulario para ajustes justificados. Las compras y ventas generan sus propios movimientos.'}),
operation('Generar alerta de stock bajo',[],{auto:true,help:'Las alertas se generan automáticamente cuando la disponibilidad alcanza el mínimo. Una reposición resuelve la alerta.'}),
operation('Registrar movimiento de inventario',[],{auto:true,help:'Los movimientos se registran dentro de la transacción de compra, venta, reversión o ajuste. Esta pantalla muestra su origen.'})]};
