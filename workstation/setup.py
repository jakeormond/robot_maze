from setuptools import setup, find_packages

setup(
    name="robot_honeycomb_maze",
    version="1.0.0",
    author="Jake_Ormond",
    description="A version of the honeycomb maze using line-following robots",
    packages=find_packages(),
    install_requires=[  # List your package dependencies here
        "pandas",
        "numpy",
        "matplotlib",
        "pyyaml",
        "cv2"
    ],
)