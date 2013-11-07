from setuptools import setup
from requests_debug import __version__

setup(
    name="requests_debug",
    description="Adds logging and timing for the requests library",
    version=__version__,
    url="https://github.com/ericmoritz/requests_debug",
    author="Eric Moritz",
    author_email="eric@themoritzfamily.com",
    packages=["requests_debug"],
    install_requires=[
        "simpleflake>=0.1.2,<0.2",
        "requests>=0.13,<0.14",
        ]
    )
