import os

from kallisticore.version import VERSION
from setuptools import find_packages
from setuptools import setup

packages = ['kallisticore']

install_requires = []
tests_require = []

REQUIREMENTS = 'requirements.txt'
if os.path.isfile(REQUIREMENTS):
    with open(REQUIREMENTS) as fd:
        install_requires = [
            pkg.strip() for pkg in fd.readlines()
            if not (pkg.startswith("--") or pkg is "\n"
                    or pkg.startswith('deps/'))]


TEST_REQUIREMENTS = 'requirements-dev.txt'
if os.path.isfile(TEST_REQUIREMENTS):
    with open(TEST_REQUIREMENTS) as fd:
        tests_require = [
            pkg for pkg in fd.readlines()
            if not (pkg.startswith("--") or pkg is "\n")]
setup(
    name="kallisti-core",
    description='Core of the chaos engineering framework: Kallisti',
    url='https://github.com/jpmorganchase/kallisti-core',
    author='kallisti-core authors',
    packages=find_packages(exclude=('config',)),
    install_requires=install_requires,
    version=VERSION,
    extras_require={
        'test': tests_require,
    },
    classifiers=(
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Framework :: Django :: 2.0',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9'
    ),
    include_package_data=True
)
