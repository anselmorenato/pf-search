import __init__
from  searchengine import *

s = searcher("searchindex.db")

query  = ["help","python","programming","ppp","pp","aaaa"]

for q in query:
    print "~ * Start search '",q,"'"
    s.query(q)
    

