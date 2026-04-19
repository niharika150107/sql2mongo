import os

# Workers
workers = 1
worker_class = "sync"
timeout = 300

# Pre-load app so parser is built ONCE before workers fork
preload_app = True

# Port
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Called once in master process BEFORE forking workers
def on_starting(server):
    print(">>> Pre-warming parser (runs once before workers fork)...")
    from sql2mongo.parser.sql_parser import SqlParser
    from sql2mongo.codegen.mongodb_generator import MongoDBGenerator
    import app as application
    application._parser = SqlParser()
    application._generator = MongoDBGenerator()
    print(">>> Parser ready!")
