#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python
# encoding: utf-8
#!/usr/bin/env python 
"""
pybulk_upload.py

Created by Orestes Sanchez on 2012-02-27.
Copyright (c) 2012 Telefónica I+D. All rights reserved.
"""

import sys

if sys.version_info < (2, 7):
    sys.path.append( '/kunden/homepages/8/d228439513/htdocs/lib/python2.6/site-packages/xlrd-0.7.3-py2.6.egg' )

import getopt
import xlrd
import os
import zipfile
from datetime import datetime
import logging
import tempfile
import collections
import cgi
import re

# Debug trace for CGI
import cgitb

cgitb.enable()

# Global Folders dictionary
folders = {}

def read_folders( filename ):
    global folders
    folders = {}
    try:
        for d in csv.DictReader(open(filename),fieldnames=['0','1']):
            folders[ d['0'] ] = d['1']
    except:
        pass

def banner( message ):
    return "\n".join( ( "*" * 20, message, "*" * 20 ))
    
def html_message( message ):
    return "<div class='message'>%s</div>" % message 
    
# Log file at tmp dir based on script name

stop_delimiters = re.compile( '[,;\.]|(\si\s)')
open_close_delimiters = re.compile( '[\)\]]')
MAX_SUMMARY = 100

def generate_delimiter_re( open_delimiter, close_delimiter ):
    c = re.compile( "".join( ( open_delimiter, '[^', close_delimiter, ']*$' ) ) )
    return c
    
def summarize( message ):
    # Position for first closing delimiter 
    result = message[:MAX_SUMMARY][::-1]
    #print "reversed message=",result
    match = open_close_delimiters.search( result )
    if match is not None and match.start() < MAX_SUMMARY:
        result = result[match.start()-1:]
        #print "result open_close:", result
    else:
        match = stop_delimiters.search ( result )
        if match is not None and match.start() < MAX_SUMMARY:
            result = result[ match.end():]
            #print "result stop:", result
    # print "reversed=", result
    return result[::-1]

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
        self.FOLDER = 1
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
        date = "%02d-%02d-%04d"  % (d,m,y)    if filter(nonzero, (d,m,y))                else ''
        # date = "%04d-%02d-%02d"  % (y,m,d)    if filter(nonzero, (y,m,d))                else ''
        time = "T%02d:%02d:%02d" % (hh,mm,ss) if filter(nonzero, (hh,mm,ss)) or not date else ''
        return date+time
      
    def format( self, row ):
        """format using field delimiters"""
        return self.field_delimiter.join( row )

    def generate( self, row, file_name ):
        """generate a row"""
        result = []
        # Strip extention of the filename
        raw_file_name = os.path.split( file_name )[1]
        raw_title = os.path.splitext( raw_file_name )[0]
        result.append( unicode( raw_title, 'utf-8' ) )
        result.append( summarize( row[ self.DESCRIPTION ].value) )
        result.append( row[ self.DESCRIPTION ].value )
        keywords = []
        keywords.append( str( int( row[ self.NUMBER ].value ) ) )
        # Get folder name, or empty string
        folder_name = folders.get( row[ self.FOLDER ].value, "" )
        if folder_name != "":
            keywords.append( folder_name )
        # Add also folder number in case it is not empty
        if row[ self.FOLDER ].value != "" :
            keywords.append( row[ self.FOLDER ].value )
        keywords.append( row[ self.TERMS ].value ) 
        keywords.append( row[ self.MEDIA ].value )

        keywords.append( row[ self.PLACE ].value )
        keywords.append( row[ self.AUTHOR ].value )
        MODE_1900 = 0
        MODE_1904 = 1
        
        value = row[ self.DATE ].value
        
        if row[ self.DATE ].ctype == xlrd.XL_CELL_DATE:
            date_tuple = xlrd.xldate_as_tuple( row[ self.DATE ].value, MODE_1900 )
            date_string = self.tupledate_to_isodate( date_tuple )
        elif row[ self.DATE ].ctype == xlrd.XL_CELL_TEXT:
            # It is a year as a number or as a text
            date_string = value
        elif row[ self.DATE ].ctype == xlrd.XL_CELL_NUMBER:
            # It is a year as a number or as a text
            date_string = str( int( value ) )
            
        logging.debug( "date: %s" % date_string )
        keywords.append( date_string )

        result.append( ",".join( keywords ) )
        result.append( os.path.join( self.base_path, unicode( file_name, 'utf-8' ) ) )
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
        """Get a slice from row [start, end), that is, it does not include end"""
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
        logging.debug( "header %s" % h)
        print h
    print ""
    for i,r in enumerate( response ):
        logging.debug( "response %d: %s" % (i,r))
        print r
        
