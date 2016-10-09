import requests
import logging
import os
import datetime
logger = logging.getLogger('api')


class SensuAPI_Exception(Exception):
    pass


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
            if resp.status_code == 401:
                raise SensuAPI_Exception(str(resp.status_code) +
                                    ':Authentication denied')
                return

            if resp.status_code == 500:
                raise SensuAPI_Exception(str(resp.status_code) + ':Server error.')
                return

            if resp.status_code == 404:
                raise SensuAPI_Exception(str(resp.status_code) +
                                    ' :This request returns nothing.')
                return
        except SensuAPI_Exception as e:
            logger.error('Error with request: {0}'.format(e))
            return
        logger.info('Test Comlpeted with sucess.')
        return resp.json()
