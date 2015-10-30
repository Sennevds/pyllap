from setuptools import setup, find_packages

setup(
    name='pyllap',

    version='0.1',

    description='A library for sending and receiving LLAP messages for controlling Ciseco hardware.',
    long_description='There is a controller that leans heavily on the Python threading library to handle I/O and all the important things that must be done like ACKing messages to stop retries. It will also handle transmit retries and sleeping devices.',

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
