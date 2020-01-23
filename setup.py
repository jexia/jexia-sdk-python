from io import open
from os import path
import re
from setuptools import setup, find_packages


PYPI_RST_FILTERS = (
    # Replace Python crossreferences by simple monospace
    (r':(?:class|func|meth|mod|attr|obj|exc|data|const):`~(?:\w+\.)*(\w+)`', r'``\1``'),
    (r':(?:class|func|meth|mod|attr|obj|exc|data|const):`([^`]+)`', r'``\1``'),
    # replace doc references
    (r':doc:`(.+) <(.*)>`', r'`\1 <http://jexia-sdk.readthedocs.org/en/stable\2.html>`_'),
    # replace issues references
    (r':issue:`(.+?)`', r'`#\1 <https://github.com/jexia/jexia-sdk-python/issues/\1>`_'),
    # replace pr references
    (r':pr:`(.+?)`', r'`#\1 <https://github.com/jexia/jexia-sdk-python/pull/\1>`_'),
    # replace commit references
    (r':commit:`(.+?)`', r'`#\1 <https://github.com/jexia/jexia-sdk-python/commit/\1>`_'),
    # Drop unrecognized currentmodule
    (r'\.\. currentmodule:: .*', ''),
)


def rst(filename):
    '''
    Load rst file and sanitize it for PyPI.
    Remove unsupported github tags:
     - code-block directive
     - all badges
    '''
    content = open(filename).read()
    for regex, replacement in PYPI_RST_FILTERS:
        content = re.sub(regex, replacement, content)
    return content


def pip(filename):
    '''Parse pip reqs file and transform it to setuptools requirements.'''
    requirements = []
    for line in open(path.join('requirements', '{0}.txt'.format(filename))):
        line = line.strip()
        if not line or '://' in line or line.startswith('#'):
            continue
        requirements.append(line)
    return requirements


install_requires = pip('install')
doc_require = pip('doc')
tests_require = pip('test')
dev_require = tests_require + pip('develop')
long_description = '\n'.join((
    rst('README.rst'),
    rst('CHANGELOG.rst'),
    ''
))

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