def getfirstInt( form , field_name, default = "" ):
    """Get the first element of a form as an integer. Check if it is empty"""
    value = form.getfirst( field_name, default )
    result = 0
    if value is not None and value != "":
        result = int( value )
    return result
    
    
def main(argv=None):
    
    start = 0
    end = 0
    response = []
    headers = []
    
    DEFAULT_TARGET_PATH = ( '~','Downloads','gallery','bulk' )
    # DEFAULT_TARGET_PATH = ( '~','private','gallery','bulk' )
    destination_path = os.path.expanduser( os.path.join( *DEFAULT_TARGET_PATH ) )
    
    # Log file writes to the destination path
    log_file=os.path.join( destination_path, os.path.splitext( sys.argv[0] )[0]+ ".log" )
    logging.basicConfig(filename=log_file,level=logging.DEBUG)
    
    # write_response( headers, response )
    if argv is None:
        argv = sys.argv
    try:
        field_delimiter = '\t'
        line_delimiter = '\r\n'
        
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
        
        # Read the folders data
        read_folders( 'carpetes.csv' )
        
        # Read data from the XLS file
        # XLS file to process   
        # xls_file_name = 'fotos.xls'
        xls_file_param = form[ 'xls' ]
        xls_file_name = copy_file( xls_file_param, base_path )
        
        slicer = Slicer( xls_file_name, 0 )
        # Start position
        start = getfirstInt( form, 'start', 0 ) - 1
        if start < 0:
            start = 0
        # End position
        end = getfirstInt( form, 'end', slicer.num_rows)
        if end == 0:
            end = slicer.num_rows
        
        rows = slicer.slice( start, end )
        logging.debug( banner( "slicer") )
        logging.debug( "\n".join( [ str( r ) for r in rows ] ) )
        
        # Process the ZIP file
        zip_file_param = form[ 'zip' ]
        base_name = os.path.splitext( os.path.basename( zip_file_param.filename ) )[0]
        # copy it to the temp directory
        zip_file_name = copy_file( zip_file_param, base_path )
        # Read the names of the files
        z = zipfile.ZipFile( zip_file_param.file, 'r' )
        files = sorted( z.namelist() )
        files = files[ start:end]
        message = "Zip file copied to %s" % zip_file_name
        logging.info( message )
        response.append( html_message( message ) )
        logging.debug( "Files to sort: %s" % ",".join( files ) )
        # Decompress the file
        message = "Decompressing file %s at directory %s" % ( zip_file_name, base_path  )
        logging.info( message )
        response.append( html_message( message ))
                    
        z.extractall( base_path, files )
        
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
        response.append( html_message( message ) )
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
    
def test_main():
    sys.exit(main())
    
