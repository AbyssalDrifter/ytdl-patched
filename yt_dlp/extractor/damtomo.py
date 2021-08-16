# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError, clean_html, int_or_none, try_get
from ..compat import compat_str


class DamtomoVideoIE(InfoExtractor):
    IE_NAME = 'damtomo:video'
    _VALID_URL = r'https?://(www\.)?clubdam\.com/app/damtomo/(?:SP/)?karaokeMovie/StreamingDkm\.do\?karaokeMovieId=(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.clubdam.com/app/damtomo/karaokeMovie/StreamingDkm.do?karaokeMovieId=2414316',
        'info_dict': {
            'id': '2414316',
            'uploader': 'Ｋドロン',
            'uploader_id': 'ODk5NTQwMzQ',
            'song_title': 'Get Wild',
            'song_artist': 'TM NETWORK(TMN)',
            'upload_date': '20201226',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, handle = self._download_webpage_handle(
            'https://www.clubdam.com/app/damtomo/karaokeMovie/StreamingDkm.do?karaokeMovieId=%s' % video_id, video_id,
            encoding='sjis')

        if handle.url == 'https://www.clubdam.com/sorry/':
            raise ExtractorError('You are rate-limited. Try again later.', expected=True)
        if '<h2>予期せぬエラーが発生しました。</h2>' in webpage:
            raise ExtractorError('There is an error on server-side. Try again later.', expected=True)

        # NOTE: there is excessive amount of spaces and line breaks, so ignore spaces around these part
        description = self._search_regex(r'(?m)<div id="public_comment">\s*<p>\s*([^<]*?)\s*</p>', webpage, 'description', default=None)
        uploader_id = self._search_regex(r'<a href="https://www\.clubdam\.com/app/damtomo/member/info/Profile\.do\?damtomoId=([^"]+)"', webpage, 'uploader_id', default=None)

        # cleaner way to extract information in HTML
        # example content: https://gist.github.com/nao20010128nao/1d419cc9ca3177be134094addf28ab51
        data_dict = {g.group(2): clean_html(g.group(3)) for g in re.finditer(r'(?s)<(p|div)\s+class="([^" ]+?)">(.+?)</\1>', webpage)}
        data_dict = {k: re.sub(r'\s+', ' ', v) for k, v in data_dict.items() if v}
        # print(json.dumps(data_dict))

        # since videos do not have title, name the video like '%(song_title)s-%(song_artist)s-%(uploader)s' for convenience
        data_dict['user_name'] = re.sub(r'\s*さん\s*$', '', data_dict['user_name'])
        title = '%(song_title)s-%(song_artist)s-%(user_name)s' % data_dict

        stream_tree = self._download_xml(
            'https://www.clubdam.com/app/damtomo/karaokeMovie/GetStreamingDkmUrlXML.do?movieSelectFlg=2&karaokeMovieId=%s' % video_id, video_id,
            note='Requesting stream information', encoding='sjis')
        m3u8_url = try_get(stream_tree, lambda x: x.find(
            './/d:streamingUrl',
            {'d': 'https://www.clubdam.com/app/damtomo/karaokeMovie/GetStreamingDkmUrlXML'}).text.strip(), compat_str)
        if not m3u8_url:
            raise ExtractorError('Failed to obtain m3u8 URL')

        return {
            'id': video_id,
            'title': title,
            'uploader_id': uploader_id,
            'description': description,
            'formats': [{
                'format_id': 'hls',
                'url': m3u8_url,
                'ext': 'mp4',
                'protocol': 'm3u8_native',
            }],
            'uploader': data_dict['user_name'],
            'upload_date': try_get(data_dict, lambda x: self._search_regex(r'(\d\d\d\d/\d\d/\d\d)', x['date'], 'upload_date', default=None).replace('/', ''), compat_str),
            'view_count': int_or_none(self._search_regex(r'(\d+)', data_dict['audience'], 'view_count', default=None)),
            'like_count': int_or_none(self._search_regex(r'(\d+)', data_dict['nice'], 'like_count', default=None)),
            'song_title': data_dict['song_title'],
            'song_artist': data_dict['song_artist'],
        }


class DamtomoRecordIE(InfoExtractor):
    IE_NAME = 'damtomo:record'
    _VALID_URL = r'https?://(www\.)?clubdam\.com/app/damtomo/(?:SP/)?karaokePost/StreamingKrk\.do\?karaokeContributeId=(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.clubdam.com/app/damtomo/karaokePost/StreamingKrk.do?karaokeContributeId=27376862',
        'info_dict': {
            'id': '27376862',
            'title': 'イカSUMMER [良音]-ORANGE RANGE-ＮＡＮＡ',
            'description': None,
            'uploader': 'ＮＡＮＡ',
            'uploader_id': 'MzAyMDExNTY',
            'upload_date': '20210721',
            'view_count': 4,
            'like_count': 1,
            'song_title': 'イカSUMMER [良音]',
            'song_artist': 'ORANGE RANGE',
        }
    }, {
        'url': 'https://www.clubdam.com/app/damtomo/karaokePost/StreamingKrk.do?karaokeContributeId=27489418',
        'info_dict': {
            'id': '27489418',
            'title': '心みだれて〜say it with flowers〜(生音)-小林明子-箱の「中の人」',
            'uploader_id': 'NjI1MjI2MjU',
            'description': 'やっぱりキーを下げて正解だった感じ。リベンジ成功ということで。',
            'uploader': '箱の「中の人」',
            'upload_date': '20210815',
            'view_count': 5,
            'like_count': 3,
            'song_title': '心みだれて〜say it with flowers〜(生音)',
            'song_artist': '小林明子',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, handle = self._download_webpage_handle(
            'https://www.clubdam.com/app/damtomo/karaokePost/StreamingKrk.do?karaokeContributeId=%s' % video_id, video_id,
            encoding='sjis')

        if handle.url == 'https://www.clubdam.com/sorry/':
            raise ExtractorError('You are rate-limited. Try again later.', expected=True)
        if '<h2>予期せぬエラーが発生しました。</h2>' in webpage:
            raise ExtractorError('There is an error on server-side. Try again later.', expected=True)

        # NOTE: there is excessive amount of spaces and line breaks, so ignore spaces around these part
        description = self._search_regex(r'(?m)<div id="public_comment">\s*<p>\s*([^<]*?)\s*</p>', webpage, 'description', default=None)
        uploader_id = self._search_regex(r'<a href="https://www\.clubdam\.com/app/damtomo/member/info/Profile\.do\?damtomoId=([^"]+)"', webpage, 'uploader_id', default=None)

        # cleaner way to extract information in HTML
        # example content: https://gist.github.com/nao20010128nao/1d419cc9ca3177be134094addf28ab51
        data_dict = {g.group(2): clean_html(g.group(3)) for g in re.finditer(r'(?s)<(p|div)\s+class="([^" ]+?)">(.+?)</\1>', webpage)}
        data_dict = {k: re.sub(r'\s+', ' ', v) for k, v in data_dict.items() if v}
        # print(json.dumps(data_dict))

        # since videos do not have title, name the video like '%(song_title)s-%(song_artist)s-%(uploader)s' for convenience
        data_dict['user_name'] = re.sub(r'\s*さん\s*$', '', data_dict['user_name'])
        title = '%(song_title)s-%(song_artist)s-%(user_name)s' % data_dict

        stream_tree = self._download_xml(
            'https://www.clubdam.com/app/damtomo/karaokePost/GetStreamingKrkUrlXML.do?karaokeContributeId=%s' % video_id, video_id,
            note='Requesting stream information', encoding='sjis')
        m3u8_url = try_get(stream_tree, lambda x: x.find(
            './/d:streamingUrl',
            {'d': 'https://www.clubdam.com/app/damtomo/karaokePost/GetStreamingKrkUrlXML'}).text.strip(), compat_str)
        if not m3u8_url:
            raise ExtractorError('Failed to obtain m3u8 URL')

        return {
            'id': video_id,
            'title': title,
            'uploader_id': uploader_id,
            'description': description,
            'formats': [{
                'format_id': 'hls',
                'url': m3u8_url,
                'ext': 'mp4',
                'protocol': 'm3u8_native',
            }],
            'uploader': data_dict['user_name'],
            'upload_date': try_get(data_dict, lambda x: self._search_regex(r'(\d\d\d\d/\d\d/\d\d)', x['date'], 'upload_date', default=None).replace('/', ''), compat_str),
            'view_count': int_or_none(self._search_regex(r'(\d+)', data_dict['audience'], 'view_count', default=None)),
            'like_count': int_or_none(self._search_regex(r'(\d+)', data_dict['nice'], 'like_count', default=None)),
            'song_title': data_dict['song_title'],
            'song_artist': data_dict['song_artist'],
        }
