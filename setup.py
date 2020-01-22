import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="python-gcp-injections",  # Replace with your own username
    version="1.5.1",
    author="Tommy Strand",
    author_email="github-projects@ireality.no",
    description="Tools and libraries for python to better run services on GCP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/injectedreality/python-gcp-injections",
    packages=['gcpi',
              'gcpi.stackdriverlog',
              'gcpi.stackdriverlog.contrib',
              'gcpi.stackdriverlog.contrib.django',
              'gcpi.stackdriverlog.contrib.flask', ],
    keywords='stackdriver django gcp logging gke',
    install_requires=[
        'structlog',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)