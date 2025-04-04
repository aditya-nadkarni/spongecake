from setuptools import setup, find_packages

setup(
    name="spongecake",
    version="0.1.10",
    description="Open source SDK to launch OpenAI computer use agents",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Terrell Marshall",
    author_email="founders@passage-team.com",
    url="https://github.com/aditya-nadkarni/spongecake",
    packages=find_packages(exclude=["docker", "static", "test"]),
        install_requires=[
        "docker",         # List your dependencies here
        "openai>=1.66.3",
        "python-dotenv",  # If you're using dotenv, for example
        "requests",
        "marionette-driver>=3.0.0",  # For Firefox browser automation
        "pyautogui",  # For automating actions locally on MacOS
        # etc.
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)
