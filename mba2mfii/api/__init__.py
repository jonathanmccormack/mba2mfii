# -*- coding: utf-8 -*-

import os
import logging
import json

from six import integer_types, string_types, iteritems

from mba2mfii.tools import json_decode

from .legacy import SKLegacyExport
from .modern import SKModernExport

__all__     =   [ 'SKFileExport', 'SKLegacyExport', 'SKModernExport' ]



class SKFileExport(object):

    # TODO: Detect app based upon metadata
    sk_app_versions =   {
        'legacy':   lambda ddict: ddict.get('enterprise_id') == 'FCC_Public',
        'modern':   lambda ddict: ddict.get('device_environment') is not None
    }

    def __init__(self, fp, **kwargs):
        """
        """
        import os
        import logging
        import json
        from six import integer_types, string_types

        self.logger =   logging.getLogger(__name__)

        if isinstance(fp, string_types):
            if not os.path.isfile(fp):
                raise TypeError('invalid file pointer: {0!r}'.format(fp))
            else:
                fp = open(fp, 'r')

        if not hasattr(fp, 'read'):
            raise TypeError('invalid file pointer: {0!r}'.format(fp))

        if 'b' in fp.mode:
            raise TypeError('invalid file pointer: {0!r} (binary mode detected)'.format(fp))

        #self.logger.debug('loading file: {0!r}'.format(fp))
        json_data   =   json.load(fp, object_hook=json_decode)

        if isinstance(json_data, list):
            if len(json_data) > 1:
                self.logger.warn('multiple submissions detected')

            json_data   =   next((data for data in json_data), dict())

        if isinstance(json_data, dict):
            self.data   =   json_data
        else:
            self.logger.error('unexpected data type returned from json.load:%s', type(json_data))
            raise ValueError('json_data must be a list of dicts or dict')

        if self.is_legacy_app:
            self.export = SKLegacyExport(data=self.data, **kwargs)
        elif self.is_modern_app:
            self.export = SKModernExport(data=self.data, **kwargs)
        else:
            raise ValueError('cannot detect valid FCC Speed Test app export data')


    def check_app_version(self):
        """
        """
        for version, fn in iteritems(self.sk_app_versions):
            if callable(fn):
                if fn(self.data):
                    return version
            else:
                self.logger.warn('invalid version:%s in sk_app_versions -- value is not callable:%s', version, fn)
        self.logger.error('cannot detect valid FCC Speed Test app export data')


    @property
    def is_legacy_app(self):
        """
        """
        return (self.check_app_version() == 'legacy')


    @property
    def is_modern_app(self):
        """
        """
        return (self.check_app_version() == 'modern')


    def to_dataframe(self, *args, **kwargs):
        return self.export.to_dataframe(*args, **kwargs)


#
