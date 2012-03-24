import pycurl
import gobject
import re

class Curl(gobject.GObject):
    def __init__(self, url = None):
        self.__gobject_init__()

        self.handle = pycurl.Curl()
        self._header_string = None
        self._headers = None
        self._content = None
        self._status = None
        self._return_transfer = True
        self.user_header_callback = None
        self.user_write_callback = None
        self.writedata_option = None

        self.set_url(url)
        # Verify that we've got the right site; harmless on a non-SSL connect.
        self.set_option(pycurl.SSL_VERIFYHOST, 2)
        # Follow redirects in case it wants to take us to a CGI...
        self.set_option(pycurl.FOLLOWLOCATION, 1)
        self.set_option(pycurl.MAXREDIRS, 5)
        self.set_option(pycurl.NOSIGNAL, 1)
        # Setting this option with even a nonexistent file makes libcurl
        # handle cookie capture and playback automatically.
        self.set_option(pycurl.COOKIEFILE, "/dev/null")

        self.handle.setopt(pycurl.HEADERFUNCTION, self._default_header_callback)
        self.handle.setopt(pycurl.WRITEFUNCTION, self._default_write_callback)

    def _default_header_callback(self, d):
        self._header_string += d

        if d == "\r\n":
            self.emit("header-downloaded")

        if self.user_header_callback != None:
            return self.user_header_callback(d)

    def _default_write_callback(self, d):
        if self._return_transfer == True:
            self._content += d

        if self.writedata_option != None:
            self.writedata_option.write(d)

        if self.user_write_callback != None:
            return self.user_write_callback(d)

    def get_header_string(self):
        return self._header_string

    def get_headers(self):
        if self._headers == None:
            data = self._header_string.split("\r\n")
            matches = re.match(r"HTTP/\d\.\d (\d+)", data[0])
            if matches:
                self._status = int(matches.group(1))

            del data[0]
            self._headers = {}
            for httpfield in data:
                httpfield = httpfield.split(":")
                if len(httpfield) > 1:
                    httpkey = httpfield[0].lower().strip()
                    httpvalue = httpfield[1].strip()
                    self._headers[httpkey] = httpvalue

        return self._headers

    def get_status(self):
        self.get_headers()
        return self._status

    def set_timeout(self, timeout):
        "Set timeout for a retrieving an object"
        self.set_option(pycurl.TIMEOUT, timeout)

    def set_url(self, url):
        "Set the URL to be retrieved."
        self.set_option(pycurl.URL, url)

    def set_option(self, option, value):
        "Set an option on the retrieval."
        if option == pycurl.HEADERFUNCTION:
            self.user_header_callback = value
        elif option == pycurl.WRITEFUNCTION:
            self.user_write_callback = value
        elif option == pycurl.WRITEDATA:
            self.writedata_option = value
        else:
            self.handle.setopt(option, value)

    def setopt(self, option, value):
        "Set an option on the retrieval."
        self.set_option(option, value)

    def get_info(self, *args):
        "Get information about retrieval."
        return apply(self.handle.getinfo, args)

    def getinfo(self, *args):
        "Get information about retrieval."
        return apply(self.handle.getinfo, args)

    def set_return_transfer(self, enable):
        self._return_transfer = bool(enable)

    def get_return_transfer(self):
        return self._return_transfer

    def perform(self):
        if self._return_transfer == True:
            self._content = ""
        else:
            self._content = None
        self._header_string = ""
        self._headers = None
        self._status = None
        self.handle.perform()

        return self._content

    def get_content(self):
        return self._content

    def info(self):
        "Return a dictionary with all info on the last response."
        m = {}
        m['effective-url'] = self.handle.getinfo(pycurl.EFFECTIVE_URL)
        m['http-code'] = self.handle.getinfo(pycurl.HTTP_CODE)
        m['total-time'] = self.handle.getinfo(pycurl.TOTAL_TIME)
        m['namelookup-time'] = self.handle.getinfo(pycurl.NAMELOOKUP_TIME)
        m['connect-time'] = self.handle.getinfo(pycurl.CONNECT_TIME)
        m['pretransfer-time'] = self.handle.getinfo(pycurl.PRETRANSFER_TIME)
        m['redirect-time'] = self.handle.getinfo(pycurl.REDIRECT_TIME)
        m['redirect-count'] = self.handle.getinfo(pycurl.REDIRECT_COUNT)
        m['size-upload'] = self.handle.getinfo(pycurl.SIZE_UPLOAD)
        m['size-download'] = self.handle.getinfo(pycurl.SIZE_DOWNLOAD)
        m['speed-upload'] = self.handle.getinfo(pycurl.SPEED_UPLOAD)
        m['header-size'] = self.handle.getinfo(pycurl.HEADER_SIZE)
        m['request-size'] = self.handle.getinfo(pycurl.REQUEST_SIZE)
        m['content-length-download'] = self.handle.getinfo(pycurl.CONTENT_LENGTH_DOWNLOAD)
        m['content-length-upload'] = self.handle.getinfo(pycurl.CONTENT_LENGTH_UPLOAD)
        m['content-type'] = self.handle.getinfo(pycurl.CONTENT_TYPE)
        m['response-code'] = self.handle.getinfo(pycurl.RESPONSE_CODE)
        m['speed-download'] = self.handle.getinfo(pycurl.SPEED_DOWNLOAD)
        m['ssl-verifyresult'] = self.handle.getinfo(pycurl.SSL_VERIFYRESULT)
        m['filetime'] = self.handle.getinfo(pycurl.INFO_FILETIME)
        m['starttransfer-time'] = self.handle.getinfo(pycurl.STARTTRANSFER_TIME)
        m['redirect-time'] = self.handle.getinfo(pycurl.REDIRECT_TIME)
        m['redirect-count'] = self.handle.getinfo(pycurl.REDIRECT_COUNT)
        m['http-connectcode'] = self.handle.getinfo(pycurl.HTTP_CONNECTCODE)
        m['httpauth-avail'] = self.handle.getinfo(pycurl.HTTPAUTH_AVAIL)
        m['proxyauth-avail'] = self.handle.getinfo(pycurl.PROXYAUTH_AVAIL)
        m['os-errno'] = self.handle.getinfo(pycurl.OS_ERRNO)
        m['num-connects'] = self.handle.getinfo(pycurl.NUM_CONNECTS)
        m['ssl-engines'] = self.handle.getinfo(pycurl.SSL_ENGINES)
        m['cookielist'] = self.handle.getinfo(pycurl.INFO_COOKIELIST)
        m['lastsocket'] = self.handle.getinfo(pycurl.LASTSOCKET)
        m['ftp-entry-path'] = self.handle.getinfo(pycurl.FTP_ENTRY_PATH)
        return m

    def close(self):
        "Close a session, freeing resources."
        if self.handle:
            self.handle.close()
        self.handle = None
        self._header_string = None
        self._headers = None
        self._status = None
        self._content = None
        self.user_header_callback = None
        self.user_write_callback = None

    def __del__(self):
        self.close()

gobject.type_register(Curl)
gobject.signal_new("header-downloaded", Curl, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
