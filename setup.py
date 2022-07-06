from setuptools import find_packages
from setuptools import setup
from glob import glob
from os.path import basename
from os.path import splitext

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="falcon-integration-gateway",
    version="3.1.1",
    author="CrowdStrike",
    maintainer="Simon Lukasik",
    description="The CrowdStrike Demo Falcon Integration Gateway for GCP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/crowdstrike/falcon-integration-gateway",
    packages=find_packages("fig"),
    package_dir={"": "fig"},
    py_modules=[splitext(basename(path))[0] for path in glob("fig/*.py")],
    include_package_data=True,
    install_requires=[
        'boto3',
        'crowdstrike-falconpy',
        'google-cloud-securitycenter',
        'google-cloud-resource-manager >= 1.0.2',
        'tls-syslog',
        'google-auth',
        'google-api-python-client'
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
    python_requires='>=3.6',
)
