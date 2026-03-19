import os
from concurrent.futures import ThreadPoolExecutor

max_workers = min(32, os.cpu_count() * 4)
executor = ThreadPoolExecutor(max_workers=max_workers)