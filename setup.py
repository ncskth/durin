from setuptools import find_packages, setup

with open("requirements.txt", "r") as fp:
    requirements = fp.read().split("\n")

with open("README.md", "r") as fp:
    long_description = fp.read()

setup(
    name="durin",
    version="0.0.80",
    install_requires=requirements,
    packages=find_packages(),
    license="LGPLv3",
    maintainer="Jens E. Pedersen",
    maintainer_email="jeped@kth.se",
    extras_require={"aestream": ["aestream"]},
    scripts=["bin/durin"],
    description="Python control interface for the Durin robot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True
)