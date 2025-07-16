from Cython.Build import cythonize
from setuptools import setup, Extension

# setup(
# ext_modules=cythonize("alcgen/cooccurrences.pyx", annotate=True)
# )

setup(ext_modules=cythonize(Extension(
    "alcgen.cooccurrences",  # the extension name
    sources=["alcgen/cooccurrences.pyx"],  # the Cython source and
    # additional C++ source files
    language="c++",  # generate and compile C++ code
extra_compile_args=["-std=c++20"]
), annotate=True))
