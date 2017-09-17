from setuptools import setup

setup(
    name='sixquiprend',
    packages=['sixquiprend'],
    version='0.1.0',
    include_package_data=True,
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'psycopg2',
        'passlib',
        'bcrypt',
        'flask-login',
        'gunicorn',
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
    ],
)
