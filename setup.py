import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bascontrolns",
    version="0.0.3",
    author="Steven Bailey and Gerrod Bailey",
    author_email="sjpbailey@comcast.net",
    description="BASpi/20/pi/ao/po control module API interface",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sjpbailey/bascontrol_ns",
    packages=setuptools.find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'requests',
    ]

    
)