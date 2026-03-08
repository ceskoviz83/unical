from setuptools import setup, find_packages

setup(
    name="unical",
    version="0.2",
    package_dir={"": "src"},  # directory where packages are located
    packages=find_packages(where="src"),  # find all packages and list them
    author="ceskoviz83",
    python_requires=">=3.10", # compatible python version
    description="Unical Modbus TCP - Communication Library",
    install_requires=["pandas",
                      "setuptools",
                    "pandas-stubs",
                    "pymodbus>=3.11",
                    "tabulate>=0.9.0",
                    "python-dotenv",
                    "sqlalchemy",
                    "unical"],

)