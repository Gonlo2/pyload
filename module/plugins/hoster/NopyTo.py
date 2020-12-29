# -*- coding: utf-8 -*-

import re
from enum import Enum

from module.network.RequestFactory import getURL as get_url

from ..internal.misc import json
from ..internal.SimpleHoster import SimpleHoster


class NopyStatus(Enum):
    OK = 0
    WARNING = 1
    ERROR = 2
    FATAL_ERROR = 3


class NopyTo(SimpleHoster):
    __name__ = "NopyTo"
    __type__ = "hoster"
    __version__ = "0.1"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?nopy\.to/(?P<ID>.+?)/(?P<FN>.+)'

    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Nopy.to hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Gonlo2", "https://github.com/Gonlo2")]

    @classmethod
    def api_info(cls, url):
        info = {}

        m = re.search(cls.__pattern__, url)
        if m is None:
            info['status'] = 8
            info['error'] = _("The provided url isn't valid")
            return info

        file_id = m.group('ID')
        file_name = m.group('FN')

        data = json.loads(get_url("https://data.nopy.to/file",
                                  post={'code': file_id, 'file': file_name},
                                  decode=True))

        status, msg = cls._check_file_error(data)
        if status != NopyStatus.OK:
            if status == NopyStatus.ERROR:
                info['status'] = 6
                info['error'] = _(msg)
                return info
            if status == NopyStatus.FATAL_ERROR:
                info['status'] = 8
                info['error'] = _(msg)
                return info
            cls.log_warning(_(msg))

        info['status'] = 2
        info['name'] = data['msg']['filename']
        info['size'] = data['msg']['raw_size']

        info['nopy'] = {'code': file_id}
        for x in ('fid', 'request', 'session'):
            info['nopy'][x] = data['msg'][x]

        return info

    def handle_free(self, pyfile):
        if 'nopy' not in self.info:
            self.error(_("Missing nopy data"))

        data = json.loads(get_url("https://data.nopy.to/download",
                                  post=self.info['nopy'],
                                  decode=True))

        status, msg = self._check_request_error(data)
        if status != NopyStatus.OK:
            self.error(_(msg))

        self.link = self.fixurl(data['msg']['download'])

    @classmethod
    def _check_file_error(cls, data):
        status, msg = cls._check_request_error(data)
        if status != NopyStatus.OK:
            return (status, msg)

        payload = data['msg']

        if payload['error_fatal']:
            if 'offline' in payload['errors']:
                return (NopyStatus.ERROR, 'this file cluster is offline, please try again later')
            elif 'uploading' in payload['errors']:
                return (NopyStatus.ERROR, 'file is still being uploaded, please try again later')
            return (NopyStatus.ERROR, 'server error, please try again later')

        if payload['errors']:
            if 'offline' in payload['errors']:
                return (NopyStatus.WARNING, 'some file servers are offline, speeds may be impacted')
            elif 'uploading' in payload['errors']:
                return (NopyStatus.WARNING, 'file is being distributed across cluster, speeds may be impacted')
            elif 'capacity' in payload['errors']:
                return (NopyStatus.WARNING, 'file cluster is over capacity, speeds may be impacted')
            return (NopyStatus.WARNING, "unknown warning id '{}'".format(payload['errors'][0]))

        return (NopyStatus.OK, '')

    @classmethod
    def _check_request_error(cls, data):
        if data['status'] == 'error':
            return (NopyStatus.FATAL_ERROR, data['msg'])
        return (NopyStatus.OK, '')
