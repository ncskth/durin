from msilib.schema import File
from setuptools import setup

with open("requirements.txt", "r") as fp:
    requirements = fp.read()

setup(
    name="durin",
    version="0.0.1",
    packages=requirements,
    license="LGPLv3",
    maintainer="Jens E. Pedersen",
    maintainer_email="jeped@kth.se",
)
