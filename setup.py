from setuptools import setup
import requests_debug


setup(
    name="requests_debug",
    description="Adds logging and timing for the requests library",
    version=requests_debug.__version__,
    py_modules="requests_debug")
