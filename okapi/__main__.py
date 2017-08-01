import sys, os

import logging
logging.basicConfig(level=logging.DEBUG)

if not __package__:
    path = os.path.join(os.path.dirname(__file__), os.pardir)
    sys.path.insert(0, path)
    
from okapi import app
from okapi.models import prepare
if len(sys.argv) >= 2 and sys.argv[1] == "init":
    prepare()
else:
    app.run()