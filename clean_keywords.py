

import csv


filename = 'g2_ChildEntity.csv'
folders = {}

def read_folders( filename ):
    global folders
    folders = {}
    try:
        for d in csv.DictReader(open(filename),fieldnames=['0','1']):
            folders[ d['0'] ] = d['1']
    except:
        pass

read_folders( 'carpetes.csv' )

database = 'db271970365'

print "use %s;" % database
print

for i in csv.DictReader( open( filename ),delimiter=';',fieldnames=[ str(n) for n in xrange(0,3)] ):
    keywords = i['2'].split( ',' )
    keywords.insert( 0, i['0'] )
    if len(keywords)> 2 and keywords[2] != '':
        # Search for folder name
        folder_number = keywords[2]
        folder_name = folders.get( folder_number, "")
        if folder_name != "":
           keywords.append( folder_name )
        # print keywords
        s = "update g2_Item set g_keywords = '%s' where g_id = %s;" % ( ",".join( [ unicode( keyword, 'utf-8') for keyword in keywords[1:] ] ).replace( "'", r"\'"), keywords[0] )
        print s.encode( 'utf-8' )
        
        

