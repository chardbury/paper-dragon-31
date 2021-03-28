from setuptools import setup


setup(
    name = 'applib',
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
