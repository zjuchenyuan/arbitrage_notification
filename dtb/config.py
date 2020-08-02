import os
from urllib import parse
from typing import Generic, TypeVar
from .utils import instance


class Config(object):
    @property
    def url(self): pass


class WebhookConfig(Config):
    def __init__(self, webhook):
        self._webhook = webhook

    @property
    def url(self):
        return self._webhook


class BaseAuthConfig(Config):
    def __init__(self, base_url, **auth):
        self._base_url = base_url
        self._auth = auth

    @property
    def url(self):
        return self._base_url + '?' + parse.urlencode(self._auth)


@instance()
class EnvironConfig(object):
    def __getitem__(self, ConfigCls):
        def create(*args, **kwargs):
            return ConfigCls(*(os.environ[arg] for arg in args), **{kw: os.environ[arg] for kw, arg in kwargs.items()})
        return create
