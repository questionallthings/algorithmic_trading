#!/usr/bin/env python3

"""
This script is used to test various ideas from internal/external sources before implementing in development code.
This will not be part of final package.
"""

import pymysql
import os
from src import db_manager

password = os.environ['memsql_password']
ip = os.environ['memsql_ip']
port = os.environ['memsql_port']
user = os.environ['memsql_user']

# Open database connection
db = db_manager.Database
db.create_tables(table_data)
