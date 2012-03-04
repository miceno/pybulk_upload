#!/usr/bin/env python
print "Content-type: text/html"
print
print "<html><head><title>Situation snapshot</title></head><body><pre>" 
import sys
sys.stderr = sys.stdout
import os
import cgi
from cgi import escape
import cgitb
cgitb.enable()
print "<strong>Python %s</strong>" % sys.version
keys = os.environ.keys( )
keys.sort( )
for k in keys:
    print "%s\t%s" % (escape(k), escape(os.environ[k])) 

form = cgi.FieldStorage()
for i in form:
    print "%s: %s" % ( i, form.getvalue( i ) )
    
print "</pre></body></html>"
