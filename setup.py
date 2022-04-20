from setuptools import setup

with open("requirements.txt", "r") as fp:
    requirements = fp.read().split("\n")

setup(
    name="durin",
    version="0.0.1",
    install_requires=requirements,
    packages=["durin"],
    license="LGPLv3",
    maintainer="Jens E. Pedersen",
    maintainer_email="jeped@kth.se",
    extras_require={"aestream": ["aestream"]},
)
