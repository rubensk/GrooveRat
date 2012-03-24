import sys
import os
import locale
import gettext
import glib
import libproxy
import ipycurl
import pycurl
import gtk
from configobj import ConfigObj

class Enviroment:
    """
    This class represent the execution enviroment and configuration
    of the app. Is a singleton class an the instance should be accessed
    using the env() function.
    """

    def __init__(self):
        # Application name
        self.APP = 'gsharkdown'

        self.VERSION = None

        # Data for use Last.fm API
        self.LASTFM_KEY = "51fd71dc8939360b25a1029e556258a4"
        self.LASTFM_SECRET = "cf35dd38f998ca4d3af4adbe59ae23f7"

        # URL to check for updates
        self.UPDATE_URL = "http://bitbucket.org/vkolev/gsharkdown/raw/latest/VERSION"
        self.DONATE_URL = "https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=427TQGWLEXXFQ&lc=AR&item_name=gSharkDown&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donate_LG%2egif%3aNonHosted"

        ### The following attributes should be initialized on initialize method ###
        # Application base path
        self.BASEPATH = None

        # Dependencies information
        self.HAVE_NOTIFY = None
        self.HAVE_PYLAST = None
        self.HAVE_INDICATOR = None

        # Directory for i18n files
        self.LOCALE_DIR = None

        # User agent for HTTP requests
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/10.0"

        # The application object (SharkDown instance)
        self._app = None

        # The config object
        self._config = None

        # The proxy data
        self._proxy = None

    def app(self):
        return self._app

    def set_app(self, app):
        self._app = app

    def config(self):
        return self._config

    def set_config(self, config):
        self._config = config

    def get_config_directory(self):
        return "%s/.gsharkdown" % os.environ.get("HOME")

    def get_config_filename(self):
        """
        Returns the filename for the configuration file
        """
        return "%s/gsharkdown.ini" % self.get_config_directory()

    def get_default_down_path(self):
        """
        Returns the default download path.
        """
        music_dir = glib.get_user_special_dir(glib.USER_DIRECTORY_MUSIC) or os.path.join(os.environ.get("HOME"), "Music")
        return os.path.join(music_dir, "Grooveshark")

    def config_defaults(self):
        return {
            'show_stat_icon': 0,
            'repeat_playlist': 1,
            'shuffle_playlist': 0,
            'show_notification': 0,
            'update_checked': 0,
            'completition': "",
            'scrobbling': 0,
            'lastuser': "",
            'lastpass': "",
            'startup_update_check': 1,
            'quit_without_confirmation': 1,
            'speed_limit': 0,
            'file_pattern': "{artist} - {song}",
            'down_path': self.get_default_down_path(),
            'playlist_style': 0,
            'proxy_enabled': 'auto',
            'proxy_host': '',
            'proxy_port': '',
            'proxy_user': '',
            'proxy_pass': '',
            'cover_cache_limit': 16 * 1024 * 1024,
        }

    def _safe_create_dirs(self, dirs):
        if os.path.isdir(dirs) == False:
            try:
                os.makedirs(dirs)
            except:
                pass

    def initialize(self):
        """
        Initialize the enviroment
        """
        # Initialize i18n variables
        if os.path.exists("%s/locale" % self.BASEPATH):
            self.LOCALE_DIR = "%s/locale" % self.BASEPATH
        else:
            self.LOCALE_DIR = os.path.join(sys.prefix, 'share', 'locale')

        try:
            locale.setlocale(locale.LC_ALL, '')
        except locale.Error:
            locale.setlocale(locale.LC_ALL, 'en_US.utf8')
        locale.bindtextdomain(self.APP, self.LOCALE_DIR)
        locale.bind_textdomain_codeset(self.APP, 'UTF-8')
        gettext.bindtextdomain(self.APP, self.LOCALE_DIR)
        gettext.textdomain(self.APP)
        gettext.install(self.APP, localedir = self.LOCALE_DIR, unicode = True)

        # Initialize the Version number
        version = open("%s/VERSION" % self.BASEPATH, 'r')
        self.VERSION = version.readline()
        version.close()

        # Initialize configuration
        config = ConfigObj(self.config_defaults())
        config.filename = self.get_config_filename()
        user_config = ConfigObj(self.get_config_filename())

        config.merge(user_config)

        self._safe_create_dirs(self.get_config_directory())
        self._safe_create_dirs(config['down_path'])
        self._safe_create_dirs(os.path.join(self.get_config_directory(), "covers"))

        config.write()
        self.set_config(config)

        # Initialize proxy
        # To avoid requests problems with Grooveshark, the proxy is initialized
        # one time and user needs to restart gSharkDown in order to use a new
        # proxy. This should be fixed!
        self.refresh_proxy()

    def have_notify(self):
        return int(config()['show_notification']) == 1 and env().HAVE_NOTIFY

    def have_pylast(self):
        return int(config()['scrobbling']) == 1 and env().HAVE_PYLAST

    def have_playlist_style(self):
        v = gtk.pygtk_version
        return v[0] >= 2 and v[1] >= 22

    def refresh_proxy(self):
        if config()["proxy_enabled"] == "auto":
            self._proxy = self.get_system_proxy()
        elif config()["proxy_enabled"] == "1":
            if config()["proxy_host"] == "":
                self._proxy = None
            else:
                self._proxy = {}
                self._proxy["host"] = config()["proxy_host"]
                self._proxy["port"] = config()["proxy_port"]
                if config()["proxy_user"] == "":
                    self._proxy["user"] = None
                    self._proxy["pass"] = None
                else:
                    self._proxy["user"] = config()["proxy_user"]
                    self._proxy["pass"] = config()["proxy_pass"]
        else:
            self._proxy = None

    def get_system_proxy(self):
        if os.environ.has_key("HTTP_PROXY") and os.environ.get("HTTP_PROXY") != "":
            proxy_url = "http://" + os.environ.get("http_proxy")
        else:
            proxy_factory = libproxy.ProxyFactory()
            proxy_url = proxy_factory.getProxies("http://grooveshark.com")[0]

        if proxy_url == "direct://":
            proxy = None
        else:
            proxy_url = proxy_url.replace("http://", "")
            if proxy_url.find(":") == -1:
                proxy_url += ":8080"

            proxy = {}
            proxy["host"] = proxy_url.split(":")[0]
            proxy["port"] = proxy_url.split(":")[1].replace('/', '')
            proxy["user"] = None
            proxy["pass"] = None

        return proxy

    def get_proxy(self):
        return self._proxy

enviroment_singleton = Enviroment()

def env():
    global enviroment_singleton
    return enviroment_singleton

def app():
    return env().app()

def config():
    return env().config()
