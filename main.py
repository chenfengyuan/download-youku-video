#!/usr/bin/env python3
# coding=utf-8
__author__ = 'chenfengyuan'
import tornado.gen
import tornado.log
import tornado.ioloop
import tornado.options
import youku
import sys
import os
import utils
import tqdm
import math
import decimal
import tornado.httpclient


def main():
    tornado.options.parse_config_file('/dev/null')
    tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    io = tornado.ioloop.IOLoop.instance()

    @tornado.gen.coroutine
    def dummy():
        for raw_url in sys.argv[1:]:
            for url in (yield youku.Youku.get_videos(raw_url)):
                data = yield youku.Youku.get_video_name_and_download_urls(url)
                directory = data[0].replace('/', '_')
                if os.path.exists(os.path.join(directory, '.finished')):
                    continue
                tornado.log.app_log.info('download %s' % directory)
                urls = data[1]
                if not os.path.exists(directory):
                    os.mkdir(directory)
                process = tqdm.tqdm(range(len(urls)), leave=True, mininterval=0)
                template = '%%0%dd.flv' % math.ceil(decimal.Decimal(len(urls)).log10())
                for i, durl in enumerate(urls):
                    try:
                        next(process)
                    except StopIteration:
                        pass
                    path = os.path.join(directory, template % i)
                    # try:
                    #     os.remove(path)
                    # except KeyboardInterrupt:
                    #     raise
                    # except:
                    #     pass
                    # data = yield utils.url_fetch(durl)
                    # open(path, 'bw').write(data.body)
                    yield utils.download_to_file(path, durl)
                else:
                    try:
                        next(process)
                    except StopIteration:
                        pass
                    sys.stderr.write('\n')
                    open(os.path.join(directory, '.finished'), 'w')
    io.run_sync(dummy)


if __name__ == '__main__':
    main()
