import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="seedener",
    version="0.0.1",
    author="MaximEdogawa",
    author_email="leo@librem.one",
    description="DIY build an offline, airgapped signing device for Chia Blockchain custody solution!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MaximEdogawa/seedener",
    project_urls={
        "Bug Tracker": "https://github.com/MaximEdogawa/seedener/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)