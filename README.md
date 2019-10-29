Crawl a site, following links to depth 1.  That is, crawl each page linked on a
page that is linked to from the start page.

~~~
python -m cachewarmer.cli --url https://www.mysite.com --depth 2
~~~

This will run forever, keeping pages warm.  Responses with `Cache-Control:
nocache` will cause that URL to be added to an in-memory blacklist to avoid
useless requests.
