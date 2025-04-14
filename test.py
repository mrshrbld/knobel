### Set environment
## General Stuff
# Lines are written up to column 75-80
# print() statements only for development and will be deleted later

## Load needed modules
import numpy as np
import datetime as dt
from flask import Flask

#### Flask specific stuff
app = Flask(__name__)

@app.route("/table")
def open_table():
    return 'This is table {}'.format(dt.datetime.now())

### Allows to run the app/webpage as usual python scripts
if __name__ == "__main__":
    app.run(port=8080, debug=True)