import time
import functools

def retry(max_attempts=3, initial_delay=1.0, backoff=2.0):
    def deco(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            attempt = 0
            while True:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    time.sleep(delay)
                    delay *= backoff
        return wrapper
    return deco
