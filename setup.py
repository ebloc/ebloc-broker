#!/usr/bin/env python3

# $ pip instal -e .
# link: https://stackoverflow.com/a/50193944/2402577

from setuptools import find_packages, setup

"""
with open("README.md", "r") as fh:
    long_description = fh.read()
"""

with open("requirements.txt", "r") as f:
    requirements = list(map(str.strip, f.read().split("\n")))[:-1]


setup(
    name="eBlocBroker",
    version="1.0.4",  # don't change this manually, use bumpversion instead
    license="MIT",
    description=(  # noqa: E501
        "A Python framework to communicate with eBlocBroker, which is "
        "a blockchain based autonomous computational resource broker."
    ),
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    author="Alper Alimoglu",
    author_email="alper.alimoglu@gmail.com",
    url="https://github.com/eBloc/eBlocBroker",
    keywords=["eblocbroker", "ethereum"],
    include_package_data=True,
    python_requires=">=3.7,<4",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    packages=find_packages("src"),
    setup_requires=["wheel"],
)
