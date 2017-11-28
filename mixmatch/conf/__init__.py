import os
import sys
from ConfigParser import SafeConfigParser

from ..core.exceptions import ImproperlyConfigured
from ..utils.functional import LazyObject, empty

ENVIRONMENT_SETTINGS = "READER_SETTINGS"
BASE_DIR = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(sys.argv[0]))
# BASE_DIR = os.path.dirname(sys.executable)


class LazySettings(LazyObject):
    """
    A lazy proxy for either global Reader settings or a custom settings object.
    The user can manually configure settings prior to using them. Otherwise,
    Reader uses the settings module pointed to by ENVIRONMENT_SETTINGS.
    """

    def _setup(self, name=None):
        """
        Load the settings module pointed to by the environment variable. This
        is used the first time we need any settings at all, if the user has not
        previously configured the settings manually.
        """
        settings_module = os.environ.get(ENVIRONMENT_SETTINGS)
        if not settings_module:
            desc = ("setting %s" % name) if name else "settings"
            raise ImproperlyConfigured(
                "Requested %s, but settings are not configured. "
                "You must either define the environment variable %s "
                "or call settings.configure() before accessing settings."
                % (desc, ENVIRONMENT_SETTINGS))

        self._wrapped = Settings(settings_module)

    def __repr__(self):
        # Hardcode the class name as otherwise it yields 'Settings'.
        if self._wrapped is empty:
            return '<LazySettings [Unevaluated]>'
        return '<LazySettings "%(settings_module)s">' % {
            'settings_module': self._wrapped.SETTINGS_MODULE,
        }

    def __getattr__(self, name):
        """
        Return the value of a setting and cache it in self.__dict__.
        """
        if self._wrapped is empty:
            self._setup(name)
        val = getattr(self._wrapped, name)
        self.__dict__[name] = val
        return val

    def __setattr__(self, name, value):
        """
        Set the value of setting. Clear all cached values if _wrapped changes
        (@override_settings does this) or clear single values when set.
        """
        if name == '_wrapped':
            self.__dict__.clear()
        else:
            self.__dict__.pop(name, None)
        super(LazySettings, self).__setattr__(name, value)

    def __delattr__(self, name):
        """
        Delete a setting and clear it from cache if needed.
        """
        super(LazySettings, self).__delattr__(name)
        self.__dict__.pop(name, None)


class Settings(object):
    def __init__(self, settings_module):
        # update the dict from global settings
        self.SETTINGS_MODULE = os.path.join(BASE_DIR, os.environ.get(ENVIRONMENT_SETTINGS))
        # Load properties file
        reader_config = SafeConfigParser()
        reader_config.read(self.SETTINGS_MODULE)
        for section in reader_config.sections():
            setattr(self, section, dict(reader_config.items(section)))

    def __repr__(self):
        return '<%(cls)s "%(settings_module)s">' % {
            'cls': self.__class__.__name__,
            'settings_module': self.SETTINGS_MODULE
        }


settings = LazySettings()

__all__ = ['settings']
