"""
Generate SQL update commands to update keywords

Input: CSV file. Columns are those of the g2_Item table
Output: SQL commands
"""

import csv


filename = 'authors.csv'

database = 'db271970365'

print "use %s;" % database
print

for i in csv.DictReader( open( filename ),delimiter=';',fieldnames=[ str(n) for n in xrange(0,5)] ):
    # print repr( i )
    keywords = i['3']
    # print keywords
    s = "update g2_Item set g_keywords = '%s' where g_id = %s;" % \
         ( unicode( i['3'].replace( "'", r"\'"), 'utf-8'), i['0'] )
    print s.encode( 'utf-8' )
        
        

