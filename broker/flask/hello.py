from flask import Flask
from broker.utils import run

app = Flask(__name__)


@app.route("/")
def hello():
    core_info = run(["sinfo", "-h", "-o%C"]).split("/")

    # allocated_cores = int(core_info[0])
    idle_cores = int(core_info[1])
    # other_cores = int(core_info[2])
    # total_cores = int(core_info[3])

    return str(idle_cores)
