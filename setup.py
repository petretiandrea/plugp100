import codecs
import os
from distutils.dist import Distribution

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    README = readme_file.read()

with open("requirements.txt") as requirements_file:
    REQUIREMENTS = requirements_file.read().split("\n")

FORCE_BINARY = "FORCE_BINARY" in os.environ


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

    class bdist_wheel(_bdist_wheel):
        def __init__(self, dist: Distribution):
            super().__init__(dist)

        def finalize_options(self):
            _bdist_wheel.finalize_options(self)
            # Mark us as not a pure python package
            self.root_is_pure = False

        def get_tag(self):
            python, abi, plat = _bdist_wheel.get_tag(self)
            print(f"Tag: {python} {abi} {plat}")
            return python, abi, plat

except ImportError:
    bdist_wheel = None

if FORCE_BINARY:
    print("Binary forced")

setup_args = dict(
    name="plugp100",
    version=get_version("plugp100/__init__.py"),
    install_requires=REQUIREMENTS,
    description="Controller for TP-Link Tapo P100 and other devices",
    long_description_content_type="text/markdown",
    long_description=README,
    license="GPL3",
    packages=find_packages(exclude=("tests",)),
    author="@petretiandrea",
    author_email="petretiandrea@gmail.com",
    keywords=["Tapo", "P100"],
    url="https://github.com/petretiandrea/plugp100",
    download_url="https://github.com/petretiandrea/plugp100",
    classifiers=[
        # 'Development Status :: 4 - Beta',
        "Development Status :: 5 - Production/Stable"
    ],
    cmdclass={
        **({"bdist_wheel": bdist_wheel} if FORCE_BINARY else {}),
    },
)

if __name__ == "__main__":
    setup(**setup_args)
