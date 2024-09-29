gunicorn --bind 0.0.0.0:8000 --workers 3 redit.wsgi:application
#gunicorn --bind 0.0.0.0:8000 --daemon redit.wsgi:application
#gunicorn --bind 0.0.0.0:8000  --worker-class gevent redit.wsgi:application
