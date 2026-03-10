# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
sys.path.append("/home/admin/myproject/myprojectenv/lib/python2.7/site-packages")
import json
import requests
import urllib2
import urllib as ul
import time
from datetime import datetime


requestedUnits='any'
userName='ailsonarcsdk'
password='arcsdk'
requestedUnits='any'
startDate='2019-08-02'
endDate='2019-08-03'
requestedPropertiesStr='u.plate_num,u.plate_number,sc.start_time,sc.end_time,sc.total_distance,ad0.address,ad1.address,sc.period'

payload = {'userName': userName,'password': password,'requestedUnits': requestedUnits,'startDate': startDate, 'endDate': endDate,'requestedPropertiesStr':requestedPropertiesStr}
uri = 'https://sdk.galooli-systems.com/galooliSDKService.svc/json/Trip_Report'


class Tripreportview:
    response= requests.get(uri, params=payload)
    print (response.url)
    dados = json.loads(response.content)
