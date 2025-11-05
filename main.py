from uvicorn import run
from server import app

from receiver import *

run(app, host="0.0.0.0", port=8000)
