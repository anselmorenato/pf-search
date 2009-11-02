import urllib2
import re
import lxml.html
from lxml.html import tostring
from lxml.html.clean import Cleaner
from urlparse import urljoin


from pysqlite2 import dbapi2 as sqlite


ignorewords = set(['the','of','to','and','a','in','is','it'])


class crawler:
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

    def dbcommit(self):
        self.con.commit()

    def getentryid(self,table,field,value,createnew=True):
        cur = self.con.execute(
            "select rowid from %s where %s = '%s'" % (table, field, value))
        res = cur.fetchone()
        if res == None:
            cur=self.con.execute(
                "insert into %s (%s) values ('%s')" % (table, field, value))
            return cur.lastrowid
        else:
            return res[0]

    # Add word and url to wordlocation schame
    def addtoindex(self, url, soup):
        if self.isindexed(url) : return
        print 'Indexing %s' % url

        # fetch words
        text = self.gettextonly(soup)
        words = self.separatewords(text)

        # get url's id
        urlid = self.getentryid('urllist', 'url', url)

        # make every word related
        for i in range(len(words)):
            word = words[i]
            if word in ignorewords: continue
            wordid = self.getentryid('wordlist', 'word', word);
            self.con.execute("insert into wordlocation(urlid,wordid,location) values (%d, %d, %d)"
                             % (urlid,wordid, i))
        
    
    def gettextonly(self, tree):
        cleaner = Cleaner(style=True, links=True, add_nofollow=True,
                          page_structure=False, safe_attrs_only=False)

        
        try:
            v = tostring(tree,method='text',encoding=unicode)
        except:
            v = None
            
        if v == None:
            c = lxml.html.tostring(tree)
            print 'v== null' 
#            resulttext = ''
#            for t in c:
#                subtext = self.gettextonly(t)
#                resulttext += subtext + '\n'
#            return resulttext
            return c
        else:
            # Clean up the javascript and comment.
            try:
                v = cleaner.clean_html(v)
            except:
                # Ignore clean error
                pass
            return v.strip()
        
    
    def separatewords(self, text):
        splitter=re.compile('\\W*')
        return [s.lower() for s in splitter.split(text) if s != '']

    def isindexed(self, url):
        u = self.con.execute \
            ("select rowid from urllist where url='%s'" % url).fetchone()
        if u != None:
            v = self.con.execute(
                'select * from wordlocation where urlid=%d' % u[0]).fetchone()
            if v!= None: return True
        else :
            return False

    def addlinkref(self, urlFrom, urlTo, linkText):
       # print "add link ref From:%s To:%s" % (urlFrom, urlTo)
        pass

    def setupurlrequest(self,url):
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        headers = { 'User-Agent' : user_agent }
        #req = urllib2.Request(url, '', headers)
        req = urllib2.Request(url)
        return req

    def crawl (self, pages, depth=2):
        for i in range(depth):
            newpages = set()
            for page in pages:
                print "Opening %s" % page

                try:
                    node = urllib2.urlopen(page, timeout=30)
                except urllib2.HTTPError, msg:
                    print "%s  %s" % (page, msg)
                    continue
                except urllib2.URLError, msg:
                    print "%s %s" % (page, msg)
                    continue
                except:
                    print "%s cann't open" % page
                    raise
                
                try:
                    tree = lxml.html.parse(node)
                except IOError, msg:
                    print msg
                    print "Please Check Your Network"
                
                    

                self.addtoindex(page,tree)
                links = tree.findall('.//a')
                for link in links:
                    if ('href' in dict(link.attrib)):
                        url = urljoin(page, link.attrib['href'])
                        if url.find("'") != -1: continue
                        url = url.split('#')[0]
                        if url[0:4] == 'http' and not self.isindexed(url):
                            newpages.add(url)
                         #   print 'adding %s' % url
                        linkText = link.text
                        # This should be the title of link
                        self.addlinkref(page,url,linkText)
                self.dbcommit()
            pages = newpages


    def createindextables(self):
        self.con.execute('create table urllist(url)')
        self.con.execute('create table wordlist(word)')
        self.con.execute('create table wordlocation(urlid,wordid,location)')
        self.con.execute('create table link(fromid integer, toid integer)')
        self.con.execute('create table linkwords(wordid,linkid)')
        self.con.execute('create index wordidx on wordlist(word)')
        self.con.execute('create index urlidx on urllist(url)')
        self.con.execute('create index wordurlidx on wordlocation(wordid)')
        self.con.execute('create index urltoidx on link(toid)')
        self.con.execute('create index urlfromidx on link(fromid)')
        self.dbcommit()
        
    

class searcher:
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()
        
    def getmatchrows(self, q):
        # construct query strings
        fieldlist = 'w0.urlid'
        tablelist = ''
        clauselist = ''
        wordids = []

        #split words
        words = q.split(' ')
        tablenumber = 0

        for word in words:
            # fetch word id
            wordrow = self.con.execute(
                "select rowid from wordlist where word='%s'" % word).fetchone()
            if wordrow != None:
                wordid = wordrow[0]
                wordids.append(wordid)
                if tablenumber > 0:
                    tablelist += ','
                    clauselist +=' and '
                    clauselist += 'w%d.urlid=w%d.urlid and ' % (tablenumber-1, tablenumber)
                fieldlist += ',w%d.location' % tablenumber
                tablelist += 'wordlocation w%d' % tablenumber
                clauselist += 'w%d.wordid=%d' % (tablenumber, wordid)
                tablenumber += 1
            else:
                print "cann't fetch word id"
                return [],0

        fullquery = 'select %s from %s where %s' % (fieldlist, tablelist, clauselist)
        print fullquery
        cur = self.con.execute(fullquery)
        rows = [row for row in cur]

        return rows, wordids

    def getscoredlist(self, rows, wordids):
        totalscores = dict([(row[0],0) for row in rows])

        # define leave for evaluate function
        weights = [(1.0, self.frequencyscore(rows))]

        for (weight, scores) in weights:
            for url in totalscores:
                totalscores[url] += weight * scores[url]

        return totalscores

    def geturlname(self, ids):
        return self.con.execute(
            "select url from urllist where rowid=%d" % ids).fetchone()[0]

    def query(self, q):
        rows, wordids = self.getmatchrows(q)
        if (rows == []):
            print 'No result about %s' % q
            return
        scores = self.getscoredlist(rows, wordids)
        randedscores = sorted([(score, url) for (url, score) in scores.items()], reverse = 1)
        for (score, urlid) in randedscores[0:10]:
            print '%f\t%s' % (score, self. geturlname(urlid))

    def normalizescores(self, scores, smallIsBetter = 0):
        vsmall = 0.0001 # avoid zero devid
        if smallIsBetter:
            miniscore = min(scores.values())
            return dict([(u, float(minscore)/max(vsmall,l)) for (u, l) in scores.items()])
        else :
            maxscore = max(scores.values())
            if maxscore == 0:
                maxscore = vsmall
            return dict ([(u, float(c)/maxscore) for (u, c) in scores.items()])


    def frequencyscore(self, rows):
        counts = dict([(row[0], 0) for row in rows])
        for now in rows: counts[row[0]] += 1
        return self.normalizescores(counts)

    
                    
