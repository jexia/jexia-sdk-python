from io import open
from os import path
from setuptools import setup, find_packages


here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


def pip(filename):
    '''Parse pip reqs file and transform it to setuptools requirements.'''
    requirements = []
    for line in open(path.join(here, 'requirements', '{0}.txt'.format(filename))):
        line = line.strip()
        if not line or '://' in line or line.startswith('#'):
            continue
        requirements.append(line)
    return requirements


install_requires = pip('install')
doc_require = pip('doc')
tests_require = pip('test')
dev_require = tests_require + pip('develop')

exec(compile(open('jexia_sdk/__init__.py').read(), 'jexia_sdk/__init__.py', 'exec'))

setup(
    name = "jexia_sdk",
    version = __version__,
    author = "Jexia",
    author_email = "sdk-team@jexia.com",
    description = ("Official SDK for Jexia platform"),
    long_description = long_description,
    license = "MIT",
    url = "https://github.com/jexia/jexia-sdk-python",
    install_requires = install_requires,
    tests_require = tests_require,
    extras_require = {
        'test': tests_require,
        'doc': doc_require,
        'dev': dev_require,
    },
    classifiers = [
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords = "jexia sdk",
    packages = find_packages(exclude=['tests']),
    python_requires = '>=2.7.15, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4',
    project_urls = {
        'Bug Reports': 'https://github.com/jexia/jexia-sdk-python/issues',
        'Source': 'https://github.com/jexia/jexia-sdk-python/',
    },
)
