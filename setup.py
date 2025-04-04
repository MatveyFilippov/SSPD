from setuptools import setup, find_packages


def requirements() -> list[str]:
    with open("requirements.txt", "r", encoding="UTF-8") as rf:
        return rf.read().splitlines()


def readme() -> str:
    with open("README.md", "r") as f:
        return f.read()


setup(
    name="sspd",
    author="Homer",
    author_email="mdfilippov_2@edu.hse.ru",
    version="1.3.0",
    packages=find_packages(),
    install_requires=requirements(),
    url="https://github.com/MatveyFilippov/SSPD?tab=readme-ov-file#sspd---sshscp-project-delivery",
    project_urls={
        "GitHub": "https://github.com/MatveyFilippov/SSPD"
    },
    description="SSH/SCP Project Delivery",
    long_description=readme(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
)
# python3 setup.py sdist bdist_wheel
