from update_bus_schedules import parse_gtfs,seconds,refresh
import unittest,zipfile,io,csv,json,tempfile
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone,timedelta

def archive(tables):
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w') as z:
        for name,(headers,rows) in tables.items():
            s=io.StringIO();w=csv.writer(s);w.writerow(headers);w.writerows(rows);z.writestr(name,s.getvalue())
    return buffer.getvalue()
class Schedules(unittest.TestCase):
    def test_public_services_and_calendar_exceptions(self):
        body=archive({
          'routes.txt':(['route_id','route_short_name','route_long_name'],[['r','D36','Nyons Montelimar'],['school','26-25026','SCO Nyons']]),
          'trips.txt':(['route_id','service_id','trip_id'],[['r','s','t'],['school','s','sco']]),
          'stops.txt':(['stop_id','stop_name','location_type'],[['FR:26220:ZE:1:DROME','Halte','0'],['FR:26198:ZE:2:DROME','Gare','0']]),
          'stop_times.txt':(['trip_id','stop_id','stop_sequence','arrival_time','departure_time','pickup_type','drop_off_type'],[['t','FR:26220:ZE:1:DROME',1,'08:00:00','08:00:00',0,1],['t','FR:26198:ZE:2:DROME',2,'09:00:00','09:00:00',1,0],['sco','FR:26220:ZE:1:DROME',1,'08:00:00','08:00:00',0,1]]),
          'calendar_dates.txt':(['service_id','date','exception_type'],[['s','20261010',1],['s','20261011',2]])})
        result=parse_gtfs(body,'drome',{'26220':'Nyons','26198':'Montelimar'})
        self.assertEqual(len(result['trips']),1);self.assertEqual(result['services']['drome:s']['added'],['20261010']);self.assertEqual(result['services']['drome:s']['removed'],['20261011'])
        self.assertEqual(result['trips'][0]['stops'][1][3],1)
    def test_time_validation(self):
        self.assertEqual(seconds('24:30:00'),88200);self.assertIsNone(seconds('12:65:00'));self.assertIsNone(seconds(''));self.assertIsNone(seconds('garbage'))
    def test_independent_outage_and_expired_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'assets').mkdir()
            old={'sources':{'drome':{'status':'available','checkedAt':datetime.now(timezone.utc).isoformat(),'label':'Drôme'},'zou':{'status':'available','checkedAt':(datetime.now(timezone.utc)-timedelta(days=4)).isoformat()}},'routes':{'drome:r':{},'zou:r':{}},'stops':{'drome:n':{'cityCode':'26220','city':'Nyons'}},'services':{'drome:s':{},'zou:s':{}},'trips':[{'id':'drome:t'},{'id':'zou:t'}]}
            (root/'assets/bus-nyons.json').write_text(json.dumps(old))
            with patch('update_bus_schedules.fetch',side_effect=OSError('offline')):refresh(root)
            result=json.loads((root/'assets/bus-nyons.json').read_text())
            self.assertEqual(result['sources']['drome']['status'],'cached');self.assertEqual(result['sources']['zou']['status'],'unavailable');self.assertEqual(result['trips'],[{'id':'drome:t'}])
            self.assertEqual(result['sources']['drome']['checkedAt'],old['sources']['drome']['checkedAt'])
            self.assertEqual((root/'assets/bus-nyons.json').read_bytes(),(root/'vivreanyons-test/assets/bus-nyons.json').read_bytes())
if __name__=='__main__':unittest.main()
