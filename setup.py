from setuptools import setup, find_packages

setup(
    name="lsl",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyyaml",
        "jsonschema",
        "fastapi",
        "uvicorn",
        "jinja2",
        "python-multipart",
        "bcrypt",
        "docker",
        "requests",
        "psutil",
    ],
)
