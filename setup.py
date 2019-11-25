from setuptools import setup, find_packages

setup(
    name='gamification',
    version='0.2',
    py_modules=['gamification'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'canvasapi',
    ],
    entry_points='''
    [console_scripts]
    gamification=gamification:cli
    ''',
)