import __init__
from  searchengine import searcher

s = searcher.searcher("searchindex.db")

query  = ["help","python","programming","ppp","pp","aaaa"]

for q in query:
    print "=" * 20
    print "~ * Start search '",q,"'"
    s.query(q)
    

