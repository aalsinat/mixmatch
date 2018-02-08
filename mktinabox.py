from subprocess import Popen, TimeoutExpired

proc = Popen([r'.\\mixmatch\\mixmatch.exe'])
try:
    outs, errs = proc.communicate(timeout=10)
except TimeoutExpired:
    proc.kill()
    outs, errs = proc.communicate()
