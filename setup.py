from setuptools import setup

setup(
    name='sixquiprend',
    packages=['sixquiprend'],
    include_package_data=True,
    install_requires=[
        'flask',
        'sqlalchemy',
        'psycopg2',
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
    ],
)
