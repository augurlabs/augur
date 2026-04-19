from subprocess import run, PIPE, Popen
import signal, time, os

# Ignore SIGTERM from parent process (since we're terminating our parent)
signal.signal(signal.SIGTERM, lambda signum, frame: None)

run("augur backend stop-collection-blocking", shell=True, stderr=PIPE, stdout=PIPE, stdin=PIPE)
Popen("augur backend stop", shell=True, stderr=PIPE, stdout=PIPE, stdin=PIPE).wait()

time.sleep(5)

cmd = "augur backend start"

if os.environ.get("AUGUR_DEV") == "1":
    cmd += " --development"

if os.environ.get("AUGUR_DISABLE_COLLECTION") == "1":
    cmd += " --disable-collection"

if os.environ.get("AUGUR_PORT"):
    cmd += f" --port {os.environ['AUGUR_PORT']}"

if os.environ.get("AUGUR_PIDFILE"):
    cmd += f" --pidfile {os.environ['AUGUR_PIDFILE']}"

if signal.getsignal(signal.SIGHUP) != signal.SIG_DFL:
    cmd = "nohup " + cmd

Popen(cmd, shell=True)
