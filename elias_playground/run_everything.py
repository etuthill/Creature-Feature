# run_everything.py
import subprocess
import signal
import sys
import time
import os

procs = []

def start(cmd):
    p = subprocess.Popen(cmd)
    procs.append(p)
def shutdown(signum=None, frame=None):
    print("Supervisor: shutting down all processes")

    for p in procs:
        try:
            p.send_signal(signal.SIGINT)
        except Exception:
            pass

    timeout = 5
    start_time = time.time()
    for p in procs:
        while p.poll() is None and (time.time() - start_time < timeout):
            time.sleep(0.1)

    for p in procs:
        if p.poll() is None:
            print(f"Force killing PID {p.pid}")
            p.kill()

    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

start(["python3", "state_controller.py"])
start(["python3", "audio_screen_drivers.py"])
start(["python3", "machine_idle.py"])
start(["python3", "boredom.py"])
start(["python3", "hunger.py"])

signal.pause()
