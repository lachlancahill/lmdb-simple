from setuptools import setup, find_packages
from pathlib import Path

here = Path(__file__).parent
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="lmdb-simple",
    version="0.1.3",
    description="LMDB-backed dict-like store",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="you@example.com",
    url="https://github.com/yourusername/lmdb-simple",
    license="Apache-2.0",
    python_requires=">=3.9",
    install_requires=["lmdb==1.6.2"],
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)