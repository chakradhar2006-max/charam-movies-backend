"""
Shared SQLAlchemy instance. Imported by app.py and every model module,
so there is a single db object across the whole application.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
