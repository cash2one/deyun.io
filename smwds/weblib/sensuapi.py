import requests
import logging
import os
import datetime
try:
    from urllib.request import HTTPHandler, Request, urlopen, \
        install_opener, build_opener
    from urllib.error import HTTPError, URLError
    import urllib.parse as urlparse
except ImportError:
    from urllib2 import HTTPHandler, Request, urlopen, install_opener, build_opener, \
        HTTPError, URLError
    import urlparse

logger = logging.getLogger('api')


class SensuAPI_Exception(Exception):
    def __init__(self, message, statuscode):
    
        # Call the base class constructor with the parameters it needs
        super(SensuAPI_Exception, self).__init__(message)
    
        self.statuscode = statuscode






class SensuAPI(object):
    
    def __init__(self, api_url='https://localhost:4567'):

        self.api_url = api_url


    def test(self):
        url = self.api_url + '/clients'
        params = {'url': url,
          'verify': False,
          }
        try:
            resp = requests.get(**params)
        except Exception as e:
            if resp.status_code == 401:
                raise SensuAPI_Exception('Authentication denied', statuscode=resp.status_code)
            if resp.status_code == 500:
                raise SensuAPI_Exception('server error', statuscode=resp.status_code)
            if resp.status_code == 404:
                raise SensuAPI_Exception('not found', statuscode=resp.status_code)
            logger.error('Error with request: {0}'.format(e))
            return
        if resp.status_code ==  200:
            logger.info('Test Comlpeted with sucess.')
            return True
        else:
            return False

    def get(self, path):
        '''
        A thin wrapper from get http method of sensuapi
        '''       
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        }
        params = {'url': self._construct_url(path),
                  'headers': headers,
                  'verify': False,
                  }
        try:
            resp = requests.get(**params)           
        except Exception as e:
            if resp.status_code == 401:
                raise SensuAPI_Exception('Authentication denied', statuscode=resp.status_code)
            if resp.status_code == 500:
                raise SensuAPI_Exception('server error', statuscode=resp.status_code)
            if resp.status_code == 404:
                raise SensuAPI_Exception('not found', statuscode=resp.status_code)
            logger.error('Error with request: {0}'.format(e))
            return
        return resp.json()

    def _construct_url(self, path):
        
        relative_path = path.lstrip('/')
        return urlparse.urljoin(self.api_url, relative_path)