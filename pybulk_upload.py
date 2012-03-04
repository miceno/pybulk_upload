#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python
# encoding: utf-8
#!/usr/bin/env python 
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
import collections
import cgi

# Debug trace for CGI
import cgitb

cgitb.enable()

# Log file at tmp dir based on script name
tempdir = tempfile.gettempdir()
log_file=os.path.join( tempdir, os.path.splitext( sys.argv[0] )[0]+ ".log" )
logging.basicConfig(filename=log_file,level=logging.DEBUG)
   
class HtmlFormatter:
    def __init__ ( self ):
        pass
        
    def format( self, payload ):
        result = []
        result.append( '<div class="results-container">' )
        for p in payload:
            result.append( "<div class='result-value'>%s</div>" % p )
        result.append( '</div>' )
        return result
    
class BulkOperationFormatter:
    """Format an array to produce the bulk_operation output file format.
    Usage is:
      b = BulkOperationFormatter( '/var/tmp' )
      l = get_list_of_files( 'file.zip' )
      result = []
      result = b.header()
      for r, f in zip( rows, l ):
          result.append( b.generate( r, f) )
    """
    def __init__( self, base_path, field_delimiter = '\t', line_delimiter = '\r\n' ):
        self.NUMBER = 0
        self.REFERENCE = 1
        self.TERMS = 2
        self.MEDIA = 3
        self.DESCRIPTION = 4
        self.PLACE = 5
        self.AUTHOR = 6
        self.DATE = 7
        self.MAX_SUMMARY = 100
        
        self.field_delimiter = field_delimiter
        self.line_delimiter = line_delimiter
        
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
      
    def format( self, row ):
        """format using field delimiters"""
        return self.field_delimiter.join( row )

    def generate( self, row, file_name ):
        """generate a row"""
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
        logging.debug( "date: %s" % datetime(*date_tuple).isoformat() )
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
        n = open( os.devnull, "w")
        self.sheet = xlrd.open_workbook( file_name, logfile= n, verbosity=0, on_demand = True ).sheet_by_index( sheet_index )
        self.num_rows = self.sheet.nrows
        
    def slice( self, start, end ):
        if start> end:
            start, end = ( end, start )
        return [ self.sheet.row( i ) for i in xrange( start, end ) ]

CHUNK_SIZE = 10000

# Generator to buffer file chunks
def fbuffer(f, chunk_size=CHUNK_SIZE):
   while True:
      chunk = f.read(chunk_size)
      if not chunk: break
      yield chunk

def copy_file( fileitem, target_path ):
    """Copy an uploaded file to a new location.
    Returns the name of the file or None in case the file is not copied"""
    filename = None
    # Test if the file was uploaded
    if fileitem.filename:
        # strip leading path from file name to avoid directory traversal attacks
        base_filename = os.path.basename(fileitem.filename)
        filename = os.path.join( target_path, base_filename )
        f = open( filename, 'wb', CHUNK_SIZE)

        try:
            # Read the file in chunks
            for chunk in fbuffer(fileitem.file):
                f.write(chunk)
            f.close()
        except:
            filename = None
            f.close()
       
    return filename
    
def write_response( headers, response ):
    for h in headers:
        print h
    print ""
    for r in response:
        print response
    
def main(argv=None):
    
    start = 0
    end = 0
    response = []
    headers = []
    
    # write_response( headers, response )
    if argv is None:
        argv = sys.argv
    try:
        field_delimiter = '\t'
        line_delimiter = '\r\n'
        destination_path = os.path.join( 'gallery','import')
        
        form = cgi.FieldStorage()
        #for i in form:
        #    logging.debug( "%s: %s" % ( i, form.getvalue( i ) ) )

        # Check requisite fields
        requisites = ( 'zip', 'xls' )
        for requisite in requisites:
            if requisite not in form:
                raise ValueError, 'Required parameter not in query string: %s' % requisite

        # Create destination path
        try:
            os.makedirs( destination_path )
        except:
            pass
        # Use a temporal directory to decompress the zip file
        base_path = tempfile.mkdtemp( dir = destination_path )

        # Read data from the XLS file
        # XLS file to process   
        # xls_file_name = 'fotos.xls'
        xls_file_name = form[ 'xls' ].filename
        
        slicer = Slicer( xls_file_name, 0 )
        # Start position
        start = int( form.getfirst( 'start', 0 ) )
        # End position
        end = int( form.getfirst( 'end', slicer.num_rows ) )
        rows = slicer.slice( start, end )
        # print "\n".join( [ str( r ) for r in rows ] )
        
        # Process the ZIP file
        # Read the names of the files
        zip_file_param = form[ 'zip' ]
        base_name = os.path.splitext( os.path.basename( zip_file_param.filename ) )[0]
        # copy it to the temp directory
        zip_file_name = copy_file( zip_file_param, base_path )
        z = zipfile.ZipFile( zip_file_param.file, 'r' )
        files = sorted( z.namelist() )
        logging.info( "Zip file copied to %s", zip_file_name )
        logging.debug( "Files to sort: %s" % ",".join( files ) )
        
        # Generating bulk_upload text file
        b = BulkOperationFormatter( base_path, field_delimiter )
        h = HtmlFormatter()
        
        result = []
        html_result = []
        result.append( b.header() )
        # Format each row
        for r, f in zip( rows, files ):
            # Output each row processed
            row = b.generate( r, f)
            logging.debug( "row: %s" % row)
            result.append( row )
            html_result.append( h.format( row ) )

        logging.debug( "result= %s" % result )
        logging.debug( "html_result = %s" % html_result )
        
        headers.append( "Content-type: text/html" )
        response.append( """<html>
        <head>
            <meta http-equiv="Content-type" content="text/html; charset=utf-8">
            <link rel="stylesheet" href="bulk.css" type="text/css" media="screen" title="bulk" charset="utf-8">
            <title>Bulk results</title>
        </head>
        <body>""")
        
        # print ",<br/>".join( [ r for r in result] )
        txt_result = ""
        txt_result = line_delimiter.join( [ field_delimiter.join( r ).encode( 'utf-8') for r in result] )
        # Write output file
        output_file_name = os.path.join( base_path, base_name ) + ".txt"
        message = "Output File name located at: %s" % output_file_name
        logging.info( message )
        response.append( "<div class='message'>%s</div>" % message )
        response.append( "<hr/>" )

        output_file = open( output_file_name, "w" )
        for r in result:
            output_file.write( b.format( r ).encode( 'utf-8' ) )
            output_file.write( line_delimiter )
        output_file.close()
        
        for l in html_result:
            for r in l:
                response.append( r.encode( 'utf-8') )
        response.append( "</body></html>" )
    except Usage, err:
        logging.error( sys.argv[0].split("/")[-1] + ": " + str(err.msg) )
        return 2
        """except:
            headers = []
            headers.append( 'Status: 500' )
            response = []
            response.append( "Error" )"""
        pass
    write_response( headers, response )
    
if __name__ == "__main__":
    sys.exit(main())
