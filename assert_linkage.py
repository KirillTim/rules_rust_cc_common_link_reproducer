#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def bazel(*args: str) -> str:
    result = subprocess.run(
        ["bazel", "--nohome_rc", *args],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        result.check_returncode()
    return result.stdout


def link_markers(target: str, mode: str, markers: tuple[str, ...]) -> tuple[str, ...]:
    output = bazel(
        "aquery",
        f'mnemonic("CppLink", //:{target})',
        "--output=jsonproto",
        f"--dynamic_mode={mode}",
    )
    actions = json.loads(output)["actions"]
    links = [action for action in actions if action.get("mnemonic") == "CppLink"]
    assert len(links) == 1, f"expected one CppLink action for {target}: {links}"
    found = set()
    for argument in links[0].get("arguments", []):
        for marker in markers:
            if marker in argument:
                found.add(marker)
    return tuple(sorted(found))


def runfile_markers(target: str, mode: str, markers: tuple[str, ...]) -> tuple[str, ...]:
    expression = (
        '[f.basename for f in '
        'providers(target)["DefaultInfo"].default_runfiles.files.to_list()]'
    )
    output = bazel(
        "cquery",
        f"//:{target}",
        "--output=starlark",
        f"--starlark:expr={expression}",
        f"--dynamic_mode={mode}",
    )
    basenames = set(json.loads(output))
    # Keep only the runfiles whose basenames are requested markers.
    return tuple(sorted(basenames.intersection(markers)))


def main() -> int:
    failures = []

    runtime_markers = ("dummy.a", "dummy.so")
    cc_runtime = link_markers("cc_runtime_selection", "fully", runtime_markers)
    rust_runtime = link_markers("rust_runtime_selection", "fully", runtime_markers)
    print("USE CASE 1: toolchain runtime selection (--dynamic_mode=fully)")
    print(f"  C++ link:  {cc_runtime}")
    print(f"  Rust link: {rust_runtime}")
    if rust_runtime != cc_runtime:
        failures.append(
            f"runtime selection: Rust link {rust_runtime} != C++ link {cc_runtime}"
        )

    link_dep_markers = ("link_dep.so",)
    cc_link_dep = link_markers("cc_link_deps_runfiles", "off", link_dep_markers)
    rust_link_dep = link_markers("rust_link_deps_runfiles", "off", link_dep_markers)
    cc_link_dep_runfiles = runfile_markers(
        "cc_link_deps_runfiles", "off", link_dep_markers
    )
    rust_link_dep_runfiles = runfile_markers(
        "rust_link_deps_runfiles", "off", link_dep_markers
    )
    print("\nUSE CASE 2: shared link_deps runfiles (--dynamic_mode=off)")
    print(f"  C++ link/runfiles:  {cc_link_dep} / {cc_link_dep_runfiles}")
    print(f"  Rust link/runfiles: {rust_link_dep} / {rust_link_dep_runfiles}")
    expected_link_dep = ("link_dep.so",)
    if cc_link_dep != expected_link_dep or rust_link_dep != expected_link_dep:
        failures.append(
            f"link_deps setup: expected both links to contain {expected_link_dep}, "
            f"got C++ {cc_link_dep} and Rust {rust_link_dep}"
        )
    elif rust_link_dep_runfiles != cc_link_dep_runfiles:
        failures.append(
            "link_deps runfiles: "
            f"Rust {rust_link_dep_runfiles} != C++ {cc_link_dep_runfiles}"
        )

    if failures:
        print("\nREPRODUCED:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nBoth Rust results match their C++ baselines.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
