# -*- coding: utf-8 -*-
from builtins import _

from pyload.network.http_request import BadHeader
from pyload.plugins.hoster.Http import Http

# Support onlinetvrecorder.com


class OnlineTvRecorder(Http):
    __name__ = "OnlineTvRecorder"
    __type__ = "hoster"
    __version__ = "0.05"
    __status__ = "testing"

    # RIPE Database:
    # inetnum: 81.95.11.0 - 81.95.11.63
    # route:   81.95.8.0/21
    # additional: 93.115.84.162
    __pattern__ = r"https?://(81\.95\.11\.\d{1,2}|93\.115\.84\.162|download\d{1,2}.onlinetvrecorder.com)/download/\d+/\d+/\d*/[0-9a-f]+/.+"
    __config__ = [("activated", "bool", "Activated", True)]
    __description__ = """OnlineTvRecorder hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Tim Gregory", "bogeyman@valar.de")]

    def setup(self):
        # OnlineTvRecorder policy
        self.multiDL = False
        self.chunk_limit = 1
        self.resume_download = True

    def process(self, pyfile):
        try:
            return Http.process(self, pyfile)

        except BadHeader as e:
            self.log_debug("OnlineTvRecorder httpcode: {}".format(e.code))
            if e.code == 503:
                # max queueing for 3 hours
                self.retry(360, 30, _("Waiting in download queue"))