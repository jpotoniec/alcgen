from Cython.Build import cythonize
from setuptools import setup

setup(
    ext_modules=cythonize(["alcgen/aux.pyx"], annotate=True),
)
