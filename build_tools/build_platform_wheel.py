import os
import platform
import sys

import packaging.tags

from ci_build_utils import (
    get_names_from_wheels,
    read_requirements_file,
    intersect_contains_string,
    delete_requirements,
)

SUPPORTED_ARCHITECTURES = ["armv6l", "armv7l", "amd64", "aarch64", "x86"]


def get_compiled_architectures(wheels_branch_folder: str) -> [str]:
    return list(
        filter(
            lambda folder: folder in SUPPORTED_ARCHITECTURES,
            os.listdir(wheels_branch_folder),
        )
    )


def get_build_platform() -> str:
    from distutils.util import get_platform

    return get_platform().replace("-", "_").replace(".", "_")


def get_interpreter_version() -> str:
    return f"{packaging.tags.interpreter_name()}{packaging.tags.interpreter_version()}"


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage build_platform_wheel.py <vendor_folder> <requirements_file_name>")
        exit(-1)

    python_executable = sys.executable
    vendor_folder = sys.argv[1]
    new_requirements_file = sys.argv[2]

    architecture = platform.machine().lower()
    requirements = read_requirements_file("requirements.txt")

    print(f"Using {vendor_folder} as vendor folder with {architecture} architecture")
    print(f"Generating requirements for vendoring...")

    vendor_requirement_names = get_names_from_wheels(vendor_folder)

    print("Removing vendoring requirements from requirements.txt")
    to_remove = intersect_contains_string(requirements, vendor_requirement_names)

    new_requirements = delete_requirements(requirements, to_remove)
    with open(new_requirements_file, "w") as file:
        file.writelines("\n".join(new_requirements))

    # force build binaries for specific platform
    os.environ["FORCE_BINARY"] = "True"
    os.system(f"{python_executable} setup.py bdist_wheel")

    print("Done.")
