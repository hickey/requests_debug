from setuptools import setup
import requests_debug


setup(
    name="requests_debug",
    description="Adds logging and timing for the requests library",
    version=requests_debug.__version__,
    url="https://github.com/ericmoritz/requests_debug",
    author="Eric Moritz",
    author_email="eric@themoritzfamily.com",
    py_modules="requests_debug")
