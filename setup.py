from setuptools import setup, find_packages

setup(
    name="Unical Communication Library",
    version="0.1",
    packages=find_packages(),
    author="ceskoviz83",
    description="Breve descrizione del pacchetto",
    install_requires=[
        # Elenca qui le dipendenze, es: 'requests>=2.25.1'
            "numpy==2.4.2",
            "pandas==2.3.3",
            "pandas-stubs==2.3.3.260113",
            "pymodbus==3.11.4",
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