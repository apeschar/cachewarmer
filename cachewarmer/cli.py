import sys
from argparse import ArgumentParser

import requests
from lxml import etree
from urllib.parse import urljoin, urlparse, urlunparse


def main():
    parser = ArgumentParser()
    parser.add_argument('--url', '-u', required=True)
    parser.add_argument('--max-depth', '-d', type=int, default=2)
    parser.add_argument('--exclude', '-e', action='append')
    args = parser.parse_args()

    ignored = set()

    while True:
        session = requests.Session()
        seen = set()
        queue = [Request(args.url, depth=0)]
        while queue:
            request = queue.pop(0)
            if request.url in ignored or request.url in seen:
                continue
            if request.depth > args.max_depth:
                continue
            print('[%d] %s' % (request.depth, request.url), file=sys.stderr)
            seen.add(request.url)
            with session.get(request.url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
            }, stream=True) as resp:
                if len(resp.text) > 1024**2:
                    print("Response is too large, ignoring:", request.url)
                    ignored.add(request.url)
                    continue
                if not is_cachable(resp):
                    print("Page is not cachable, ignoring:", request.url)
                    ignored.add(request.url)
                root = etree.HTML(resp.text)
            for link in links(root, resp.url):
                if is_excluded(args.exclude, link):
                    continue
                queue.append(Request(link, depth=request.depth + 1))


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
