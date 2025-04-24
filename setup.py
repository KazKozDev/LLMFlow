from setuptools import setup, find_packages

setup(
    name="llmflow",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'requests>=2.28.0',
        'pandas>=1.4.0',
        'nltk>=3.7.0',
        'beautifulsoup4>=4.11.0',
        'newspaper3k>=0.2.8',
        'geopy>=2.2.0',
    ],
    python_requires='>=3.9',
) 