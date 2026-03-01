from setuptools import setup, find_packages

setup(
    name="unical",
    version="0.1",
    package_dir={"": "src"},  # directory where packages are located
    packages=find_packages(where="src"),  # find all packages and list them
    author="ceskoviz83",
    python_requires=">=3.10", # compatible python version
    description="Unical Modbus TCP - Communication Library",
    install_requires=[
        # Elenca qui le dipendenze, es: 'requests>=2.25.1'
            "numpy>=2.4.2",
            "pandas>=2.3.3",
            "pandas-stubs==2.3.3.260113",
            "pymodbus>=3.11",
            "python-dateutil==2.9.0.post0",
            "pytz==2025.2",
            "six==1.17.0",
            "tabulate==0.9.0",
            "types-pytz==2025.2.0.20251108",
            "tzdata==2025.3",
            "python-dotenv==1.0.1",
            "sqlalchemy"
    ],
)