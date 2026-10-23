"""Exportador XLSX sin dependencias. Usa celdas de texto, nunca fórmulas."""
import io
import zipfile
from xml.sax.saxutils import escape

MONEY={'monto','total','precio_actual','precio_unitario','costo_unitario','importe','saldo','verificado','pendiente','costo','ventas_vigentes','cobros_verificados','saldos_pendientes','pagos_por_verificar','total_vigente','total_anulado'}

def column(i):
    name=''
    while i:
        i,r=divmod(i-1,26)
        name=chr(65+r)+name
    return name

def xlsx(data):
    sheets=[]
    if isinstance(data,list):
        sheets.append(('Registros',data))
    elif isinstance(data,dict):
        scalar=[{'concepto':k.replace('_',' '),'valor_Bs' if k in MONEY else 'valor':v/100 if k in MONEY else v} for k,v in data.items() if v is not None and not isinstance(v,(dict,list))]
        if scalar:
            sheets.append(('Resumen',scalar))
        for k,v in data.items():
            if isinstance(v,list):
                sheets.append((k[:31],v))
    if not sheets:
        sheets=[('Registros',[])]
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        overrides=''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1,len(sheets)+1))
        z.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'+overrides+'</Types>')
        z.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml','<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'+''.join(f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>' for i,(name,_) in enumerate(sheets,1))+'</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1,len(sheets)+1))+'</Relationships>')
        for i,(_,records) in enumerate(sheets,1):
            keys=list(dict.fromkeys(k for r in records if isinstance(r,dict) for k,v in r.items() if not isinstance(v,(dict,list))))
            table=[{k:k.replace('_',' ') for k in keys}]+records if records else [{'estado':'Sin registros'}]
            if not keys:
                keys=['estado']
            xml=[]
            for rn,record in enumerate(table,1):
                cells=[]
                for cn,k in enumerate(keys,1):
                    value=record.get(k,'')
                    if rn>1 and k in MONEY and value is not None:
                        value=value/100
                    coordinate=f'{column(cn)}{rn}'
                    if isinstance(value,(int,float)):
                        cells.append(f'<c r="{coordinate}"><v>{value}</v></c>')
                    else:
                        clean=''.join(ch for ch in str(value if value is not None else '') if ch in '\t\n\r' or ord(ch)>=32)
                        cells.append(f'<c r="{coordinate}" t="inlineStr"><is><t xml:space="preserve">{escape(clean)}</t></is></c>')
                xml.append(f'<row r="{rn}">'+''.join(cells)+'</row>')
            z.writestr(f'xl/worksheets/sheet{i}.xml','<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+''.join(xml)+'</sheetData></worksheet>')
    return output.getvalue()
