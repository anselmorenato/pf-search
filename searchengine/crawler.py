import urllib2
import re
import lxml.html
from lxml.html import tostring
from lxml.html.clean import Cleaner
from urlparse import urljoin

USEMYSQL=True
#from pysqlite2 import dbapi2 as sqlite
import MySQLdb

import Queue
from threading import Thread,Lock
import time

debuglock = False

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)
# stop by ctrl c


ignorewords = set(['the','of','to','and','a','in','is','it'])

class mtcrawler:
    "This is the multi thread warpper of crawler"
    def __init__(self, pages, dbuser, dbpasswd,dbname='pfdb',threads=5,depth=2,host='localhost'):
        self.crawlervec = set()
        self.threads = threads;
        self.depth = depth;
        self.dbname = dbname
        self.dbuser = dbuser
        self.dbpasswd = dbpasswd
        self.dbhost = host
        self.jobs = Queue.Queue();
        self.newpages = set()
        self.pages = pages

    def start(self):
        for i in range(self.depth):
            self.crawlervec.clear()
            for page in self.pages:
                self.jobs.put(page)
            for t in range(self.threads):
                c = crawler(dbname = self.dbname,jobs = self.jobs, \
                                newpages = self.newpages, host= self.dbhost, \
                                dbuser=self.dbuser, dbpasswd = self.dbpasswd);
                self.crawlervec.add(c);

            for t in self.crawlervec:
                t.start()
                
            for t in self.crawlervec:
                t.join()
            self.pages = self.newpages

    def createdb(self):
        pass
    def cleardb(self):
        # this sql command
        # drop database pfdb;
        # create database pfdb;
        pass


class crawler(Thread):
    """This class was a crawler thread, do crawler things. every thread
    has a connection to data base"""
    
    def __init__(self, dbname,dbuser,dbpasswd, jobs, newpages, \
                     host):
        self.con = MySQLdb.connect(host=host, user=dbuser,passwd=dbpasswd, \
                                       use_unicode=True)
        self.curs = self.con.cursor()
        self.curs.execute('use %s;' % dbname)
        self.jobs = jobs
        self.newpages = newpages
        Thread.__init__(self)

    def __del__(self):
        self.curs.close()

    def dbcommit(self):
        self.con.commit()

    def getentryid(self,table,field,value,createnew=True):
        self.curs.execute(
            "select rowid from %s where %s = '%s'" % (table, field, value))
        res = self.curs.fetchone()
        if res == None:
            self.curs.execute(
                "insert into %s (%s) values ('%s')" % (table, field, value))
            rowid = self.curs.lastrowid
            return rowid
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
            self.curs.execute("insert into wordlocation(urlid,wordid,location) values (%d, %d, %d)" % (urlid,wordid, i))
                        
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
        self.curs.execute \
            ("select rowid from urllist where url='%s'" % url);
        u = self.curs.fetchone()
        if u != None:
            self.curs.execute(
                'select * from wordlocation where urlid=%d' % u[0])
            v = self.curs.fetchone()
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

    def run(self):
        self.thread_crawl(self.jobs, self.newpages)
        
    def thread_crawl(self,jobs, newpages):
        while 1:
            try:
                page = jobs.get(True,3)
            except Queue.Empty:
                    print 'one thread gone'
                    return
            self.docrawl(page,newpages);

    # do crawl job, if failed return False, or return True
    def docrawl(self,page, newpages):
        node = self.openurl(page)
        if node == None: return False
        try:
            tree = lxml.html.parse(node)
        except IOError, msg:
            print msg
            print "IOError: Please Check Your Network Connection."
            exit
            
        # start operating db
        self.addtoindex(page,tree)
        self.genrate_link_map(tree,page,newpages)
        self.dbcommit()
        return True
        
    def crawl (self, pages, depth=2, lock=None):
        for i in range(depth):
            newpages = set()
            for page in pages:
                self.docrawl(page, newpages);
            pages = newpages

    def openurl(self, page,timeout=30):
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
    

    def genrate_link_map(self,tree,page,newpages):
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

    def createindextables(self):
        try :
            self.curs.execute('create database pfdb;')
        except:
            pass
        self.curs.execute('use pfdb;')
        self.curs.execute('create table urllist(url text(1024) not null);')
        self.curs.execute('create table wordlist(word char(255));')
        self.curs.execute('create table wordlocation(urlid int,wordid int,location int (20));')
        self.curs.execute('create table link(fromid int, toid int);')
        self.curs.execute('create table linkwords(wordid int,linkid int);')

        tables = ['urllist','wordlist','wordlocation','link','linkwords']
        for t in tables:
            self.curs.execute('alter table %s add column rowid int(10) auto_increment primary key first;' % t)
        self.curs.execute('create index wordidx on wordlist(word);')
        self.curs.execute('create index urlidx on urllist(url(1000));')
        self.curs.execute('create index wordurlidx on wordlocation(wordid);')
        self.curs.execute('create index urltoidx on link(toid);')
        self.curs.execute('create index urlfromidx on link(fromid);')
        self.dbcommit()
        
