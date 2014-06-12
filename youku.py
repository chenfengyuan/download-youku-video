#!/usr/bin/env python3
# coding=utf-8
__author__ = 'chenfengyuan'

import tornado.gen
import urllib.parse
import tornado.log
import tornado.ioloop
import traceback
import re
import utils
from bs4 import BeautifulSoup


class Youku:

    @staticmethod
    @tornado.gen.coroutine
    def get_video_urls_from_show_id(show_id):
        template = 'http://www.youku.com/show_episode/id_%s.html?dt=json&divid=reload_%s'
        start = 1
        videos = []
        while True:
            content = yield utils.url_fetch(template % (show_id, start))
            soup = BeautifulSoup(content.body)
            videos_tmp = [x['href'] for x in soup.find_all('a')]
            if len(videos_tmp) == 0:
                break
            start += len(videos_tmp)
            videos += videos_tmp
        raise tornado.gen.Return(videos)

    @classmethod
    @tornado.gen.coroutine
    def get_videos(cls, url):
        try:
            if re.search('show_page', url):
                show_id = re.search(r'id_(\w+)\.html',
                                    url).group(1)
                videos = yield cls.get_video_urls_from_show_id(show_id)
                raise tornado.gen.Return(videos)
            raise tornado.gen.Return([url])
        except (KeyboardInterrupt, tornado.gen.Return):
            raise
        except:
            tornado.log.app_log.error(traceback.format_exc())
            raise tornado.gen.Return([])

    @staticmethod
    @tornado.gen.coroutine
    def get_video_download_url(video_or_soup):
        try:
            if isinstance(video_or_soup, BeautifulSoup):
                soup = video_or_soup
            else:
                template = 'http://www.flvcd.com/parse.php?&format=super&kw=%s'
                content = yield utils.url_fetch(template % urllib.parse.quote_plus(video_or_soup))
                soup = BeautifulSoup(content.body)
            urls = [x['href'] for x in soup.find_all('a', href=re.compile('getFlvPath'))]
            raise tornado.gen.Return(urls)
        except (KeyboardInterrupt, tornado.gen.Return):
            raise
        except:
            tornado.log.app_log.error(traceback.format_exc())
            raise tornado.gen.Return([])

    @staticmethod
    @tornado.gen.coroutine
    def get_video_name(video_or_soup):
        try:
            if isinstance(video_or_soup, BeautifulSoup):
                soup = video_or_soup
            else:
                template = 'http://www.flvcd.com/parse.php?&format=super&kw=%s'
                content = yield utils.url_fetch(template % urllib.parse.quote_plus(video_or_soup))
                soup = BeautifulSoup(content.body)
            raise tornado.gen.Return(list(soup.find_all(class_='mn STYLE4')[1].children)
                                     [2].strip())
        except (KeyboardInterrupt, tornado.gen.Return):
            raise
        except:
            tornado.log.app_log.error(traceback.format_exc())

    @classmethod
    @tornado.gen.coroutine
    def get_video_name_and_download_urls(cls, video_or_soup):
        try:
            if isinstance(video_or_soup, BeautifulSoup):
                soup = video_or_soup
            else:
                template = 'http://www.flvcd.com/parse.php?&format=super&kw=%s'
                content = yield utils.url_fetch(template % urllib.parse.quote_plus(video_or_soup))
                soup = BeautifulSoup(content.body)
            name = yield cls.get_video_name(soup)
            download_urls = yield cls.get_video_download_url(soup)
            raise tornado.gen.Return((name, download_urls))
        except (KeyboardInterrupt, tornado.gen.Return):
            raise
        except:
            tornado.log.app_log.error(traceback.format_exc())


class YoukuTest:
    @staticmethod
    def get_video_urls_from_show_id():
        io = tornado.ioloop.IOLoop.instance()
        show_id = 'zcbfd4dee962411de83b1'

        @tornado.gen.coroutine
        def dummy():
            yield Youku.get_video_urls_from_show_id(show_id)

        io.run_sync(dummy)

    @staticmethod
    def get_videos():
        io = tornado.ioloop.IOLoop.instance()

        @tornado.gen.coroutine
        def dummy():
            data = yield Youku.get_videos('http://www.youku.com/show_page/id_zcbfd4dee962411de83b1.html')
            print(data)
            data = yield Youku.get_videos('http://v.youku.com/v_show/id_XNDExNTg1NTcy.html')
            print(data)

        io.run_sync(dummy)

    @staticmethod
    def get_video_download_url():
        io = tornado.ioloop.IOLoop.instance()
        tornado.log.app_log.error('foo')

        @tornado.gen.coroutine
        def dummy():
            template = 'http://www.flvcd.com/parse.php?&format=super&kw=%s'
            content = yield utils.url_fetch(template %
                                            urllib.parse.quote_plus('http://v.youku.com/v_show/id_XNDExNTg1NTcy.html'))
            soup = BeautifulSoup(content.body)
            data = yield Youku.get_video_download_url(soup)
            print(data)
            data = yield Youku.get_video_name(soup)
            print(data)
        io.run_sync(dummy)

if __name__ == '__main__':
    #YoukuTest.get_video_urls_from_show_id()
    #YoukuTest.get_videos()
    YoukuTest.get_video_download_url()
