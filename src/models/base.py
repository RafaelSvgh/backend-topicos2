"""
Configuración base para los modelos SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

connection_string = "mssql+pyodbc://sa:rafa0134@localhost\\MSSQLSERVER2,1433/negocio?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=no&TrustServerCertificate=yes"
engine = create_engine(connection_string)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base() 