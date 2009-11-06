import __init__
from  searchengine import searcher

s = searcher.searcher("data/engine.db")

query  = ["help","python","programming","ppp","pp","aaaa"]

for q in query:
    print "=" * 20
    print "~ * Start search '",q,"'"
    res,count = s.query(q)
    print "------------- res ---------"
    print "---- count ---",count
    print res
    print "---------------------------"
    

