#!/usr/bin/env python
# encoding: utf-8
"""
pybulk_upload.py

Created by Orestes Sanchez on 2012-02-27.
Copyright (c) 2012 Telefónica I+D. All rights reserved.
"""

import sys
import getopt
import xlrd
import os
import zipfile
from datetime import datetime
import logging
import tempfile
import cgi

# Log file at tmp dir based on script name
tempdir = tempfile.gettempdir()
print "tempdir=", tempdir
log_file=os.path.join( tempdir, os.path.splitext( sys.argv[0] )[0]+ ".log" )
logging.basicConfig(filename=log_file,level=logging.DEBUG)
   
class HtmlFormatter:
    def __init__ ( self ):
        pass
        
    def format( self, payload ):
        
        return result
    
class BulkOperationFormatter:
    """Format an array to produce the bulk_operation output file format.
    Usage is:
      b = BulkOperationFormatter( '/var/tmp' )
      l = get_list_of_files( 'file.zip' )
      result = []
      result = b.header()
      for r, f in zip( rows, l ):
          result.append( b.format( r, f) )
    """
    def __init__( self, base_path ):
        self.NUMBER = 0
        self.REFERENCE = 1
        self.TERMS = 2
        self.MEDIA = 3
        self.DESCRIPTION = 4
        self.PLACE = 5
        self.AUTHOR = 6
        self.DATE = 7
        self.MAX_SUMMARY = 100
        
        self.base_path = base_path
        pass
    
    def header( self ):
        result = ( 'title', 'summary', 'description', 'keywords', 'filename' )
        return result
  
    #
    def tupledate_to_isodate( self, tupledate ):
        """
        Turns a gregorian (year, month, day, hour, minute, nearest_second) into a
        standard YYYY-MM-DDTHH:MM:SS ISO date.  If the date part is all zeros, it's
        assumed to be a time; if the time part is all zeros it's assumed to be a date;
        if all of it is zeros it's taken to be a time, specifically 00:00:00 (midnight).

        Note that datetimes of midnight will come back as date-only strings.  A date
        of month=0 and day=0 is meaningless, so that part of the coercion is safe.
        For more on the hairy nature of Excel date/times see http://www.lexicon.net/sjmachin/xlrd.html
        """
        (y,m,d, hh,mm,ss) = tupledate
        nonzero = lambda n: n!=0
        date = "%04d-%02d-%02d"  % (y,m,d)    if filter(nonzero, (y,m,d))                else ''
        time = "T%02d:%02d:%02d" % (hh,mm,ss) if filter(nonzero, (hh,mm,ss)) or not date else ''
        return date+time
      
    def format( self, row, file_name ):
        """format a row"""
        result = []
        # Strip extention of the filename
        result.append( os.path.splitext( os.path.split( file_name )[1] )[0] )
        result.append( row[ self.DESCRIPTION ].value[:self.MAX_SUMMARY] )
        result.append( row[ self.DESCRIPTION ].value )
        keywords = []
        keywords.append( str( int( row[ self.NUMBER ].value ) ) )
        keywords.append( row[ self.REFERENCE ].value )
        keywords.append( row[ self.TERMS ].value ) 
        keywords.append( row[ self.MEDIA ].value )

        keywords.append( row[ self.PLACE ].value )
        keywords.append( row[ self.AUTHOR ].value )
        MODE_1900 = 0
        MODE_1904 = 1
        
        date_tuple = xlrd.xldate_as_tuple( row[ self.DATE ].value, MODE_1900 )
        logging.debug( "date: ", datetime(*date_tuple) )
        keywords.append( self.tupledate_to_isodate( date_tuple ) )

        result.append( ",".join( keywords ) )
        result.append( os.path.join( self.base_path, file_name ) )
        return result
        pass

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

class Slicer:
    """Slice an XLS file"""
    def __init__( self, file_name, sheet_index=0 ):
        self.sheet = xlrd.open_workbook( file_name, on_demand = True ).sheet_by_index( sheet_index )
        self.num_rows = self.sheet.nrows
        
    def slice( self, start, end ):
        if start> end:
            start, end = ( end, start )
        return [ self.sheet.row( i ) for i in xrange( start, end ) ]

def main(argv=None):
    
    start = 0
    end = 0
    if argv is None:
        argv = sys.argv
    try:
        form = cgi.FieldStorage()
        for i in form:
            logging.debug( "%s: %s" % ( i, form.getvalue( i ) ) )
        
        requisites = ( 'zip', 'xls' )
        for requisite in requisites:
            if requisite not in form:
                raise ValueError, 'Required parameter not in query string: %s' % requisite
                
        # XLS file to process   
        # xls_file_name = 'fotos.xls'
        xls_file_name = form[ 'xls' ]
        
        slicer = Slicer( xls_file_name.file, 0 )
        # Start position
        start = int( form.getfirst( 'start', 0 ) )
        # End position
        end = int( form.getfirst( 'end', slicer.num_rows ) )
        
        zip_file_name = form[ 'zip' ]
        
        # Use a temporal directory to decompress the zip file
        base_path = tempfile.mkdtemp( )        
    
        rows = slicer.slice( start, end )
        # print "\n".join( [ str( r ) for r in rows ] )
        
        z = zipfile.ZipFile( zip_file_name.file, 'r' )
        files = sorted( z.namelist() )
        
        b = BulkOperationFormatter( base_path )
        
        result = []
        result.append( b.header() )
        for r, f in zip( rows, files ):
            result.append( b.format( r, f) )
        
        logging.debug( "result= ", str( result ) )
        # print "debug result= ", repr( result )    
        # print "\n".join( [ "|".join( r ) for r in result ] )
        
    except Usage, err:
        logging.error( sys.argv[0].split("/")[-1] + ": " + str(err.msg) )
        return 2


if __name__ == "__main__":
    sys.exit(main())
