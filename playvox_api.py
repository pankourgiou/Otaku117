import json
import logging
import time

import requests
from requests.auth import HTTPBasicAuth


class PlayVoxAPI:
    """
    Class to access the PlayVox API and retrieve data from it
    API documentation: https://developers.playvox.com/restapis/
    """
    def __init__(self, domain, api_key, api_secret, paging_size=None):
        self.__logger = self.get_logger()
        if not domain or not api_key or not api_secret:
            self.__logger.error('Credentials missing: domain missing: {0}, api_key missing: {1}, api_secret missing: {2}'.
                                format(not domain, not api_key, not api_secret))
            self.__logger.error('Given values: domain: {domain}, api_key: {api_key}, api_secret: {api_secret}'.
                                format(domain=domain, api_key=api_key, api_secret=api_secret))
            exit(1)
        self.__base_url = 'https://{}.playvox.com/api/v1'.format(domain)
        self.__basic_auth = HTTPBasicAuth(api_key, api_secret)
        self.__paging_size = paging_size if paging_size else 2000

    @staticmethod
    def get_logger():
        logger = logging.getLogger('playvox_API_data_fetcher')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def __get_parameters(self, page_number):
        """Return the concatenated string of parameters to call the API"""
        parameters = {'include': 'all', 'all_sites': 'true', 'sort': '-updated_at', 'per_page': self.__paging_size, 'page': page_number}
        return '&'.join({'{k}={v}'.format(k=key, v=value) for key, value in parameters.items()})

    def make_get_request(self, resource_name, endpoint, page_number, query=None):
        """Make a GET request to the PlayVox API and retry in case of temporary server errors"""
        num_tries = 1
        max_num_tries = 3

        resource_url = '{api}/{endpoint}?{params}'.format(api=self.__base_url, endpoint=endpoint, params=self.__get_parameters(page_number))
        if query:
            resource_url += '&query={}'.format(query)
        while num_tries <= max_num_tries:
            get_resource_req = requests.get(url=resource_url, auth=self.__basic_auth)
            if get_resource_req.status_code == 200:
                # if the get-request succeeds, return the data as a JSON dictionary
                return json.loads(get_resource_req.content)
            elif get_resource_req.status_code in (500, 502, 503, 504):
                self.__logger.warning('Server temporarily unavailable (code {}), will retry in 30 seconds'.format(get_resource_req.status_code))
                time.sleep(30)
                num_tries += 1
            else:
                self.__logger.error('Get {resource} request failed with status code {status}'.
                                    format(resource=resource_name, status=get_resource_req.status_code))
                exit(1)
        # maximum number of tries reached without success
        self.__logger.error('Reached maximum number of tries without success - now exiting')
        exit(1)
