from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="namespaced_enums",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="0.0.2",
    license="MIT",
    author="Piotr Waszkiewicz",
    author_email="waszka23@gmail.com",
    py_modules=["namespaced_enums"],
    package_dir={"": "src"},
    url="https://github.com/waszker/namespaced_enums",
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 3 - Alpha",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        # Pick your license as you wish
        "License :: OSI Approved :: MIT License",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate you support Python 3. These classifiers are *not*
        # checked by 'pip install'. See instead 'python_requires' below.
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="python, enum, namespaced",
    python_requires=">=3.7, <4",
    install_requires=[],
    project_urls={
        "Bug Reports": "https://github.com/waszker/namespaced_enums/issues",
        "Source": "https://github.com/waszker/namespaced_enums",
    },
)
