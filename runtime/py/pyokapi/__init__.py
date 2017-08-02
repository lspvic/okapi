import os

import thriftpy
dirname = os.path.dirname(__file__)
okapi_thrift = thriftpy.load(os.path.join(dirname, "okapi.thrift"), module_name="okapi_thrift")

Response = okapi_thrift.Response

