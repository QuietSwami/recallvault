from setuptools import setup, find_packages

setup(
    name='recallvault',
    version='1.0',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "rich-click",  # Include any other dependencies here
    ],
    entry_points={
        'console_scripts': [
            'recallvault = main:cli',  # Points to the 'cli' function inside 'main.py'
        ]
    },
)