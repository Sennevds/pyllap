from setuptools import setup, find_packages

setup(
    name='pyllap',

    version='0.1',

    description='LLAP control library.',
    long_description='A library for sending and receiving LLAP messages for controlling Ciseco hardware.',

    url='https://github.com/sgsabbage/pyllap',

    author='Sean Sabbage',
    author_email='sgsabbage@gmail.com',

    license='GPLv3',

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',

        'Intended Audience :: Developers',

        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4'
    ],

    keywords='llap ciseco',

    packages=find_packages(),

    install_requires=['pyserial'],

)
