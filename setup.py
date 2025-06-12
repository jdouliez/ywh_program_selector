from setuptools import setup, find_packages

setup(
    name='ywh_program_selector',
    version='0.1.0',
    packages=find_packages(),
    install_requires=open("requirements.txt").readlines(),
    entry_points={
        'console_scripts': [
            'ywh_program_selector = ywh_program_selector.ywh_program_selector:main',
        ],
    },
    author="@_Ali4s_",
    author_email="jordan.douliez@gmail.com",
    description='The ywh_program_selector project is a tool designed to help users manage and prioritize their YesWeHack (YWH) private programs',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/jdouliez/ywh_program_selector',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)