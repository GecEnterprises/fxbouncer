from setuptools import setup, find_packages

setup(
    name='fxbouncer',
    version='0.1.0',
    description='A CLI tool to download content from X or other platforms using fxtwitter.',
    author='GecEnterprises',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests==2.32.3',
        'beautifulsoup4==4.12.3',
        'click==8.1.7',
        'tqdm==4.66.5'
    ],
    entry_points='''
        [console_scripts]
        fxbouncer=fxbouncer.cli:cli
    ''',
)
