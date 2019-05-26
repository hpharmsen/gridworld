from setuptools import setup

setup(
    name='gridworld',
    version='0.1',
    description='Array based grid which facilitates easy creation of grid based games and applications using Pygame.',
    url='https://github.com/hpharmsen/gridworld',
    author='HP Harmsen',
    author_email='hp@harmsen.nl',
    license='GPL',
    packages=['gridworld'],
    install_requires=['pygame'],
    zip_safe=False,
)
