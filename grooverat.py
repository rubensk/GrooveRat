import gzip
import pycurl
import json
import threading
import gobject
import uuid 
import random 
import string
import hashlib 
import ipycurl
import StringIO
import gst
import pygst
from enviroment import env

def isInitialized():
    return _isInitialized

def dummy(error = None):
    pass

h = {}
h["country"] = {}
h["country"]["CC1"] = "0"
h["country"]["CC2"] = "0"
h["country"]["CC3"] = "0"
h["country"]["IPR"] = "1"
h["country"]["CC4"] = "0"
h["country"]["ID"] = "1"
h["privacy"] = 0
h["session"] = None
h["uuid"] = str.upper(str(uuid.uuid4()))

_initializingLock = threading.Lock()
_initFailed = False
_isInitialized = False
_onInitStart = dummy
_onInitError = dummy
_onInitFinish = dummy
_token = '' 
_referer = "http://grooveshark.com/JSQueue.swf?20111111.111"
_player = None

def getToken():
    """
    Gets a token from the grooveshark.com service
    """
    global h, _token
    p = {}
    p["parameters"] = {}
    p["parameters"]["secretKey"] = hashlib.md5(h["session"]).hexdigest()
    p["method"] = "getCommunicationToken"
    p["header"] = h
    p["header"]["client"] = "htmlshark"
    p["header"]["clientRevision"] = "20120220"

    conn = createCurl("https://grooveshark.com/more.php?" + p["method"])
    conn.setopt(pycurl.POST, True)
    conn.setopt(pycurl.POSTFIELDS, json.JSONEncoder().encode(p))
    conn.setopt(pycurl.HTTPHEADER, [
        "Referer: " + _referer,
        "Accept-Encoding: gzip",
        "Content-Type: application/json"
    ])
    resp = conn.perform()
    conn.close()

    gzipfile = gzip.GzipFile(fileobj = (StringIO.StringIO(resp)))
    _token = json.JSONDecoder().decode(gzipfile.read())["result"]


def createCurl(url = None):
    """
    Create a configurated cURL object
    """
    c = ipycurl.Curl(url)
    c.setopt(pycurl.USERAGENT, env().USER_AGENT)
    c.set_option(pycurl.FAILONERROR, True)

    c.setopt(pycurl.COOKIEFILE, env().get_config_directory() + "/cookie.txt")
    c.setopt(pycurl.COOKIEJAR, env().get_config_directory() + "/cookie.txt")
    c.set_timeout(50)

    proxy = env().get_proxy()
    if proxy != None:
        c.setopt(pycurl.PROXY, proxy["host"])
        c.setopt(pycurl.PROXYPORT, int(proxy["port"]))
        if proxy["user"] != None:
            c.setopt(pycurl.PROXYUSERPWD, proxy["user"] + ":" + proxy["pass"])
    else:
        c.setopt(pycurl.PROXY, "")

    return c

def prepToken(method, sectoken):
    """
    Method to create the tocken for the request.
    """
    rnd = (''.join(random.choice(string.hexdigits) for x in range(6))).lower()
    hashs = hashlib.sha1(
        method + ":" + _token + sectoken + rnd).hexdigest()
    ret = rnd + hashs
    return ret

def getSearchResultsEx(query, _type = "Songs"):
    """
    Method to get the search results from the gs service
    and returns them as dictionary.
    """
    init()

    p = {}
    p["parameters"] = {}
    p["parameters"]["type"] = _type
    p["parameters"]["query"] = query
    p["header"] = h
    p["header"]["client"] = "htmlshark"
    p["header"]["clientRevision"] = "20120220"
    p["header"]["token"] = prepToken("getResultsFromSearch", ":jayLikeWater:")
    p["method"] = "getResultsFromSearch"

    conn = createCurl("https://grooveshark.com/more.php?" + p["method"])
    conn.setopt(pycurl.POST, True)
    conn.setopt(pycurl.POSTFIELDS, json.JSONEncoder().encode(p))
    conn.setopt(pycurl.HTTPHEADER, [
        "Referer: http://grooveshark.com/",
        "Accept-Encoding: gzip",
        "Content-Type: application/json"
    ])
    resp = conn.perform()
    conn.close()

    gzipfile = gzip.GzipFile(fileobj = (StringIO.StringIO(resp)))
    j = json.JSONDecoder().decode(gzipfile.read())
    result = j['result']['result']
    if hasattr(result, 'Songs'):
        return result['Songs']
    else:
        return result

