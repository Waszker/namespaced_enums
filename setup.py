from setuptools import setup, find_packages


setup(
    name="namespaced_enums",
    version="0.0.1",
    license="MIT",
    author="Piotr Waszkiewicz",
    author_email="waszka23@gmail.com",
    packages=find_packages("src"),
    package_dir={"": "src"},
    url="https://github.com/waszker/namespaced_enums",
    keywords="python enum namespaced",
    install_requires=[],
)
