import __init__
from  searchengine import searcher
import sys

if len(sys.argv)  > 1:
    db = sys.argv[1]
else:
    db = "data/engine.db"
    
print "search engine use database: ", db
s = searcher.searcher(db)

query  = ["help","python","programming","ppp","pp","aaaa", "kaifu"]

for q in query:
    print "=" * 20
    print "~ * Start search '",q,"'"
    res,count = s.query(q)
    print "------------- res ---------"
    print "---- count ---",count
    print res
    print "---------------------------"
    

