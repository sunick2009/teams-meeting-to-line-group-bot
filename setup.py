from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="teams-meeting-to-line-group-bot",
    version="1.0.0",
    author="Teams-LINE Bot Team",
    author_email="",
    description="將 Microsoft Teams 會議通知自動轉發到 LINE 群組，並提供智能翻譯功能的 Azure Function 應用程式",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sunick2009/teams-meeting-to-line-group-bot",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Chat",
        "Topic :: Office/Business :: Scheduling",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Framework :: Flask",
        "Environment :: Web Environment",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "isort>=5.0.0",
            "bandit>=1.7.0",
            "safety>=2.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "python-dotenv>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "teams-line-bot=function_app:main",
        ],
    },
    keywords="teams line bot azure functions webhook translation openai",
    project_urls={
        "Bug Reports": "https://github.com/sunick2009/teams-meeting-to-line-group-bot/issues",
        "Source": "https://github.com/sunick2009/teams-meeting-to-line-group-bot",
        "Documentation": "https://github.com/sunick2009/teams-meeting-to-line-group-bot/tree/main/docs",
    },
)
