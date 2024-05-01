from setuptools import setup, find_packages

setup(
    name="taskbox",
    version="0.1.0",
    description="A package for managing tasks",
    author="Dongbox",
    author_email="sfreebobo@gmail.com",
    url="https://github.com/dongbox/taskbox",
    packages=find_packages(),
    install_requires=[
        # Add any dependencies required by your package here
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
