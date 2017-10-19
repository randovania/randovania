from setuptools import setup, find_packages

from randovania import VERSION

setup(
    name='randovania',
    version=VERSION,
    author='Henrique Gemignani',
    url='https://github.com/henriquegemignani/randovania',
    description='A randomizer validator for the Metroid Prime series.',
    packages=find_packages(),
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
        'py', ],
    setup_requires=[
        'pytest', 'markdown', 'PyInstaller',
    ],
    entry_points={
        'console_scripts': [
            "randovania = randovania.__main__:main"
        ]
    },
)
