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


@tornado.gen.coroutine
def url_fetch(url):
    max_try_time = 3
    for try_time in range(max_try_time):
        try:
            http = tornado.httpclient.AsyncHTTPClient()
            resp = yield http.fetch(url)
            if resp.code == 200 and resp.body:
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
                g.LOGGER.error(traceback.format_exc())
            pass
    g.LOGGER.error('failed to fetch %s' % url)
    raise FetchError('failed to fetch %s', url)


class ExistsError(RuntimeError):
    pass


@tornado.gen.coroutine
def download_to_file(path, url):
    out = {'fo': None, 'filesize': None, 'last_received_time': None}

    def on_header(header):
        if out['filesize'] is None:
            return
        if 'Content-Length' not in header:
            return
        download_size = int(header.split(':')[1])
        if out['filesize'] != download_size:
            os.remove(path)
        else:
            raise ExistsError

    def on_body(data):
        try:
            if not out['last_received_time']:
                out['last_received_time'] = tornado.ioloop.IOLoop.current().time()

            if tornado.ioloop.IOLoop.current().time() - out['last_received_time'] > 60:
                raise tornado.httpclient.HTTPError(599, 'Timeout')

            if not out['fo']:
                out['fo'] = open(path, 'wb')
            out['fo'].write(data)
            out['last_received_time'] = tornado.ioloop.IOLoop.current().time()
        except:
            tornado.log.app_log.error(traceback.format_exc())

    if os.path.exists(path):
        out['filesize'] = os.path.getsize(path)

    http = tornado.httpclient.AsyncHTTPClient()
    resp = yield get_redirect(url)
    try:
        yield http.fetch(resp.headers['Location'], header_callback=on_header, streaming_callback=on_body,
                         request_timeout=0)
    except ExistsError:
        pass
    except:
        tornado.log.app_log.error(traceback.format_exc())


def download_to_file_test():
    import tornado.ioloop
    io = tornado.ioloop.IOLoop.instance()

    @tornado.gen.coroutine
    def dummy():
        yield download_to_file('favicon.ico', 'http://www.solidot.org/favicon.ico')

    io.run_sync(dummy)

if __name__ == '__main__':
    download_to_file_test()

