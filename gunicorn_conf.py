from multiprocessing import cpu_count



# Socket Path

bind = 'unix:/home/ubuntu/Desktop/project/fastapi/gunicorn.sock'



# Worker Options

workers = cpu_count() + 1

worker_class = 'uvicorn.workers.UvicornWorker'



# Logging Options

loglevel = 'debug'

accesslog = '/home/ubuntu/Desktop/project/fastapi/access_log'

errorlog =  '/home/ubuntu/Desktop/project/fastapi/error_log'


