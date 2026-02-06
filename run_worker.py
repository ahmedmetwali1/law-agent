import sys
import os

# Ensure current directory is in path
sys.path.append(os.getcwd())

from arq import run_worker
from api.queue.worker import WorkerSettings

if __name__ == '__main__':
    print("🚀 Starting Recovery Queue Worker...")
    run_worker(WorkerSettings)
