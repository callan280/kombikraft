"""Offline typed projection admission. Shape/hash validation is NOT source authentication."""
from pathlib import Path
import hashlib,json,math,re
H=Path(__file__).resolve().parent
FIELDS=[('engineRpm','rpm',12000,'engineRpm'),('oilTemperatureC','°C',206,'oilTempC'),('remainingRangeKm','km',4094,'rangeKm'),('odometerKm','km',16777214,'odometerKm'),('fuelLitres','l',254,'fuelLitres')]
UNAVAILABLE=['indicatedSpeed','coolantTemperatureC','boost','fuelPercent','gear','drivingMode']
def compact(request,previous=None,*,source_pins=None):
 if set(request)!={'id','stateSequence','producerSession','frame'}:raise ValueError('Unexpected typed state request keys')
 rid,seq,session,f=(request[k]for k in ['id','stateSequence','producerSession','frame'])
 if type(rid)is not int or not 1<=rid<=9007199254740090 or type(seq)is not int or not 1<=seq<=2147483647 or not isinstance(session,str)or not re.fullmatch('[A-Za-z0-9_-]{8,64}',session):raise ValueError('Invalid offline state lifetime identity')
 if not isinstance(source_pins,dict)or not source_pins:raise ValueError('An explicit reviewed projector/decoder source-pin mapping is required')
 pins=source_pins
 for path,expected in pins.items():
  if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:raise ValueError('Pinned projector/decoder changed')
 if not isinstance(f,dict)or not isinstance(f.get('readouts'),dict)or not isinstance(f.get('themeMode'),dict):raise ValueError('Malformed projected state containers')
 for name in [k[0]for k in FIELDS]+UNAVAILABLE:
  if not isinstance(f['readouts'].get(name),dict):raise ValueError('Malformed projected field '+name)
 for name,_,_,_ in FIELDS:
  if not isinstance(f['readouts'][name].get('provenance'),dict):raise ValueError('Malformed field provenance '+name)
 if not isinstance(f['themeMode'].get('provenance',{}),dict):raise ValueError('Malformed theme provenance')
 if f.get('schema')!='f40-offline-display-state-proposal-v1'or f.get('manifestSha256')!='2a7b1e8a5b3e845dd01b344dd91e79e62f46c3b6d59a8f196f9bc8980d97d2c6'or type(f.get('epoch'))is not int or not 1<=f['epoch']<=2147483647:raise ValueError('Invalid exact projected state header')
 if any(f.get(k)is not False for k in ['needleCalibrationVerified','stalenessTimingVerified','nativeRendererBindingImplemented','vehicleCompatibilityVerified','installationAllowed']):raise ValueError('Unreviewed source authority claim')
 if previous and session==previous['producerSession'] and (f['epoch']<previous['epoch']or seq<=previous['stateSequence']):raise ValueError('Old state sequence/epoch')
 values=[];mask=0
 for i,(name,units,maximum,signal) in enumerate(FIELDS):
  field=f['readouts'][name];p=field.get('provenance',{})
  if type(field.get('available'))is not bool or field.get('units')!=units or p.get('signal')!=signal:raise ValueError('Wrong field type/units/provenance '+name)
  value=field.get('value')
  if field['available']:
   if type(value)not in(int,float)or not math.isfinite(value)or not 0<=value<=maximum or p.get('epoch')!=f['epoch']or type(p.get('generation'))is not int or p['generation']<1:raise ValueError('Invalid value/lifetime '+name)
   raw=p.get('raw')
   expected=(raw*.25 if name=='engineRpm'else raw-48 if name=='oilTemperatureC'else raw)if type(raw)is int else None
   if expected!=value or (name=='oilTemperatureC'and not 48<=raw<=254)or(name=='engineRpm'and not 0<=raw<65535):raise ValueError('Raw/projected conversion mismatch '+name)
   mask|=1<<i;values.append(value)
  else:
   if value is not None:raise ValueError('Unavailable must be null')
   values.append(0)
 for name in UNAVAILABLE:
  field=f['readouts'][name]
  if field.get('available')is not False or field.get('value')is not None:raise ValueError('Unsupported semantic source '+name)
 t=f['themeMode'];mode=-1
 if t['available']:
  mode={'COMFORT':0,'SPORT':1,'ECO PRO':2}.get(t['value'],-1)
  if mode<0 or t.get('policy')!='custom-three-mode-family-v1'or t.get('provenance',{}).get('epoch')!=f['epoch']:raise ValueError('Invalid custom theme policy')
 elif t['value']is not None:raise ValueError('Unavailable mode must be null')
 line=' '.join(map(str,[rid,seq,f['epoch'],mask,*values,mode]))
 return {'line':line,'producerSession':session,'stateSequence':seq,'epoch':f['epoch'],'frameSha256':hashlib.sha256(json.dumps(f,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),'sourceAuthenticationVerified':False,'installationAllowed':False}
