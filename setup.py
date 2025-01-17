from setuptools import setup, find_packages


def requirements() -> list[str]:
    with open("requirements.txt", "r", encoding="UTF-8") as rf:
        return [req.removesuffix("\n") for req in rf.readlines()]


def readme() -> str:
    with open("README.md", "r") as f:
        return f.read()


setup(
    name="sspd",
    author="Homer",
    version="1.2.0",
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
