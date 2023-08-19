import os
import platform
from typing import Optional


def read_requirements_file(filename: str) -> [str]:
    with open(filename) as file:
        return file.read().strip().split("\n")


def get_names_from_wheels(folder: str) -> [str]:
    """Generate a list like requirements.txt file of CI compiled wheels.
    @param folder: The folder where compiled wheels are.
    @return: A list of pip dependencies names
    """
    wheel_files = os.listdir(folder)
    return [
        get_name_from_wheel(os.path.basename(wheel_file)) for wheel_file in wheel_files
    ]


def get_name_from_wheel(wheel_filename: str) -> str:
    """
    Extract wheel requirement from filename
    @param wheel_filename: The file of a whl
    @return: The requirement name of wheel.

    Example: pkcs7-0.1.2-py3-none-any.whl return pkcs7
    """
    return wheel_filename.split("-")[0]


def merge_requirements(requirements: [str], to_merge_requirements: [str]) -> [str]:
    """
    Merge two pip requirements list.
    @param requirements: Base requirements list.
    @param to_merge_requirements: Requirements list to merge.
    @return: A merged requirements list.
    """
    merged = []
    for requirement in requirements:
        to_merge = find_contains_substring(
            get_requirement_name(requirement), to_merge_requirements
        )
        merged.append(to_merge if to_merge is not None else requirement)
    return merged


def delete_requirements(requirements: [str], to_remove: [str]) -> [str]:
    return list(
        filter(lambda req: find_contains_substring(req, to_remove) is None, requirements)
    )


def find_contains_substring(substring: str, strings: [str]) -> Optional[str]:
    founded = [string for string in strings if substring in string]
    return founded[0] if founded else None


def intersect_contains_string(strings1: [str], strings2: [str]) -> [str]:
    return list(
        filter(
            lambda requirement: any(string2 in requirement for string2 in strings2),
            strings1,
        )
    )


def get_requirement_name(requirement: str) -> str:
    if "==" in requirement:
        return requirement.split("==")[0]
    else:
        return requirement


def requirements_filename_by_arch() -> str:
    requirements_file = f"requirements-{platform.machine().lower()}.txt"
    if os.path.exists(requirements_file):
        return requirements_file
    else:
        return "requirements.txt"
