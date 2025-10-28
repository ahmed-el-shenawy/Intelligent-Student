# Intelligent-Student
This is an application using Retrival Augemented Generation (RAG)
# To start the app
~~~bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
~~~

# Database Migration with Alembic

Alembic is a lightweight database migration tool for SQLAlchemy.  
It helps manage database schema changes over time, track versions, and safely upgrade or downgrade your database.
 
## Initialize Alembic
```bash
alembic init alembic
```
## Create migration
```bash
alembic revision --autogenerate -m "init"
```
## Apply migration
```bash
alembic upgrade head
```
## Downgrade (optional)
- Step back one migration
```bash
alembic downgrade -1
```
- Go back to the initial state (base)
```bash
alembic downgrade base
```
## Check migration status and history
```bash
alembic current
```
```bash
alembic history
```
```bash
alembic history --verbose
```
