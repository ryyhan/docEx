from setuptools import setup, find_packages

with open("README.MD", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="docex-serve",
    version="1.0.0",
    author="ryyhan",
    description="Document extraction API with multi-provider VLM support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ryyhan/docEx",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: General",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.32.0",
        "docling>=2.0.0",
        "python-multipart>=0.0.12",
        "pydantic-settings>=2.6.0",
        "markdown>=3.7",
        "transformers==4.57.3",
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.0",
            "httpx>=0.27.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "docex-server=docex_serve.cli:main",
        ],
    },
    include_package_data=True,
)
