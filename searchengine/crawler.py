import urllib2
import re
import lxml.html
from lxml.html import tostring
from lxml.html.clean import Cleaner
from urlparse import urljoin

import Queue
from threading import Thread, Lock
from dbmanager import dbmanager

debug = False



ignorewords = set(['the','of','to','and','a','in','is','it'])


class crawler:
    def __init__(self, dbname):
        self.dber = dbmanager(dbname)
        self.dber.start()
        self.dbLock = Lock()
        self.newpageLock = Lock()
        self.wordidLock = Lock()

    def __del__(self):
        self.dber.close()

    def dbcommit(self):
        self.dber.dbcommit()

    def getentryid(self,table,field,value,createnew=True):
        res = self.dber.fetchone("select rowid from %s where %s = '%s'" \
                                      % (table, field, value))
        if res == None:
            lastrowid = self.dber.do_wordid(
                "insert into %s (%s) values ('%s')" % (table, field, value))
            return lastrowid
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
        if debug: print 'urlid :',urlid
        # make every word related
        for i in range(len(words)):
            word = words[i]
            if word in ignorewords: continue
            wordid = self.getentryid('wordlist', 'word', word);
            try:
                self.dber.do_oneshot("insert into wordlocation(urlid,wordid,location) values (%d, %d, %d)" % (urlid,wordid, i))
            except TypeError:
                print "urlid:",urlid,"wordid:",wordid,"i:",i
                raise
                
        
    
    def gettextonly(self, tree):
        if debug: print 'gettextonly'
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
        if debug: print 'isindexed'
        u = self.dber.fetchone\
            ("select rowid from urllist where url='%s'" % url)
        if u != None:
            v = self.dber.fetchone(
                'select * from wordlocation where urlid=%d' % u[0])
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

    def thread_crawl(self, jobs, newpages):
        while(True):
            try:
                page = jobs.get(True,10)
            except:
                print 'one thread gone'
                return
            self.__doCrawl(page,newpages)

    def crawl (self, pages, depth=2, numthreads=10):
        threads = []
        
        for i in range(depth):
            print '.'
            newpages = set()
            jobs = Queue.Queue()
            for page in pages:
                jobs.put(page)
            for i in range(numthreads):
                t = Thread(target=self.thread_crawl,args=(jobs,newpages))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()
            if debug: print 'finish depth: ',depth
            pages = newpages
        self.dber.close()

    def __doCrawl(self, page,newpages):
        if debug: print 'doCrawl'
        node = self.__openUrl(page)
        if node == None: return
        try:
            tree = lxml.html.parse(node)
        except IOError, msg:
            print msg
            print "IOError: Please Check Your Network Connection."
            
        #self.dbLock.acquire()
        #print "lock db"
                # start operating db
        self.addtoindex(page,tree)
        self.__process_link(tree, page,newpages)
        self.dbcommit()
                # end operating db
        #print "release db"
        #self.dbLock.release()

        
    def __openUrl(self, page, timeout=30):
        print "Opening %s" % page

        try:
            node = urllib2.urlopen(page, timeout=timeout)
        except urllib2.HTTPError, msg:
            print "%s  %s" % (page, msg)
            return None
        except urllib2.URLError, msg:
            print "%s %s" % (page, msg)
            return None
        except:
            print "%s cann't open" % page
            raise
        return node
    

    def __process_link(self,tree,page,newpages):
        if debug :print 'processing link '
        links = tree.findall('.//a')
        for link in links:
            if ('href' in dict(link.attrib)):
                url = urljoin(page, link.attrib['href'])
                if url.find("'") != -1: continue
                url = url.split('#')[0]
                if url[0:4] == 'http' and not self.isindexed(url):
                    if (debug): print 'get newpageLock'
                    self.newpageLock.acquire()
                    newpages.add(url)
                    self.newpageLock.release()
                    if (debug): print 'release new page lock'
                    if (debug):   print 'adding %s' % url
                    linkText = link.text
                        # This should be the title of link
                    self.addlinkref(page,url,linkText)

    def createindextables(self):
        self.dber.do_oneshot('create table urllist(url)')
        self.dber.do_oneshot('create table wordlist(word)')
        self.dber.do_oneshot('create table wordlocation(urlid,wordid,location)')
        self.dber.do_oneshot('create table link(fromid integer, toid integer)')
        self.dber.do_oneshot('create table linkwords(wordid,linkid)')
        self.dber.do_oneshot('create index wordidx on wordlist(word)')
        self.dber.do_oneshot('create index urlidx on urllist(url)')
        self.dber.do_oneshot('create index wordurlidx on wordlocation(wordid)')
        self.dber.do_oneshot('create index urltoidx on link(toid)')
        self.dber.do_oneshot('create index urlfromidx on link(fromid)')
        self.dber.dbcommit()
