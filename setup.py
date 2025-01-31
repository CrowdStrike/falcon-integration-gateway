from setuptools import find_packages
from setuptools import setup
import fig

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="falcon-integration-gateway",
    version=fig.__version__,
    author="CRWD Solution Architects",
    author_email="integrations@crowdstrike.com",
    description="The CrowdStrike Demo Falcon Integration Gateway for GCP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/crowdstrike/falcon-integration-gateway",
    packages=find_packages(),
    package_data={
        'fig': ['../config/*.ini'],
    },
    include_package_data=True,
    install_requires=[
        'boto3',
        'crowdstrike-falconpy',
        'google-cloud-securitycenter',
        'google-cloud-resource-manager >= 1.0.2',
        'tls-syslog',
        'google-auth',
        'google-api-python-client',
        'py7zr'
    ],
    extras_require={
        'devel': [
            'flake8',
            'pylint',
            'pytest',
            'bandit',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: The Unlicense (Unlicense)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6, <3.12'
)