def init():
    global _isInitialized, _initFailed

    _initializingLock.acquire()
    if isInitialized():
        _initializingLock.release()
        if _initFailed == True:
            raise Exception(_("Grooveshark is not initialized"))
        return

    print "[Initializing Grooveshark]"
    gobject.idle_add(_onInitStart)
    while True:
        try:
           conn = createCurl("http://grooveshark.com/")
           conn.perform()

           cookielist = conn.get_info(pycurl.INFO_COOKIELIST)
           for cookie in cookielist:
               cookie = cookie.split("\t")
               if cookie[5] == "PHPSESSID":
                   h["session"] = cookie[6]

           conn.close()
           getToken()
           print "[Grooveshark initialized]"
           break
        except Exception as e:
            if e.args[0] == 11004:
                time.sleep(1)
            else:
                print "[Grooveshark initialized failed]"
                _initFailed = True
                gobject.idle_add(_onInitError, e.__str__())
                break

    _isInitialized = True
    _initializingLock.release()
    gobject.idle_add(_onInitFinish)

    if _initFailed == True:
        #raise Exception(_("Grooveshark is not initialized"))
	print "error"

def getStreamKeyFromSongIDEx(_id):
    """
    Gets the stream URL for Song ID
    """
    init()

    p = {}
    p["parameters"] = {}
    p["parameters"]["mobile"] = "false"
    p["parameters"]["prefetch"] = "false"
    p["parameters"]["songIDs"] = _id
    p["parameters"]["country"] = h["country"]
    p["header"] = h
    p["header"]["client"] = "jsqueue"
    p["header"]["clientRevision"] = "20120220.01"
    p["header"]["token"] = prepToken("getStreamKeysFromSongIDs", ":bangersAndMash:")
    p["method"] = "getStreamKeysFromSongIDs"

    conn = createCurl("https://grooveshark.com/more.php?" + p["method"])
    conn.setopt(pycurl.POST, True)
    conn.setopt(pycurl.POSTFIELDS, json.JSONEncoder().encode(p))
    conn.setopt(pycurl.HTTPHEADER, [
        "Referer: " + _referer,
        "Accept-Encoding: gzip",
        "Content-Type: application/json"
    ])
    resp = conn.perform()
    conn.close()

    gzipfile = gzip.GzipFile(fileobj = (StringIO.StringIO(resp)))
    j = json.JSONDecoder().decode(gzipfile.read())

    if len(j["result"][str(_id)]) == 0:
        raise Exception("The song streaming key is empty")

    return j

#def play_uri(uri):
def set_player():
    global _player

    #mainloop = gobject.MainLoop()
    _player = gst.element_factory_make("playbin", "player")
  
    #print 'Playing:', uri
    #_player.set_property('uri', uri)
    #_player.set_state(gst.STATE_PLAYING)

    #mainloop.run()

def play_uri(uri):
    global _player

    _player.set_state(gst.STATE_NULL)
    _player.set_property('uri', uri)
    _player.set_state(gst.STATE_PLAYING)

t = threading.Thread(target=set_player)
t.start()

lista = []

while True:
    srch = raw_input('Patron de busqueda: ')
    if srch == "":
        if len(lista) == 0:
	    continue
    else:
        lista = getSearchResultsEx(srch)
        lista.reverse()

    i = len(lista) 
    for row in lista:
    	print "%s- %s - %s" % (i, row['ArtistName'], row['SongName'])
    	i -= 1
    
    lista.reverse()
    sel = raw_input('Seleccione un numero: ')
    if sel == "":
        continue
    id = str(lista[int(sel)-1]['SongID'])
    print str(lista[int(sel)-1]['SongName'])
    key = getStreamKeyFromSongIDEx(id)
    playurls = "http://%s/stream.php?streamKey=%s"
    play_url = playurls % (key["result"][id]["ip"],
                           key["result"][id]["streamKey"])
    
    play_uri(play_url)
