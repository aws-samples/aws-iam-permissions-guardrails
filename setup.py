import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="iam-permissions-guardrails",  # Replace with your own username
    version="0.0.2",
    author="Josh Joy",
    author_email="jjjoy@amazon.com",
    description="IAM Permissions Guardrails module",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://code.amazon.com/packages/IAM-Permissions-Guardrails/trees/mainline",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=["aws-cdk.core>=1.74.0", "aws-cdk.custom-resources>=1.74.0","aws-cdk.aws_lambda>=1.74.0","aws-cdk.aws_iam>=1.74.0"],
)
