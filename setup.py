from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="leet_devops",
    version="0.0.1",
    description="Leet DevOps — GitHub + SSH Deploys + OpenAI Change Chat for Frappe",
    author="Aman Yousaf / Leet IT Solutions",
    author_email="dev@leetitsolutions.com",
    license="MIT",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
