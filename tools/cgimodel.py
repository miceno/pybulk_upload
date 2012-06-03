#!/usr/bin/env python
# $Id: cgimodel.py,v 1.3 1998/09/25 13:45:29
#     chenna Exp chenna $
# $Author: chenna $
# $Version$
# $Date: 1998/09/25 13:45:29 $
#  (C) Chenna Ramu, EMBL.
#      chenna@embl-heidelberg.de
# History
#  Fixed the bug, when more than one value has the
#  same key, the values should be a list for that
#  key in the dict!
import sys
from cgidisp import *
mime_html = "Content-type: text/html\n\n"
pre  = "<PRE>"
_pre = "</PRE>"
# A dictionary with default values for
# non-existing entries
import UserDict, copy
class DictWithDefault(UserDict.UserDict):
    def __init__(self, default):
        self.data = {}
        self.default = default
    def __getitem__(self, key):
        try:
            item = self.data[key]
        except KeyError:
            item = copy.copy(self.default)
            self.data[key] = item
        return item
    def __delitem__(self, key):
        try:
            del self.data[key]
        except KeyError:
            pass
def CollectArgs(parDict=None):
   if not parDict:
       parDict = DictWithDefault(None) # make anew
   if( len(sys.argv) > 1 ):
      cmdLine = sys.argv
      i = 1
      try:
        while i < len(cmdLine):
            key = cmdLine[i]
            val = cmdLine[i+1]
            if key[0] == '-':
           key = key[1:]
         if parDict.has_key(key): # make list
        if type(parDict[key]) == type([]):
            parDict[key].append(val)
        else:
            parDict[key] = []
            tmp = parDict[key]
            parDict[key].append(tmp)
            parDict[key].append(val)
         else:
        parDict[key] = val
         i = i + 2
        parDict['isCmdLine'] = 1
      except IndexError:
     pass
   else:
      import cgi
      form = cgi.FieldStorage()
      parDict['isHtml'] = 1
      for j in form.list:
     if j.name[0] == '-':  # take care of
                                # '-' in cgi
         j.name = j.name[1:]
        parDict[j.name]=j.value
      parDict['isCmdLine'] = None
      import os
      parDict['_environ'] = {}  # do not mix the
                   # environs with main dictionary
      for k,v in os.environ.items():
     parDict['_environ'][k] = v
   return parDict
def TraceIt(parDict):
    import traceback
    sys.stderr = sys.stdout
    if not parDict.has_key('isCmdLine'):
   print parDict['isCmdLine']
   print mime_html
   print pre
   print " <B> Tracing ... </B>"
    traceback.print_exc()
    if not parDict.has_key('isCmdLine'):
   print _pre
    return
##################################################
#  main
#
def main():
    parDict  = DictWithDefault(None)
    d = Dispatcher()
    parDict = CollectArgs(parDict)
    mime = parDict['mime']
    if not mime:
   print mime_html # print default mime
    if mime == 'simple':
   pass
    fun = parDict['fun']
    if not fun:
   print "usage : cgimodel -fun functionName"
   d.ShowAvailableFunc()
   TraceIt(parDict)
    else:
   try:
       d.dispatch(fun,parDict)
   except:
       TraceIt(parDict)
if __name__ == '__main__' :
    main()