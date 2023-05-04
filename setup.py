#!/usr/bin/python3

from setuptools import find_packages, setup

# from broker import __version__

with open("README.org", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as f:
    requirements = list(map(str.strip, f.read().split("\n")))[:-1]

setup(
    name="ebloc-broker",
    packages=find_packages(),
    setup_requires=["wheel", "eth-brownie", "ipdb", "rich", "dbus-python"],
    version="2.2.2",  # don't change this manually, use bumpversion instead
    license="MIT",
    description=(  # noqa: E501
        "A Python framework to communicate with ebloc-broker that is "
        "a blockchain based autonomous computational resource broker."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Alper Alimoglu",
    author_email="alper.alimoglu@gmail.com",
    url="https://github.com/ebloc/ebloc-broker",
    keywords=["eblocbroker"],
    install_requires=requirements,
    entry_points={
        "console_scripts": ["eblocbroker=broker._cli.__main__:main"],
    },
    include_package_data=True,
    python_requires=">=3.6,<4",
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
)
