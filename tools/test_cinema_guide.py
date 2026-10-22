"""Cinema-only regression checks; offline and without an AI service."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest
import update_cinema_guide as guide

class CinemaGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # A fixed regression fixture, independent of future real programmes.
        cls.data={'period_start':'2026-10-21','period_end':'2026-11-10','verified_on':'2026-10-22','source_pdf':'https://documents.monnaie-services.com/site_file/EMS0177/test.pdf','films':[
            {'title':'Film de contrôle','description':'Fixture de test uniquement.','duration':'','sessions':[{'date':'2026-10-23','time':'19:00','version':'VF'},{'date':'2026-10-23','time':'20:00','version':'VF'},{'date':'2026-10-25','time':'17:00','version':'VF'}]},
            {'title':'Quelques mots d’amour','description':'Fixture de régression de la transcription.','duration':'','sessions':[{'date':'2026-10-28','time':'11:00','version':'VF'},{'date':'2026-11-03','time':'14:30','version':'VF'},{'date':'2026-11-03','time':'16:30','version':'VF'},{'date':'2026-11-03','time':'18:30','version':'VF'}]}
        ]}

    def test_same_day_expired_sessions_are_removed(self):
        now=datetime(2026,10,23,19,30,tzinfo=guide.TZ)
        films=guide.future_films(self.data,now)
        self.assertTrue(films)
        self.assertTrue(all(guide.stamp(s)>now for _,ss in films for s in ss))
        first=[guide.stamp(ss[0]) for _,ss in films]
        self.assertEqual(first,sorted(first))

    def test_daylight_saving_preserves_local_wall_time(self):
        a=guide.stamp({'date':'2026-10-24','time':'17:00'})
        b=guide.stamp({'date':'2026-10-25','time':'17:00'})
        self.assertEqual(a.astimezone(timezone.utc).hour,15)
        self.assertEqual(b.astimezone(timezone.utc).hour,16)
        self.assertEqual(a.hour,b.hour)

    def test_expired_programme_has_no_films_or_current_pdf(self):
        now=datetime(2026,11,11,0,1,tzinfo=guide.TZ)
        self.assertEqual(guide.future_films(self.data,now),[])
        page=guide.render(self.data,now)
        self.assertIn('class="cg-current" hidden',page)
        self.assertIn('class="cg-pdf" hidden',page)
        self.assertNotIn('class="cg-film"',page)
        self.assertIn('prochain programme vérifié',page)

    def test_duplicate_or_outside_period_rejected(self):
        for change in ['duplicate','date']:
            data=copy.deepcopy(self.data)
            f=data['films'][-1]
            if change=='duplicate':f['sessions'].append(dict(f['sessions'][0]))
            else:f['sessions'][0]['date']='2027-01-01'
            with self.assertRaises(ValueError):guide.validate(data)

    def test_stable_canonical_routes(self):
        f=next(f for f in self.data['films'] if f['title']=='Quelques mots d’amour')
        self.assertEqual(guide.film_url(f),'https://agenda.vivreanyons.fr/evenements/cinema-quelques-mots-damour-2026-10-28/')
        self.assertIn('2026-10-28',guide.film_url(f))

    def test_documented_transcription_correction(self):
        f=next(f for f in self.data['films'] if f['title']=='Quelques mots d’amour')
        ss=[s['time'] for s in f['sessions'] if s['date']=='2026-11-03']
        self.assertEqual(ss,['14:30','16:30','18:30'])

if __name__=='__main__':unittest.main()

