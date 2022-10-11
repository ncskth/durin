from setuptools import setup

with open("requirements.txt", "r") as fp:
    requirements = fp.read().split("\n")

with open("README.md", "r") as fp:
    long_description = fp.read()

setup(
    name="durin",
    version="0.0.58",
    install_requires=requirements,
    packages=["durin"],
    license="LGPLv3",
    maintainer="Jens E. Pedersen",
    maintainer_email="jeped@kth.se",
    extras_require={"aestream": ["aestream"]},
    scripts=["bin/durin"],
    long_description=long_description,
    long_description_content_type="text/markdown",
)
