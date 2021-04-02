from setuptools import find_packages
from setuptools import setup

from applib.constants import APPLICATION_VERSION


setup(
    name = 'copcake-caper',
    version = APPLICATION_VERSION,
    packages = find_packages(),
    install_requires = [
        'pyglet',
    ],
    extras_require = {
        'development': [
            'ipdb',
            'ipython',
            'pyinstaller',
            'pytest',
        ],
    },
)
