import time
from contextlib import contextmanager


@contextmanager
def timer(name: str = "timer"):
    start = time.time()
    yield
    end = time.time()
    print(f"{name}: {end-start:.3f}s")
