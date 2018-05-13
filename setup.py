from setuptools import setup, find_packages


try:
    from pyqt_distutils.build_ui import build_ui
    cmdclass = {"build_ui": build_ui}
except ImportError:
    build_ui = None  # user won't have pyqt_distutils when deploying
    cmdclass = {}


from randovania import VERSION

setup(
    name='randovania',
    version=VERSION,
    author='Henrique Gemignani',
    url='https://github.com/henriquegemignani/randovania',
    description='A randomizer validator for the Metroid Prime series.',
    packages=find_packages(),
    cmdclass=cmdclass,
    scripts=[
    ],
    package_data={
        "randovania": ["data/*"]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Games/Entertainment',
    ],
    install_requires=[
        'py', 'PyQt5', ],
    setup_requires=[
        'pytest', 'markdown', 'PyInstaller', 'pyqt-distutils'
    ],
    entry_points={
        'console_scripts': [
            "randovania = randovania.__main__:main"
        ]
    },
)
