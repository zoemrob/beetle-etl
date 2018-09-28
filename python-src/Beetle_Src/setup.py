from setuptools import setup, find_packages

__version__ = '1.0.5' 

setup(
    name='BeetleETL',
    version=__version__,
    author='Robby Boney & Jonathon Carothers',
    author_email='robbyb@gointerject.com',
    packages=find_packages(exclude=['contrib', 'docs', 'Tests*']),
    
    # integrates our tests into the package
    # run tests with:
    #  > python setup.py test
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],

    scripts=["BeetleETL/beetle"],
    url='https://gitlab.com/Open-Interject/Beetle-ETL',
    license="Apache License",
    description='Open Source python package for moving data from NoSQL to relational databases.',
    long_description=open('README.md', "r").read(),
    python_requires='>=3',
    install_requires=[
        "pymongo >= 3.6.0",
        "pyodbc >= 4.0.23",
        "pandas >= 0.20.0"
    ],
    classifiers=[]
)