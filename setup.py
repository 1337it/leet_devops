from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="leet_devops",
    version="0.0.1",
    description="AI-powered DocType and Function Generator for Frappe",
    author="Leet DevOps",
    author_email="info@leetdevops.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)
