"""
Striver's 180-Day SDE Sheet — Test Runner

Entry point for testing problem solutions against LeetCode test cases.

Usage:
    python main.py [problem-name]

Each problem file lives in a topic/subtopic folder matching the 180 sheet
(e.g. Arrays/LinearScan, BinarySearch/SearchOnAnswer, ...) and contains ONLY
the LeetCode `Solution` class. All test cases are defined here in TEST_CASES.
"""

import copy
import importlib
import sys
from typing import Any

# "problem-name": ("topic.subtopic", "module_name", "method_name")
KNOWN_PROBLEMS = {
    "majority-element": ("Arrays.LinearScan", "MajorityElement", "majorityElement"),
    "majority-element-ii": ("Arrays.LinearScan", "MajorityElementII", "majorityElement"),
    "kadanes-algorithm": ("Arrays.LinearScan", "KadanesAlgorithm", "maxSubArray"),
    "maximum-product-subarray": ("Arrays.LinearScan", "MaximumProductSubarray", "maxProduct"),
}

# "problem-name": [(input_args_tuple, expected), ...]
TEST_CASES: dict[str, list[tuple[tuple[Any, ...], Any]]] = {
    "majority-element": [
        (([3, 2, 3],), 3),
        (([2, 2, 1, 1, 1, 2, 2],), 2),
    ],
    "majority-element-ii": [
        (([3, 2, 3],), [3]),
        (([1],), [1]),
        (([1, 2],), [1, 2]),
    ],
    "kadanes-algorithm": [
        (([-2, 1, -3, 4, -1, 2, 1, -5, 4],), 6),
        (([1],), 1),
        (([5, 4, -1, 7, 8],), 23),
    ],
    "maximum-product-subarray": [
        (([2, 3, -2, 4],), 6),
        (([-2, 0, -1],), 0),
    ],
}


def load_problem(key: str):
    topic, module, _method = KNOWN_PROBLEMS[key]
    return importlib.import_module(f"{topic}.{module}")


def main():
    args = sys.argv[1:]
    if args:
        run_problem(args[0].strip().lower())
        return

    if not KNOWN_PROBLEMS:
        print("No problems registered yet. Ask opencode to add the first one.")
        return

    for key in KNOWN_PROBLEMS:
        run_problem(key)


def run_problem(key: str):
    try:
        mod = load_problem(key)
    except KeyError:
        print(f"[!] Unknown problem '{key}'. Registered: {list(KNOWN_PROBLEMS)}")
        return

    _, _, method = KNOWN_PROBLEMS[key]
    print(f"\n=== {key} ===")
    cases = TEST_CASES.get(key)
    if not cases:
        print(f"[!] {key} has no test cases in main.py.")
        return

    passed = 0
    for i, (inp, expected) in enumerate(cases, 1):
        call_args = copy.deepcopy(inp)
        got = getattr(mod.Solution(), method)(*call_args)
        # in-place methods return None — compare the mutated first argument
        actual = got if got is not None else call_args[0]
        status = "PASS" if actual == expected else "FAIL"
        if status == "FAIL":
            print(f"  [{i}] {status}  input={inp}  expected={expected}  got={actual}")
        else:
            print(f"  [{i}] PASS")
        passed += status == "PASS"

    print(f"{key}: {passed}/{len(cases)} passed")


if __name__ == "__main__":
    main()