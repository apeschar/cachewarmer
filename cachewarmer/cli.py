import sys
from argparse import ArgumentParser

import requests
from lxml import etree
from urllib.parse import urljoin, urlparse, urlunparse


def main():
    parser = ArgumentParser()
    parser.add_argument('--url', '-u', required=True)
    parser.add_argument('--max-depth', '-d', type=int, default=2)
    args = parser.parse_args()

    ignored = set()

    while True:
        session = requests.Session()
        seen = set()
        queue = [Request(args.url, depth=0)]
        while queue:
            request = queue.pop(0)
            print('[%d] %s' % (request.depth, request.url), file=sys.stderr)
            seen.add(request.url)
            resp = session.get(request.url, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0',
            })
            if not is_cachable(resp):
                print("Page is not cachable, ignoring:", request.url)
                ignored.add(request.url)
            root = etree.HTML(resp.text)
            for link in links(root, resp.url):
                if link in ignored or link in seen:
                    continue
                if request.depth < args.max_depth:
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


class Request:

    def __init__(self, url, *, depth):
        self.url = url
        self.depth = depth


if __name__ == '__main__':
    main()
