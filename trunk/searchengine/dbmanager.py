from pysqlite2 import dbapi2 as sqlite
from threading import Thread
from copy import copy
from Queue import Queue

NormalFetch = 1
WordidFetch = 2

class dbmanager(Thread):
    def __init__(self, dbname):
        self.jobs = Queue()
        self.results = Queue()
        self.wordidQ = Queue()
        self.result = None
        self.cur = None
        self.con = None
        self.dbname=dbname
        Thread.__init__(self)

    def dbconnect(self):
        self.con = sqlite.connect(self.dbname)

    def close(self):
        self.jobs.put(('close',NormalFetch))

    def dbcommit(self):
        self.jobs.put(('commit',NormalFetch))

    def do_oneshot(self,command):
        self.jobs.put((command,NormalFetch))
        conn = self.results.get()
        #res  = copy(conn)
        #return res
    def do_wordid(self,command):
        self.jobs.put((command,WordidFetch))
        id= self.wordidQ.get()
        return id

    def fetchone(self,command):
        self.jobs.put((command,True))
        res = self.results.get()
        return res

    def run(self):
        if (self.con == None):
            self.dbconnect()
        while(True):
            command, FetchType = self.jobs.get()
            if (command == 'close'):
                self.con.close()
                break;
            elif command == 'commit':
                self.con.commit()
                continue
            try:
                u = self.con.execute(command)
            except:
                print 'except on command - ' + command
                self.results.put(None)
                continue
            self.cur = u
            #        if (isFetch):
            #            self.result = u.fetchone()
            if (FetchType == NormalFetch):
                self.results.put(u.fetchone())
            elif (FetchType == WordidFetch):
                self.wordidQ.put(u.lastrowid)
        
            
        
    
                
    
