#!/usr/bin/env python3
# coding=utf-8
__author__ = 'chenfengyuan'
import tornado.gen
import re
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
import join_flv
import join_mp4
import shutil
import argparse


def main():
    parser = argparse.ArgumentParser(description='download youku videos')
    parser.add_argument('urls', type=str, nargs='+',
                        help='urls to download')
    parser.add_argument('--skip', type=int, help='skip first n urls', default=0)
    args = parser.parse_args()
    tornado.options.parse_config_file('/dev/null')
    tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    io = tornado.ioloop.IOLoop.instance()

    @tornado.gen.coroutine
    def dummy():
        skipped = 0
        for raw_url in args.urls:
            for url in (yield youku.Youku.get_videos(raw_url)):
                skipped += 1
                if skipped <= args.skip:
                    continue
                data = yield youku.Youku.get_video_name_and_download_urls(url)
                directory = data[0].replace('/', '_')
                output_file = '%s.flv' % directory
                if os.path.exists(output_file):
                    continue
                print('Downloading %s' % directory)
                urls = data[1]
                if not os.path.exists(directory):
                    os.mkdir(directory)
                process = tqdm.tqdm(range(len(urls)), leave=True, mininterval=0)
                template = '%%0%dd.%%s' % math.ceil(decimal.Decimal(len(urls)).log10())
                video_files = []
                for i, durl in enumerate(urls):
                    file_suffix = re.search(r'st/(\w+)/fileid', durl).group(1)
                    try:
                        next(process)
                    except StopIteration:
                        pass
                    path = os.path.join(directory, template % ((i + 1), file_suffix))
                    video_files.append(path)
                    yield utils.download_to_file(path, durl)
                else:
                    try:
                        next(process)
                    except StopIteration:
                        pass
                    if 'flv' in video_files[0]:
                        join_flv.concat_flv(video_files, output_file)
                    elif 'mp4' in video_files[0]:
                        try:
                            join_mp4.concat_mp4(video_files, output_file)
                        except AssertionError as e:
                            if str(e) != 'no enough data':
                                raise
                    shutil.rmtree(directory)
                    sys.stderr.write('\n')
    io.run_sync(dummy)


if __name__ == '__main__':
    main()
