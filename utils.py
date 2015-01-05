#!/usr/bin/env python3
# coding=utf-8
__author__ = 'chenfengyuan'
import tornado.gen
import tornado.ioloop
import tornado.httputil
import tornado.httpclient
import traceback
import tornado.log
import os
import shutil
import subprocess
import join_flv
import join_mp4


@tornado.gen.coroutine
def sleep(seconds, ioloop_instance=None):
    if not ioloop_instance:
        ioloop_instance = tornado.ioloop.IOLoop.current()
    yield tornado.gen.Task(ioloop_instance.add_timeout, ioloop_instance.time() + seconds)


@tornado.gen.coroutine
def url_fetch(url):
    max_try_time = 3
    for try_time in range(max_try_time):
        try:
            http = tornado.httpclient.AsyncHTTPClient()
            resp = yield http.fetch(url)
            if resp.code == 200:
                raise tornado.gen.Return(resp)
        except KeyboardInterrupt:
            raise
        except tornado.gen.Return:
            raise
        except:
            if try_time == max_try_time - 1:
                tornado.log.app_log.error(traceback.format_exc())
            pass
    tornado.log.app_log.error('failed to fetch %s' % url)


class FetchError(RuntimeError):
    pass


@tornado.gen.coroutine
def get_redirect(url):
    max_try_time = 3
    for try_time in range(max_try_time):
        try:
            http = tornado.httpclient.AsyncHTTPClient()
            key = object()
            http.fetch(url, callback=(yield tornado.gen.Callback(key)), follow_redirects=False)
            resp = yield tornado.gen.Wait(key)
            if resp.code == 301:
                raise tornado.gen.Return(resp)
            if resp.code == 302:
                raise tornado.gen.Return(resp)
            if resp.code == 200:
                raise tornado.gen.Return(resp)
        except KeyboardInterrupt:
            raise
        except tornado.gen.Return:
            raise
        except:
            if try_time == max_try_time - 1:
                tornado.log.app_log.error(traceback.format_exc())
            pass
    tornado.log.app_log.error(traceback.format_exc())
    tornado.log.app_log.error('failed to fetch %s' % url)
    raise FetchError('failed to fetch %s', url)


class ExistsError(RuntimeError):
    pass


@tornado.gen.coroutine
def download_to_file(path, url):
    out = {'fo': None}

    def on_body(data):
        try:
            if not out['fo']:
                out['fo'] = open(path, 'wb')
            out['fo'].write(data)
        except KeyboardInterrupt:
            raise
        except:
            tornado.log.app_log.error(traceback.format_exc())

    http = tornado.httpclient.AsyncHTTPClient()
    resp = yield get_redirect(url)
    download_url = resp.headers['Location']
    if os.path.exists(path):
        filesize = os.path.getsize(path)
        resp = yield url_fetch(tornado.httpclient.HTTPRequest(download_url, method='HEAD'))
        download_size = int(resp.headers['Content-Length'])
        if filesize != download_size:
            os.remove(path)
        else:
            raise tornado.gen.Return()
    resp = yield http.fetch(download_url, streaming_callback=on_body,
                            request_timeout=0)
    out['fo'].close()
    assert os.path.getsize(path) == int(resp.headers['Content-Length'])


def download_to_file_test():
    import tornado.ioloop
    io = tornado.ioloop.IOLoop.instance()

    @tornado.gen.coroutine
    def dummy():
        yield download_to_file('favicon.ico', 'http://www.solidot.org/favicon.ico')

    io.run_sync(dummy)


def get_video_converter():
    for bin_ in [u'avconv', u'ffmpeg']:
        if shutil.which(bin_):
            return bin_


def merge_videos(video_files, output_basename):
    if 'flv' in video_files[0]:
        join_flv.concat_flv(video_files, output_basename + '.flv')
        converter = get_video_converter()
        if converter:
            p = subprocess.Popen([converter, '-i', output_basename + '.flv', '-c', 'copy', output_basename + '.mp4'])
            p.wait()
            os.remove(output_basename + '.flv')
    elif 'mp4' in video_files[0]:
        try:
            join_mp4.concat_mp4(video_files, output_basename + '.mp4')
        except AssertionError as e:
            if str(e) != 'no enough data':
                raise

if __name__ == '__main__':
    download_to_file_test()

