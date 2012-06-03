# File: YahooTermExtraction.py
#
# An interface to Yahoo's Term Extraction service:
#
# http://developer.yahoo.net/search/content/V1/termExtraction.html
#
# "The Term Extraction Web Service provides a list of significant
# words or phrases extracted from a larger content."
#

import urllib
try:
    from xml.etree import ElementTree # 2.5 and later
except ImportError:
    from elementtree import ElementTree

URI = "http://api.search.yahoo.com"
URI = URI + "/ContentAnalysisService/V1/termExtraction"

def termExtraction(appid, context, query=None):
    d = dict(
        appid=appid,
        context=context.encode("utf-8")
        )
    if query:
        d["query"] = query.encode("utf-8")
    result = []
    f = urllib.urlopen(URI, urllib.urlencode(d))
    for event, elem in ElementTree.iterparse(f):
        if elem.tag == "{urn:yahoo:cate}Result":
            result.append(elem.text)
    return result
    
def main( argv=None ):
    if argv is None:
        argv = sys.argv
        
    parser = OptionParser(usage="%prog [-f] [-q] <free-form date string>", version=str(__version__))
    parser.add_option("-f", "--force-update",
                      action='store_true', dest="force_update", default=False,
                      help="force self-updating of TRANSLATION_DICT in this file", metavar="FILE")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print debug messages to stdout")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("you have missed query string")
    date_string = args[0]
    
    # extract terms
    appid = 
    termExtraction(appid, text)[-5:]
    
if __name__ == "__main__":
    """>>> from YahooTermExtraction import termExtraction
    >>> appid = "/your app id/"
    >>> uri = "/some uri/"
    >>> text = urllib.urlopen(uri).read()
    >>> termExtraction(appid, text)[-5:]
    ['horrible picture', 'logo', 'spammer', 'moron', 'cat mouse']
    """
    sys.exit(main())
    