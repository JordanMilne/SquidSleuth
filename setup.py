import os
import re

from codecs import open

try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup, Command

requires = [
    'requests <3.0, >=2.4',
    'requests-futures',
    'six',
    'sqlalchemy',
]

packages = [
    "squidsleuth"
]

with open('squidsleuth/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

with open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()


class BootstrapCommand(Command):
    description = "bootstrap"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from sqlalchemy.engine import create_engine

        from squidsleuth import db

        engine = create_engine(os.environ["SQUIDSLEUTH_CONNSTR"])
        db.Base.metadata.create_all(engine)


setup(
    name='squidsleuth',
    version=version,
    packages=packages,
    install_requires=requires,
    tests_require=["mock"],
    url='https://github.com/JordanMilne/SquidSleuth',
    license='Apache 2',
    author='Jordan Milne',
    author_email='squidsleuth@saynotolinux.com',
    test_suite='test_squidsleuth',
    description='Tools for snooping around insecurely configured Squid proxies',
    long_description=readme,
    cmdclass={'bootstrap': BootstrapCommand},
    entry_points = {
        'console_scripts': [
            'squidsleuth = squidsleuth.main:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Security',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
