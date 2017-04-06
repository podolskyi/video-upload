from setuptools import setup, find_packages


setup(
    name="video_upload",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "alembic",
        "azure-storage",
        "celery",
        "jwt",
        "Flask",
        "Flask-SQLAlchemy",
        "psycopg2",
        "raven[flask]",
        "requests",
    ],
)
