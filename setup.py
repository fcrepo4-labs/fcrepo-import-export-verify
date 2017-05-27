"""
Verifies the results of import and export operations in Fedora repositories.
"""
from setuptools import find_packages, setup
from fcrepo_verify.version import __version__

dependencies = ['click',
                'isodate',
                'pyparsing',
                'rdflib',
                'rdflib_jsonld',
                'requests',
                'pyyaml',
                'flake8',
                'scandir',
                'bagit']

setup(
    name='fcrepo-verify',
    version=__version__,
    url='https://github.com/dbernstein/fcrepo-import-export-verify',
    license='Apache',
    author='Josh Westgard, Bethany Seeger, Youn Noh, Daniel Bernstein',
    author_email='westgard@umd.edu, bseeger@amherst.edu, youn.noh@yale.edu, '
                 'dbernstein@duraspace.org',
    description='Verifies the results of import and export operations in '
                'Fedora repositories.',
    long_description=__doc__,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'fcrepo-verify = fcrepo_verify.cli:main',
        ],
    },
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
