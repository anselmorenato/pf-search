import __init__
from searchengine.crawler import crawler,mtcrawler

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
    'http://www.cnn.com',
    'http://www.bbc.com',
    'http://usatoday.com/',
    'http://www.timesonline.co.uk/',
    'http://www.csmonitor.com/',
    'http://abcnews.go.com/',
    'http://www.time.com',
    'http://www.salon.com/',
    'http://www.dailytelegraph.co.uk/',
    'http://www.nationalreview.com/',
    'http://www.forbes.com/',
]
#crawler=crawler('data/news.db')
# crawler = searchengine.crawler('searchindex.db')
#try:
#    crawler.createindextables()
#except:
#    raise
#    pass

mtcrawler(pages=pagelist3, dbuser='root', dbpasswd='emerald').start()

