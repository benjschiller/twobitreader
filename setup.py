#!/usr/bin/env python
"""Description

Setup script for twobitreader

Licensed under Perl Artistic License 2.0
No warranty is provided, express or implied
"""
import platform

if platform.system() == 'Java':
    print('Warning: not sure if this library is jython-safe')

from setuptools import setup

cmdclass = {}
try:
    from sphinx.setup_command import BuildDoc

    cmdclass['build_sphinx'] = BuildDoc
except ImportError:
    pass
try:
    from sphinx_pypi_upload import UploadDoc

    cmdclass['upload_sphinx'] = UploadDoc
except ImportError:
    pass

name = 'twobitreader'
version = "3.1.0"


def main():
    setup(
        name=name,
        version=version,
        description='A fast python package for reading .2bit files \
(used by the UCSC genome browser)',
        author='Benjamin Schiller',
        author_email='ben dot j dot schiller at gmail',
        packages=['twobitreader'],
        package_data={'twobitreader': ['tests/test.2bit']},
        url='https://github.com/benjschiller/twobitreader',
        cmdclass=cmdclass,
        command_options={
            'project': ('setup.py', name),
            'version': ('setup.py', version),
        },
        classifiers=[
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: Artistic License',
            'Intended Audience :: Developers',
            'Intended Audience :: End Users/Desktop',
            'Intended Audience :: Science/Research',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.2',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Topic :: Scientific/Engineering :: Bio-Informatics'
        ]
    )


if __name__ == '__main__':
    main()
