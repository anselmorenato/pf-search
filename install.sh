#/bin/sh

enginePath=/var/lib/python-support/python2.6/searchengine
mkdir -p $enginePath
install searchengine/*.py* /var/lib/python-support/python2.6/searchengine/
install cgi-bin/query.py /usr/lib/cgi-bin/search
chmod 755 /usr/lib/cgi-bin/search

