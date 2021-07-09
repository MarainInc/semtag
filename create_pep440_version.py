#!/usr/bin/env python3

"""Script to create a PEP 440-compliant version identifier from a semtag version identifier.

This script is useful when one wants to publish Python packages and tag them with the version information
provided by semtag. Python packages must be tagged with a PEP 440-compliant version identifier and semantic
versioning [is not fully compatible](https://www.python.org/dev/peps/pep-0440/#semantic-versioning) with PEP 440.

This script expects one argument:
- Semtag version identifier.

Example:
    # Standalone use 
    ./create_pep440_version.py "v0.14.0-alpha.1.2"

    # Together with semtag
    ./create_pep440_version.py $(./semtag getcurrent)


Testing:
    This script includes self-testing functionality. It can be accessed by running `./create_pep440_version.py test`

See Also:
    - [PEP 440](https://www.python.org/dev/peps/pep-0440/)
"""

import sys
import re


def create_pep440_version(semtag_version):
    """Create a PEP440-compliant version identifier from a semtag version identifier.

    Args:
        semtag_version (str): Semtag version identifier

    Returns:
        str: PEP440-compliant version identifier.
    """

    if "unstaged" in semtag_version or "uncommitted" in semtag_version:
        raise ValueError("Cannot create PEP440-compliant version identifier if there are uncommited or unstaged changes.")

    # Regex pattern taken from https://semver.org/
    semver_pattern = r"^v(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"

    result = re.match(semver_pattern, semtag_version)
    result_dict = result.groupdict()

    major = result_dict["major"]
    minor = result_dict["minor"]
    patch = result_dict["patch"]

    epoch_segment = f"{major}."
    release_segment = f"{minor}.{patch}"

    prerelease_segment, dev_segment = _get_prerelease_and_dev_segment(result_dict)

    local_version_label = _get_local_version_label(result_dict)

    pep440_version = f"{epoch_segment}{release_segment}{prerelease_segment}{dev_segment}{local_version_label}"

    return pep440_version


def _get_prerelease_and_dev_segment(result_dict):
    def raise_error():
        raise ValueError(f"Do not know how to handle prerelease {prerelease}.")

    prerelease_opt = result_dict.get("prerelease")

    prerelease_segment = ""
    dev_segment = ""

    if prerelease_opt:
        prerelease = prerelease_opt
        prerelease_parts = prerelease.split(".")

        dev_value = None

        if len(prerelease_parts) not in {2, 3}:
            raise_error()

        prerelease_cycle_to_short_name = {"alpha": "a", "beta": "b", "rc": "rc"}

        prerelease_cycle_short_name_opt = prerelease_cycle_to_short_name.get(prerelease_parts[0])

        if prerelease_cycle_short_name_opt:
            prerelease_cycle_short_name = prerelease_cycle_short_name_opt
            prerelease_value = prerelease_parts[1]
            prerelease_segment = f"{prerelease_cycle_short_name}{prerelease_value}"

            if len(prerelease_parts) == 3:
                dev_value = prerelease_parts[2]

        elif prerelease_parts[0] == "dev":
            if len(prerelease_parts) == 2:
                dev_value = prerelease_parts[1]
            else:
                raise_error()
        else:
            raise_error()

        if dev_value is not None:
            dev_segment = f".dev{dev_value}"

    return prerelease_segment, dev_segment


def _get_local_version_label(result_dict):
    buildmetadata_opt = result_dict.get("buildmetadata")

    local_version_label = ""

    if buildmetadata_opt:
        buildmetadata = buildmetadata_opt
        commit_hash = buildmetadata.partition(".")[0]

        local_version_label = f"+{commit_hash}"

    return local_version_label


def _test_create_pep440_version():
    semtag_version_to_pep440_version = {
        "v0.14.0-alpha.1.2+f0e563586.feature-MLB-2000-developer-create-python-compatibl": "0.14.0a1.dev2+f0e563586",
        "v0.14.0-alpha.1.2": "0.14.0a1.dev2",
        "v0.14.0-alpha.1": "0.14.0a1",
        "v0.14.0-beta.1": "0.14.0b1",
        "v0.14.0-rc.1": "0.14.0rc1",
        "v0.13.1-dev.1": "0.13.1.dev1",
        "v0.14.0": "0.14.0",
        "v0.15.0": "0.15.0",
        "v1.15.0": "1.15.0",
    }

    for semtag_version, pep440_version_ref in semtag_version_to_pep440_version.items():
        pep440_version = create_pep440_version(semtag_version)
        assert (
            pep440_version == pep440_version_ref
        ), f"Failure for {semtag_version}. Got {pep440_version}. Expected {pep440_version_ref}."

    print("Test passed.")


if __name__ == "__main__":
    n_argv = len(sys.argv)
    if n_argv != 2:
        sys.exit(f"Error: Expected 1 argument, got {n_argv - 1}.")

    arg = sys.argv[1]

    if arg == "test":
        _test_create_pep440_version()
    else:
        pep440_version = create_pep440_version(semtag_version=arg)
        print(pep440_version)
