#/bin/sh

enginePath=/var/lib/python-support/python2.6/searchengine
mkdir -p $enginePath
install searchengine/*.py* /var/lib/python-support/python2.6/searchengine/
install cgi-bin/query.py /usr/lib/cgi-bin/search
engineData=/var/local/se/
mkdir -p $engineData
dbPath=test/data/engine.db
if [ ! -f $dbPath ]
then
echo "::Start download data base"
(cd test/data;. ./get_data.sh)
fi
install $dbPath $engineData/engine.db
chmod 755 /usr/lib/cgi-bin/search

