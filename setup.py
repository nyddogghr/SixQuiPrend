from setuptools import setup

setup(
    name='sixquiprend',
    packages=['sixquiprend'],
    include_package_data=True,
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'psycopg2',
        'flask-login',
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
    ],
)
