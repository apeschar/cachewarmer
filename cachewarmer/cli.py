import sys
import time
from argparse import ArgumentParser

import requests
from lxml import etree
from urllib.parse import urljoin, urlparse, urlunparse


def main():
    parser = ArgumentParser()
    parser.add_argument('--url', '-u', required=True)
    parser.add_argument('--max-depth', '-d', type=int, default=2)
    parser.add_argument('--exclude', '-e', action='append')
    parser.add_argument('--delay', '-D', type=float, default=0)
    args = parser.parse_args()

    ignored = set()

    while True:
        if ignored:
            ignored.pop()
        session = requests.Session()
        seen = set()
        queue = [Request(args.url, depth=0)]
        start_time = None
        while queue:
            request = queue.pop(0)
            if request.url in ignored or request.url in seen:
                continue
            if request.depth > args.max_depth:
                continue
            seen.add(request.url)
            if start_time is not None:
                time.sleep(max(0, start_time + args.delay - time.monotonic()))
            start_time = time.monotonic()
            with session.get(request.url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
            }, stream=True) as resp:
                hit = 'HIT' in resp.headers.get('x-cache', '')
                log('[%d] %s %s' % (request.depth, 'HIT' if hit else 'MISS', request.url))
                if len(resp.text) > 1024**2:
                    log("Response is too large, ignoring:", request.url)
                    ignored.add(request.url)
                    continue
                if not is_cachable(resp):
                    log("Page is not cachable, ignoring:", request.url)
                    ignored.add(request.url)
                    continue
                root = etree.HTML(resp.text)
            for link in links(root, resp.url):
                if is_excluded(args.exclude, link):
                    continue
                queue.append(Request(link, depth=request.depth + 1))


def log(*args):
    print(*args, file=sys.stderr)
    sys.stderr.flush()


def links(root, base_url):
    urls = set()
    for a in root.xpath('//a'):
        if not a.get('href'):
            continue
        url = urljoin(base_url, a.get('href'))
        if urljoin(url, '/') != urljoin(base_url, '/'):
            continue
        url = urlunparse(urlparse(url)._replace(fragment=''))
        urls.add(url)
    return urls


def is_cachable(resp):
    cache_control = {v.strip().lower() for v in resp.headers.get('cache-control', '').split(',')}
    return 'no-cache' not in cache_control


def is_excluded(patterns, url):
    for pattern in patterns:
        if pattern in url:
            return True
    return False


class Request:

    def __init__(self, url, *, depth):
        self.url = url
        self.depth = depth


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupt", file=sys.stderr)
        sys.exit(1)
