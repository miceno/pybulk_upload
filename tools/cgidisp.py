#!/usr/bin/env python
# $Id: cgidisp.py,v 1.3 1998/09/25 13:45:29 chenna
#            Exp chenna $
# $Author: chenna $
# $Version$
# $Date: 1998/09/25 13:45:29 $
#  (C) Chenna Ramu, EMBL.
#      chenna@embl-heidelberg.de
#  This is just a despatcher for  cgimode.py  !!
#
import string
import os
DispatchError = " Function not available "
class Dispatcher:
    def __init__(self):
        self.debug = None
    def dispatch(self, command,args=None):
        mname = 'cmd_' + command
        if hasattr(self, mname):
            method = getattr(self, mname)
            if not args:
                return method() #do not just call,
                               # return the string
            else:
                return method(args)
        else:
            print "<PRE>"
            self.error(command)
            self.ShowAvailableFunc()
            print "</PRE>"
    def ShowAvailableFunc(self):
        a = dir(Dispatcher)
        b = []
        for j in a:
            if j[0:4] != 'cmd_':
                continue
            b.append(j[4:])
        print "Available functions are\n\n "
        k = 0
        for j in b:
            k = k + 1
            print " %5d:  %s " %(k,j)
        return
    def error(self,s):
        print " <B> Error </B>: <BR> Function ( %s ) not available\n " %s
        return
#  This is a constant need for many cgi's
    def _forkJob(shellString,keepAlive=None):
        import os
        pid = os.fork()
        if pid:
            pass
        else:
            if not keepAlive: # if you the job run
                              # backround then...
                sys.stdout.close()
                sys.stderr.close()
                os.close(1) # not needed in v 4.0
                os.close(2) # not needed in v 4.0
            os.system(shellString)
    def cmd_Hello(self,parDict):
        print " Hello World !"
    def cmd_SalesInput(self,parDict):
        from sales import *
    def cmd_NewMeth(self,parDict):
        print "<PRE>"
        print " Hello new function "
    def cmd_ShowDict(self,parDict):
        print "<PRE>"
        print "<H1> Debug Info: </H1><HR>"
        for k,v in parDict.items():
            print "<B>%-30s</B> :  %s " %(k,v)
        print "</PRE>"
    def cmd_OutputForm(self,parDict):
        n = 0
        print "<PRE>"
        for k,v in parDict.items():
            n = n + 1
            print " %5d: %-20s :  %20s " %(n,k,v)
        print "</PRE>"
##################################################
# usage:
# cgimodel.py?-fun=DisplayFile&fileName=cgidisp.py
#   You need py2html to colour your python source!
#   checkout www.python.org
#
    def cmd_DisplayFile(self,parDict):
        fileName = parDict['fileName']
        if not fileName:
            print " File name not given  "
        else:
            import py2html
            p,fileName = os.path.split(fileName)
                     # take care of malicious user
            print "<B> File: %s </B> " %fileName
            py2html.main(['dummy','-stdout',fileName])
def test():
    d = Dispatcher()
    d.debug = 1
    d.dispatch('SalesInput','dummy')
# make an error to see how the traceback works!
    d.dispatch('NoFun')
if __name__ == '__main__':
    test()