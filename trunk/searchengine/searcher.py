import urllib2
import re
import lxml.html
from lxml.html import tostring
from lxml.html.clean import Cleaner
from urlparse import urljoin
from pysqlite2 import dbapi2 as sqlite


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
                return [],0

        fullquery = 'select %s from %s where %s' % (fieldlist, tablelist, clauselist)
        # print fullquery
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

    
                    
