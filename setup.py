import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cometblue-asyncio",
    version="0.9.1",
    author="Pavel Krc",
    author_email="src@pkrc.net",
    description="Python library for interacting with the Eurotronic Comet Blue thermostatic radiator valve based on bleak using asyncio.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rolicot/cometblue-asyncio",
    packages=setuptools.find_packages(),
    license='MIT',
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Development Status :: 4 - Beta",
    ],
    install_requires="bleak",
    python_requires='>=3.7',
)
