export CONFIG_DATADIR="."
export SERVER_ADDRESS="0.0.0.0"
export SERVER_PORT="8000"

# Notify the bootstrapper not to generate a Gunicorn config
# Also launch with the development server
export DEVELOPMENT=1

export TEMPLATES_AUTO_RELOAD=True

python3 bootstrap.py
