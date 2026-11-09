from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_consistencia import Consistency
from backend.core import get,DATA
from backend.storage import save_file
case=Consistency();case.setUp()
try:
 case.paid_sale();save_file(case.c,'ac'*24+'.pdf',b'%PDF-1.4 evidencia temporal de migracion');case.c.commit()
 saved=case.call('administracion',3,dict(nombre='Respaldo temporal para verificar migración',confirmar=True))
 record=get(case.c,'respaldos',saved['id'])
 Path(sys.argv[1]).write_bytes((DATA/'respaldos'/record['ubicacion']).read_bytes())
finally:case.tearDown()
