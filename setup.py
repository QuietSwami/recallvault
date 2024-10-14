from setuptools import setup, find_packages

setup(
    name='recallvault',
    version='1.0',
    packages=find_packages(),
    install_requires=[],  # List of dependencies if any
    entry_points={
        'console_scripts': [
            'recallvault=src.main:cli',  # Enables running recallvault as a CLI tool
        ]
    },
)
