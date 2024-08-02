from setuptools import setup
import json

with open("metadata.json", encoding="utf-8") as fp:
    metadata = json.load(fp)

setup(
    name='lexibank_keypano',
    py_modules=['lexibank_keypano'],
    include_package_data=True,
    url=metadata.get("url", ""),
    zip_safe=False,
    entry_points={
        'lexibank.dataset': [
            'keypano=lexibank_keypano:Dataset',
        ],
    },
    install_requires=[
        "pylexibank>=3.2.0",
        "collabutils",
        "cartopy",
        "matplotlib",
        "python-igraph",
        "scipy",
        "idspy"
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
