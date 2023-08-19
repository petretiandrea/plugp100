import os
import re
import sys

wheel_regex = r"(.*)(-.*)(-.*)(-.*-)(.*)(_.*).whl"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage rename_wheels.py <platform_name>")
        exit(-1)

    platform_name = sys.argv[1]

    # replace platform (e.g. linux --> manylinux)
    generated_wheel_names = list(filter(lambda e: ".whl" in e, os.listdir("dist/")))
    for generated_wheel_name in generated_wheel_names:
        new_wheel_name = re.sub(
            wheel_regex, rf"\1\2\3\4{platform_name}.whl", generated_wheel_name
        )
        os.rename(
            os.path.join("dist/", generated_wheel_name),
            os.path.join("dist/", new_wheel_name),
        )
