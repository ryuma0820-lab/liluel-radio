import importlib.util
from pathlib import Path
import unittest

mod_path = Path(__file__).parents[1] / 'tools/liluel_daily.py'
spec = importlib.util.spec_from_file_location('liluel_daily',mod_path)
radio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(radio)

class TestDailyRadio(unittest.TestCase):
    def test_secure_url(self):
        self.assertEqual(radio.url_key('https://Example.com/x?id=7'), 'https://example.com/x')
        self.assertEqual(radio.url_key('http://example.com'), '')
        self.assertEqual(radio.url_key('file:///etc/passwd'), '')
        self.assertEqual(radio.url_key('https://127.0.0.1:8000/a'), '')
    def test_extract_web_sources(self):
        resp = {'output':[{'type':'web_search_call','action':{'sources':[{'url':'https://news.example.com/a'}]}},
                          {'type':'message','content':[{'annotations':[{'type':'url_citation','url':'https://x.com/a/status/4'}]}]}]}
        self.assertEqual(radio.source_urls(resp), ['https://news.example.com/a','https://x.com/a/status/4'])
    def test_filter_fabricated_source(self):
        item = lambda url: {'label':'見出し','points':['根拠あり'],
                            'lines':[{'say':'テストです','show':'テストです'}], 'url':url,'category':'media'}
        doc={'title':'テスト', 'opening':[{'say':'a','show':'a'}],
             'closing':[{'say':'z','show':'z'}],
             'news':[item('https://example.com/real'),item('https://example.com/fake')]}
        out=radio.validate_script(doc, ['https://example.com/real'], strict=False)
        self.assertEqual(len(out['news']),1)

if __name__ == '__main__':
    unittest.main()

class TestAudioTiming(unittest.TestCase):
    def test_audio_timestamps_match_generated_mp3(self):
        from pydub import AudioSegment
        import io
        sample=io.BytesIO()
        AudioSegment.silent(duration=390,frame_rate=44100).export(sample,format='mp3')
        orig=radio.elevenlabs_speech
        try:
            radio.elevenlabs_speech=lambda *args:sample.getvalue()
            s={'date':'2026-11-06','title':'テスト','opening':[{'say':'a','show':'A'}],
               'news':[{'label':'テスト','points':['テスト'],
                        'lines':[{'say':'b','show':'B'}], 'url':'https://example.com/a','category':'media'}],
               'closing':[{'say':'c','show':'C'}]}
            mp3, completed=radio.make_audio_and_timing(s,'fake','voice')
            self.assertGreater(len(mp3),1000)
            self.assertEqual(len(completed['lines_timed']),3)
            self.assertEqual(len(completed['segments']),3)
            self.assertEqual([x['part'] for x in completed['lines_timed']], [0,1,2])
            self.assertLess(completed['lines_timed'][-1]['end'], completed['seconds'])
            self.assertEqual(completed['format'], 'monoradio/news-1')
        finally:
            radio.elevenlabs_speech=orig
