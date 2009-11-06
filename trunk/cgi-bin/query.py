#!/usr/bin/python

debug = False

from sys import path,argv
#path.append("../")
import cgi
import cgitb
from time import time
startTime = time()
searchText = ""
resultCount = 0

from searchengine import searcher

if not debug :
    cgitb.enable()

form = cgi.FieldStorage()

if (debug): cgi.print_form(form)

def htmlHeader(text = ''):
    decl = "Content-Type: text/html\n"
    
    # decl += """<!DOCTYPE html PUBLIC
    #  "-//W3C//DTD XHTML 1.0 Transitional//EN"
    #  "DTD/xhtml1-transitional.dtd">"""
    if text == "":
        Title = "Search"
    else:
        Title = "Result of %s" % text
   
    head =  """
   <html xmlns = "http://www.w3.org/1999/xhtml" xml:lang="en"
      lang="en">
      <head><title>%s</title></head>
      <body><table style = "border: 0">""" % Title

    search= """
        <form enctype="multipart/form-data"
          method=post
          action="search">
      <input id=text maxLength=256 name=q value="" size=50><br>
      <input type=submit value="Search">
    </form>"""
    
    return decl + head + search

def tail():
    return "</html></head>"

def beginResult():
    return "<hr>"
def noResult(is_print_result = True):
    str = htmlHeader()
    str += beginResult()
    if is_print_result:
        return str + """<H2>Your Search -%s - did not match any documents.""" % searchText + tail()
    else:
        return str+tail()

def contextHeader(text):
    t = time() - startTime
    timeStr = '%.5f' % t
    timeStr.rstrip('0')
    if resultCount < 10: val = resultCount
    else : val = 10
    return 'Result <b>1-%d</b>" of about <b>%d</b> for <b>%s</b>.(%s seconds)'    % (val,resultCount, cgi.escape(text), timeStr)

def main():
    global searchText,resultCount
    if not debug and not form.has_key('q'):
        # TODO Maybe return an query html page is better?
        print noResult(False)
        exit
    else:
        s = []
        if debug:
            text = argv[1]
        else:
            text = form["q"].value
        searchText = text
        if debug: print "text is :",text
        s = searcher.searcher("/var/local/se/engine.db")
        page = htmlHeader(text)
        
        result,resultCount = s.query(text)
        page += contextHeader(text)
        page += beginResult()
        
        if (result == []):
            print noResult()
            exit
        else:
            for (score,url) in result:
                page += '<a href="%s">%s</a><br>' % (cgi.escape(url),cgi.escape(url[0:50]))
                page += '<br>'
            print page

main()
