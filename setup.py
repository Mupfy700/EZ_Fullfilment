from setuptools import setup, find_packages

setup(
    name='ez_fullfilment',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'tk',
    ],
    entry_points={
        'console_scripts': [
            'run_fullfilment=ez_fullfilment.scripts.run_fullfilment:main',
        ],
    },
)
