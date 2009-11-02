import __init__
import searchengine

pagelist=[
    'http://en.wikipedia.org/',
    'http://kiwitobes.com/wiki/Perl.html',
    'http://www.linux.org/',
    'http://www.google.com',
    ]
pagelist2 = [
    'http://python.org/',
    'http://www.linux.org/',
    ]

pagelist3 = [
    'http://www.time.com',
    'http://www.cnn.com',
    'http://www.bbc.com'
]
crawler=searchengine.crawler('news.db')
try:
    crawler.createindextables()
except:
    pass
crawler.crawl(pagelist3)
