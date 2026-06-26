from setuptools import find_namespace_packages, setup


setup(
    packages=find_namespace_packages(include=["atlas*"]),
    package_data={"atlas": ["database/schema.sql"]},
    entry_points={
        "console_scripts": [
            "atlas=atlas.cli.main:app",
        ],
    },
)
