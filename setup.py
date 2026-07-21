from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="namespaced_enums",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="0.1.0",
    license="MIT",
    author="Piotr Waszkiewicz",
    author_email="waszka23@gmail.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    # Ship inline type information and the mypy plugin (PEP 561).
    package_data={"namespaced_enums": ["py.typed", "plugin.py"]},
    include_package_data=True,
    # The optional mypy plugin needs a modern mypy; the library itself has no
    # runtime dependencies.
    extras_require={"mypy": ["mypy>=1.0"]},
    url="https://github.com/waszker/namespaced_enums",
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 4 - Beta",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        # Pick your license as you wish
        "License :: OSI Approved :: MIT License",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate you support Python 3. These classifiers are *not*
        # checked by 'pip install'. See instead 'python_requires' below.
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="python, enum, namespaced",
    python_requires=">=3.10",
    install_requires=[],
    project_urls={
        "Bug Reports": "https://github.com/waszker/namespaced_enums/issues",
        "Source": "https://github.com/waszker/namespaced_enums",
    },
)
