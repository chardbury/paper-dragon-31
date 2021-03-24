from setuptools import find_packages
from setuptools import setup


setup(
    name = 'applib',
    package_dir = {'': '.'},
    install_requires = [
        'pyglet',
    ],
    extras_require = {
        'development': [
            'ipdb',
            'ipython',
            'pyinstaller',
            'pytest',
            'wheel',
        ],
    },
)