def test_summary():
    print banner( 'test_delimiter')
    
    texto = ( \
    """Visita a la Torre de les Aigües (Pere Falqués, 1881) rehabilitada per l'arquitecte Antoni Vilanova (centre). A la dreta XXXX, arquitecte de l'equip de Vilanova. A l'esquerra, Jordi Fossas, arquitecte i president de l'AHPN.""", \
    """Visita a la Torre de les Aigües (Pere Falqués, 1881) rehabilitada per l'arquitecte Antoni Vilanova (esquerra). Cap a la dreta Jordi Fossas, arquitecte i president de l'AHPN i Juan Roca, del MUHBA.""", \
    """Visita a la Torre de les Aigües (Pere Falqués, 1881). A l'esquerra, Juan Roca del MUHBA, en el centre el representant d'Aigües de Barcelona. Cap a la dreta, Xavier Pegenaute i Salvador Clarós, president i expresident de l'AVPN.""", \
    """Làpida a l'església del Sagrat Cor de Jesús, de la sepultura on varen ser traslladades el 5/3/1928 les restes dels germans Laureano Arango Portús (mort el 23/6/1891) i Josefa Arango Portús (morta el 4/1/1918), fundadors de la parròquia per disposició dels seus testaments. El 1936 la tomba fou profanada i les restes cremades al carrer. El que en quedà fou sepultat en un nínxol al cementiri de l'est, però per falta de pagament l'ajuntament el buidà i les restes acabaren a la fossa comú.""", \
    """Làpida a l'església del Sagrat Cor de Jesús, de la sepultura on varen ser traslladades el 5/3/1928 les restes dels germans Laureano Arango Portús (mort el 23/6/1891) i Josefa Arango Portús (morta el 4/1/1918), fundadors de la parròquia per disposició dels seus testaments. El 1936 la tomba fou profanada i les restes cremades al carrer. El que en quedà fou sepultat en un nínxol al cementiri de l'est, però per falta de pagament l'ajuntament el buidà i les restes acabaren a la fossa comú.""", \
    """Interior de l'Església del Sagrat Cor de Jesús, la única del Poblenou que nou fou totalment destruïda pel foc el 1936, gràcies als treballadors de les cotxeres del costat que van tenir por que el foc es propagués. En el terra s'observen els senyals del foc, que va enderrocar la coberta.""", \
    """Interior de l'Església del Sagrat Cor de Jesús, la única del Poblenou que nou fou totalment destruïda pel foc el 1936, gràcies als treballadors de les cotxeres del costat que van tenir por que el foc es propagués. En el terra s'observen els senyals del foc, que va enderrocar la coberta.""", \
    """Interior de l'Església del Sagrat Cor de Jesús, la única del Poblenou que nou fou totalment destruïda pel foc el 1936, gràcies als treballadors de les cotxeres del costat que van tenir por que el foc es propagués. En el terra s'observen els senyals del foc, que va enderrocar la coberta.""", \
    """Interior de l'Església del Sagrat Cor de Jesús, la única del Poblenou que nou fou totalment destruïda pel foc el 1936, gràcies als treballadors de les cotxeres del costat que van tenir por que el foc es propagués. En el terra s'observen els senyals del foc, que va enderrocar la coberta.""", \
    """Anunci, esquela a La Vanguardia pel trasllat el 5/3/1928, a l'església del Sagrat Cor de Jesús, de les restes dels germans Laureano Arango Portús (mort el 23/6/1891) i Josefa Arango Portús (morta el 4/1/1918), fundadors de la parròquia per disposició dels seus testaments.""", \
    """Anunci, invitació a la inauguració i benedicció de l'església del Sagrat Cor de Jesús, el 10/6/1926.""", \
    """Façana de l'Església del Sagrat Cor de Jesús""", \
    """Ceràmica d'Olivé Milian, 2002, dedicada a la Mare de Deu de Montserrat, damunt l'entrada a la façana de l'Església del Sagrat Cor de Jesús""", \
    """Pintada de la Guerra 1936-1939 "Viva la FAI y CNT" a l'interior del campanar de l'Església del Sagrat Cor de Jesús. També es poden llegir pintades obcenes com "El cura de esta casa de putas..." o "El cura de esta misa es un maricón...""", \
    """Pintada de la Guerra 1936-1939 "Madrid es nuestro, de las fuerzas leales a la república, y lo será siempre" """, \
    """Pintada de la Guerra 1936-1939, nu femení amb frases obcenes.""", \
    """Única campana conservada, la "Isidra" a l'Església del Sagrat Cor de Jesús. La campana porta els noms de Martina, Isidra i Antònia, i la data de 15/5/19XX""", \
    """Des del campanar de l'Església del Sagrat Cor, la fàbrica cremada de Ca l'Alier al carrer Fluvià-Talsa. A la dreta, Pere IV.""", \
    """Des del campanar de l'Església del Sagrat Cor, la fàbrica cremada de Ca l'Alier al carrer Fluvià-Talsa.""", \
    """Des del campanar de l'Església del Sagrat Cor, el carrer Pere IV. Al fons, la torre AGBAR.""", \
    """Des del campanar de l'Església del Sagrat Cor, panoràmica cap al Besòs. Al fons, les xemeneies, fora d'ús, de la incineradora del Besòs.""", \
    """Des del campanar de l'Església del Sagrat Cor, panoràmica cap al mar. Al fons, la xemeneia de MACOSA i els gratacels de Diagonal Mar. Els camps de la dreta són els únics del Poblenou que no han estat mai edificats.""", \
    """Antics esgrafiats han aparegut sota l'arrebossat de la finca Lacambra""", \
    """Antics esgrafiats han aparegut sota l'arrebossat de la finca Lacambra""", \
    """Hotel ME. Des d'una porta del Parc del Centre, Pere IV, enfront, talla la Diagonal i resta trossejat pel parc.""", \
    """El Poblenou sense gas. L'entrada d'aigua a la xarxa de gas a Pujades 196 obliga a tallar-ne el subministrament a uns 15.000 habitatges des de l'11 al 16/2/2012. Per a reparar-ho Gas Natural va obrir 250 rases, des de Taulat fins a Pere IV.""", \
    """El Poblenou sense gas. L'entrada d'aigua a la xarxa de gas a Pujades 196 obliga a tallar-ne el subministrament a uns 15.000 habitatges des de l'11 al 16/2/2012. Per a reparar-ho Gas Natural va obrir 250 rases, des de Taulat fins a Pere IV.""", \
    """El Poblenou sense gas. L'entrada d'aigua a la xarxa de gas a Pujades 196 obliga a tallar-ne el subministrament a uns 15.000 habitatges des de l'11 al 16/2/2012. Per a reparar-ho Gas Natural va obrir 250 rases, des de Taulat fins a Pere IV.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Panoràmica des d'un terrat del carrer Espronceda. Xemeneia. A l'esquerra habitatges en construcció al carrer Bolívia, al fons l'hotel ME. A la dreta la fàbrica Frigo-Farggi.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Panoràmica des d'un terrat del carrer Espronceda. Xemeneia. Pintada "Salvem Cant Ricart prou especulació". Al fons la fàbrica Frigo-Farggi.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. La torre des d'un terrat del carrer Espronceda. Al fons un tramvia a la Diagonal.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Base de la xemeneia des d'un terrat del carrer Espronceda.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Panoràmica des d'un terrat del carrer Espronceda.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Pintada contra el 22@ "Salvem Cant Ricart prou especulació".""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Xemeneia.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. La torre des d'un terrat del carrer Espronceda.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Panoràmica des d'un terrat del carrer Espronceda. Xemeneia. Al fons la fàbrica Frigo-Farggi.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Panoràmica des d'un terrat del carrer Espronceda. Pintada contra el 22@ "Salvem Cant Ricart prou especulació". Al fons la fàbrica Frigo-Farggi.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Pintada contra el 22@ "Salvem Cant Ricart prou especulació".""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Pintada "31 años aqui y no pagan un euro. Clos/Ricart= lladres""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Interior de les naus.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Interior de les naus.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Interior de les naus.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Interior de les naus.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Interior de les naus.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Interior de les naus.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Interior de les naus.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Interior de les naus.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Xemeneia i naus centrals.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Interior de les naus centrals amb estructura de ferro i fusta per a suportar el sostre de ceràmica.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Interior de les naus centrals amb estructura de ferro i fusta per a suportar el sostre de ceràmica.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. La xemeneia des de l'interior de les naus centrals.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. La xemeneia des de l'interior de les naus centrals.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Panoràmica des d'un terrat interior. Base de la xemeneia. Al fons l'hotel ME.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Panoràmica des d'un terrat interior. Habitatges en construcció al carrer Bolívia. A l'esquerra els habitatges d'Espronceda.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Interior de les naus centrals.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Acumulació d'enderrocs.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Edifici situat a l'entrada pel carrer Bolívia.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Singular edifici per les seves finestres i xemeneies.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Singular edifici per les seves finestres i xemeneies.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Pont de fusta cobert. Al fons l'hotel ME.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Pont de fusta cobert. Al fons la torre.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Singular edifici per les seves finestres i xemeneies.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Panoràmica des de l'edifici en construcció del carrer Bolívia. L'entrada, la plaça, el restaurant. Al fons el Parc Central i l'hotel ME.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Panoràmica des de l'edifici en construcció del carrer Bolívia. L'entrada, la plaça, el restaurant. Al fons el Parc Central i l'hotel ME.""", \
    """Túnel soterrani a Can Ricart""", \
    """Túnel soterrani a Can Ricart. Portes de ferro tancades.""", \
    """Túnel soterrani a Can Ricart. Portes de ferro obertes.""", \
    """Doc en pdf que recull l'acord entre l'alcalde Jordi Hereu amb el Conseller-Director General d’AGBAR, Àngel Simón, per a la rehabilitació, segons projecte d'Antoni Vilanova Omedas (1958-), de la Torre de les Aigües del Besòs i l’Antiga Casa de Vàlvules, construïts entre 1880 i 1882 segons projecte de Pere Falqués i Urpí (1850-1916).""", \
    """Visita a la Torre de les Aigües (Pere Falqués, 1881) rehabilitada per l'arquitecte Antoni Vilanova (centre). A la dreta XXXX, arquitecte de l'equip de Vilanova. A l'esquerra, Jordi Fossas, arquitecte i president de l'AHPN.""", \
    """Làpida a l'església del Sagrat Cor de Jesús, de la sepultura on varen ser traslladades el 5/3/1928 les restes dels germans Laureano Arango Portús (mort el 23/6/1891) i Josefa Arango Portús (morta el 4/1/1918), fundadors de la parròquia per disposició dels seus testaments. El 1936 la tomba fou profanada i les restes cremades al carrer. El que en quedà fou sepultat en un nínxol al cementiri de l'est, però per falta de pagament l'ajuntament el buidà i les restes acabaren a la fossa comú.""", \
    """Interior de l'Església del Sagrat Cor de Jesús, la única del Poblenou que nou fou totalment destruïda pel foc el 1936, gràcies als treballadors de les cotxeres del costat que van tenir por que el foc es propagués. En el terra s'observen els senyals del foc, que va enderrocar la coberta.""", \
    """Empitjora l'estat de Can Ricart després que les administracions aturessin Linguamón i altres projectes. Panoràmica des d'un terrat del carrer Espronceda. Xemeneia. A l'esquerra habitatges en construcció al carrer Bolívia, al fons l'hotel ME. A la dreta la fàbrica Frigo-Farggi."""
    )
    for t in texto:
        print "resumen:", summarize( t )
    
def test_delimiter():
    
    print banner( 'test_delimiter')
    
    tests = ( \
    """Visita a la Torre de les Aigües (Pere Falqués) mucho más texto""", \
    """Visita a la Torre de les Aigües (Pere Falqués con mucho más texto"""
    )
    c = generate_delimiter_re( '\(', '\)' )
    for t in tests:
        m = c.search( t )
        if m is not None:
            print m.group()
        else:
            print "don't match"
    
if __name__ == "__main__":
    #test_delimiter( )
    #test_summary()
    test_main()
