import threading
import time


def runMethodInThread(fn):
    def inner(*args, **kw):
        t = threading.Thread(target=fn, args=args, kwargs=kw)
        t.daemon = True
        t.start()
        return t
    return inner


def logTime(fn):
    def inner(*args, **kw):
        t1 = time.time()
        result = fn(*args, **kw)
        t2 = time.time()
        print('Time Taken in Method', fn.__name__, round(t2-t1, 4), 'Secs')
        return result
    return inner
