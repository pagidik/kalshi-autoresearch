"""Setup script for kalshi-autoresearch."""

from setuptools import setup, find_packages

setup(
    name="kalshi-autoresearch",
    version="0.1.0",
    description="Self-improving signal detection for Kalshi prediction markets",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(include=["kalshi_autoresearch*"]),
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.28",
        "numpy>=1.24",
    ],
    entry_points={
        "console_scripts": [
            "kalshi-research=kalshi_autoresearch.autoresearch:_cli_main",
        ],
    },
)
