# -*- coding: utf-8 -*-
from future import standard_library
standard_library.install_aliases()
import sys
import os
import urllib.request, urllib.error, urllib.parse
from urllib.error import URLError
import socket
import time
from urllib.parse import urlparse
from copy import deepcopy
import re

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3.exceptions import InsecurePlatformWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)

import ssl
