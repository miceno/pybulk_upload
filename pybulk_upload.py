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

help_message = ''' [options] xls_file_name
-e, --end       End row
-o, --output    Output file name
-s, --start     Start row
'''

class Generator:
    """Generator: takes an xls, a zipfile, start and end rows and builds a txt file"""
    
    def __init__( self, xls_file_name, zip_file_name, start, end, **kwargs ):
        # output_file_name is the basename of the zipfile
        self.output_file_name = kwargs.get( 'output_file_name', os.path.splitext( zip_file_name ) + ".txt" )
        pass
        
    def generate( self ):
        "Generate the txt file"
        pass
   
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
        pass
    
    def header( self ):
        result = ( 'title', 'summary', 'description', 'keywords', 'filename' )
        return result
        
    def format( self, row, file_name ):
        """format a row"""
        result = []
        result.append( os.path.split( file_name )[1] )
        result.append( row[ self.DESCRIPTION ][:self.MAX_SUMMARY] )
        result.append( row[ self.DESCRIPTION ] )
        keywords = row[ self.NUMBER:self.MEDIA ]
        keywords += row[ self.PLACE:self.DATE ]
        result.append( ",".join( keywords ) )
        result.append( os.path.join( base_path, file_name ) )
        return result
        pass

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

class Slicer:
    """Slice an XLS file"""
    def __init__( self, file_name, sheet_index ):
        self.sheet = xlrd.open_workbook( file_name, on_demand = True ).sheet_by_index( sheet_index )
        
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
        try:
            opts, args = getopt.getopt(argv[1:], "hz:s:e:o:v", ["help", "zipfile", "start", "end", "output="])
        except getopt.error, msg:
            raise Usage(msg)
        
        if not len( args ):
            raise Usage( help_message )
        # XLS file to process   
        xls_file_name = args[0]
        zip_file_name = 'test.zip'
        
        # option processing
        for option, value in opts:
            if option == "-v":
                verbose = True
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-z", "--zipfile"):
                zip_file_name = value
            if option in ("-o", "--output"):
                output = value
            if option in ("-s", "--start"):
                start = int( value )
            if option in ("-e", "--end"):
                end = int( value )
    
        slicer = Slicer( xls_file_name, 0 )
        rows = slicer.slice( start, end )
        # print "\n".join( [ str( r ) for r in rows ] )
        
        z = zipfile.ZipFile( zip_file_name, 'r' )
        files = sorted( z.namelist() )
        
        base_path = '/tmp'
        b = BulkOperationFormatter( base_path )
        
        result = []
        result.append( b.header() )
        for r, f in zip( rows, files ):
            result.append( b.format( r, f) )
            
        print "\n".join( result )
        
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2


if __name__ == "__main__":
    sys.exit(main())
