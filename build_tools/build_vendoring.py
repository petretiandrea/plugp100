"""
Script to build wheels which are unavailable from PyPi, caused by unsupported cpu architecture (armv7 and armv6).
"""

import os
import platform
import sys

from ci_build_utils import (
    read_requirements_file,
    intersect_contains_string,
    get_requirement_name,
)

REQUIREMENTS = read_requirements_file("requirements.txt")


def get_requirements_to_compile(requirements: [str], arch: str) -> [str]:
    compile_file = f"vendor-{arch}.txt"
    if os.path.exists(compile_file):
        return intersect_contains_string(
            requirements, read_requirements_file(compile_file)
        )
    else:
        return []


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage build_vendoring.py <vendor_folder> <pip_cache_folder>")
        exit(-1)

    current_arch = platform.machine().lower()
    vendor_wheels_folder = sys.argv[1]
    pip_cache_dir = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"""Detected {current_arch}.\nUsing vendor folder: {vendor_wheels_folder}.\n""")

    print(f"Extracting requirements to compile.")
    requirements_to_compile = get_requirements_to_compile(REQUIREMENTS, current_arch)

    if len(requirements_to_compile) > 0:
        print(f"Found {len(requirements_to_compile)} wheels to compile.")
        print("Building wheels...")
        cache_dir_command = f"--cache-dir {pip_cache_dir}" if pip_cache_dir else ""
        compile_wheels = f"--no-binary :all:"
        for requirement in requirements_to_compile:
            vendor_requirement_folder = os.path.join(
                vendor_wheels_folder, get_requirement_name(requirement)
            )
            os.system(
                f"{sys.executable} -m pip install {requirement} -t {vendor_requirement_folder} {compile_wheels} {cache_dir_command}"
            )
    else:
        print("No requirements to vendor found.")
