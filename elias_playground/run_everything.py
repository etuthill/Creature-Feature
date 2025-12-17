import subprocess
import signal
import sys

procs = []

def start(cmd):
    p = subprocess.Popen(cmd)
    procs.append(p)

def shutdown(sig, frame):
    print("Shutting down all processes")
    for p in procs:
        p.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

start(["python3", "state_controller.py"])
start(["python3", "audio_screen_drivers.py"])
start(["python3", "machine_idle.py"])
start(["python3", "boredom.py"])
start(["python3", "hunger.py"])

signal.pause()
