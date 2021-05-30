from setuptools import setup, find_packages

setup(
    name="koi",
    version="0.0.1.dev1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
)
