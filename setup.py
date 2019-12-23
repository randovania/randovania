from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from pyqt_distutils.build_ui import build_ui


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
    python_requires=">=3.7",
    setup_requires=[
        "setuptools_scm",
        "pyqt-distutils",
    ],
    install_requires=[
        'PySide2>=5.12',
        'aiofiles',
        'appdirs',
        'asyncqt',
        'nod>=1.1',
        'requests',
        'networkx',
        'bitstruct',
        'construct',
        'tenacity',
        'pytest',
        'pytest-cov',
        'pytest-qt',
    ],
    entry_points={
        'console_scripts': [
            "randovania = randovania.__main__:main"
        ]
    },
)
