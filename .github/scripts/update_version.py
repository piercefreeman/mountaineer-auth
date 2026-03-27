# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "packaging",
#     "toml",
# ]
# ///

import sys
from pathlib import Path
from sys import stdout

import toml
from packaging.version import parse


def update_version_python(new_version: str):
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("pyproject.toml not found, skipping version update")  # noqa: T201
        return

    filedata = toml.loads(pyproject_path.read_text())

    # Parse the new version to ensure it's valid and potentially reformat
    python_version = format_python_version(new_version)

    updated = False

    # Update poetry version if it exists
    if "tool" in filedata and "poetry" in filedata["tool"]:
        filedata["tool"]["poetry"]["version"] = python_version
        updated = True

    # Update project.version if it exists
    if "project" in filedata and "version" in filedata["project"]:
        filedata["project"]["version"] = python_version
        updated = True

    if not updated:
        print(  # noqa: T201
            "Warning: Neither [tool.poetry] nor [project] sections found in pyproject.toml"
        )
        return

    pyproject_path.write_text(toml.dumps(filedata))


def format_python_version(new_version: str) -> str:
    parsed_version = parse(new_version)
    python_version = (
        f"{parsed_version.major}.{parsed_version.minor}.{parsed_version.micro}"
    )
    if parsed_version.is_prerelease and parsed_version.pre is not None:
        pre_release = ".".join(str(x) for x in parsed_version.pre)
        python_version += (
            f".dev{parsed_version.pre[-1]}"
            if pre_release.startswith("dev")
            else f"b{parsed_version.pre[-1]}"
        )
    if parsed_version.is_postrelease and parsed_version.post is not None:
        python_version += f".post{parsed_version.post}"
    if parsed_version.is_devrelease and parsed_version.dev is not None:
        python_version += f".dev{parsed_version.dev}"
    return python_version


if __name__ == "__main__":
    if len(sys.argv) != 2:
        stdout.write("Usage: python update_version.py <new_version>")
        sys.exit(1)
    new_version = sys.argv[1].lstrip("v")
    update_version_python(new_version)
    stdout.write(f"Updated version to: {new_version}")
