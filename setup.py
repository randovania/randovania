from setuptools import setup, find_packages
from setuptools.command.build_py import build_py

try:
    from pyqt_distutils.build_ui import build_ui
except ModuleNotFoundError:
    build_ui = None


class custom_build_py(build_py):
    def run(self):
        self.run_command('build_ui')
        super().run()


with open("README.md") as readme_file:
    long_description = readme_file.read()


def version_scheme(version):
    import setuptools_scm.version
    if version.exact:
        return setuptools_scm.version.guess_next_simple_semver(
            version.tag, retain=setuptools_scm.version.SEMVER_LEN, increment=False)
    else:
        return version.format_next_version(
            setuptools_scm.version.guess_next_simple_semver, retain=setuptools_scm.version.SEMVER_MINOR
        )


setup(
    name='randovania',
    use_scm_version={
        "version_scheme": version_scheme,
        "local_scheme": "no-local-version",
        "write_to": "randovania/version.py",
    },
    author='Henrique Gemignani',
    url='https://github.com/randovania/randovania',
    description='A randomizer for the Metroid Prime 2: Echoes.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    cmdclass={
        "build_ui": build_ui,
        "build_py": custom_build_py
    },
    scripts=[
    ],
    package_data={
        "randovania": [
            "data/*",
            "data/ClarisPrimeRandomizer/*",
        ]
    },
    license='License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Games/Entertainment',
    ],
    python_requires=">=3.9",
    setup_requires=[
        "setuptools_scm>=3.5.0",
        "pyqt-distutils",
    ],
    install_requires=[
        'networkx',
        'bitstruct',
        'construct',
        'tenacity>=7.0.0',
        'python-slugify',
        'python-socketio[asyncio_client]',
        'aiohttp',
        'aiofiles',
        'dulwich>=0.20',
        'py_randomprime>=0.3.6',
    ],
    extras_require={
        "gui": [
            'PySide2>=5.15,<5.16',
            'appdirs',
            'qasync',
            'async-wiiload',
            'dolphin-memory-engine>=1.0.2',
            'markdown',
            'matplotlib>=3.3.3',
            'nod>=1.3',
            'pid>=3.0.0',
            'pypresence',
            'qdarkstyle',
        ],
        "server": [
            "cryptography",
            "discord.py",
            "eventlet",
            "flask-discord",
            "flask-socketio",
            "prometheus-flask-exporter",
            "peewee",
            "requests-oauthlib",
        ],
        "test": [
            'pytest',
            'pytest-cov',
            'pytest-qt',
            'pytest-asyncio',
            'pytest-mock',
            'mock>=4.0',
        ]
    },
    entry_points={
        'console_scripts': [
            "randovania = randovania.__main__:main"
        ]
    },
)
