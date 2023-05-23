#!/bin/bash

locust -f locustfile.py --worker --master-host=$1 2>&1 > out.log
