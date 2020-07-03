#!/bin/bash

source $HOME/venv/bin/activate

# export FLASK_APP=webapp/main.py
export FLASK_APP=webapp/registration_example.py
export FLASK_DEBUG=1
export FLASK_ENV=development

export FLASK_RUN_EXTRA_FILES="templates/hello.html"
export TEMPLATES_AUTO_RELOAD=True

# authbind gunicorn --log-level=debug -b 0.0.0.0:5000 run:app
# authbind gunicorn -b 0.0.0.0:5000 run:app

python -m flask run --port 5000
