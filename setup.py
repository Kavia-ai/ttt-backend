from setuptools import setup, find_packages

setup(
    name="tictactoe-api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'Flask==3.0.2',
        'SQLAlchemy==2.0.37',
    ],
)