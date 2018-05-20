from setuptools import setup, find_packages
from setuptools.command.build_py import build_py

from pyqt_distutils.build_ui import build_ui


class custom_build_py(build_py):
    def run(self):
        self.run_command('build_ui')
        super().run()


from randovania import VERSION

setup(
    name='randovania',
    version=VERSION,
    author='Henrique Gemignani',
    url='https://github.com/henriquegemignani/randovania',
    description='A randomizer validator for the Metroid Prime series.',
    packages=find_packages(),
    cmdclass={
        "build_ui": build_ui,
        "build_py": custom_build_py
    },
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
        'py', 'PyQt5', 'appdirs', ],
    setup_requires=[
        'pytest', 'markdown', 'PyInstaller', 'pyqt-distutils'
    ],
    entry_points={
        'console_scripts': [
            "randovania = randovania.__main__:main"
        ]
    },
)
