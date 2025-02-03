#!/bin/bash

# Start the Django development server (or your test server) in a separate terminal or background it.
# Example (background):
python ../../manage.py runserver &

# Run Locust tests
locust -f locustfile.py --headless -u 100 -r 20 -t 1m # 100 users, 20 spawn rate/second, for 1 minute

# Kill the Django development server
pkill -f "python.*manage.py runserver"

# Generate an HTML report (optional)
# locust -f locustfile.py --headless -u 100 -r 20 -t 1m --html=report.html

# Clean up (optional)
# rm -f locust-*.log # Remove locust log files