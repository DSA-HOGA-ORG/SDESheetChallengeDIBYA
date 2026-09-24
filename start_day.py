#!/usr/bin/env python3
"""
Striver's SDE Sheet — daily problem helper.

Scaffolds a problem end-to-end for the daily workflow:

    python start_day.py set-matrix-zeroes --topic Arrays --subtopic LinearScan --method setZeroes

Steps:
  1. Create the solution file in Topic/Subtopic/ (Python or C++).
  2. Register the problem in the matching runner (main.py / main.cpp).
  3. Append a structured entry to logs/daily_log.md (new day block if needed)
     and bump the day + problem counters.
  4. Commit everything and push to GitHub (skip with --no-git).

Options:
  --topic TOPIC       topic folder, e.g. "Arrays"
  --subtopic SUB      subtopic folder, e.g. "LinearScan"
  --method METHOD     Solution method name (default: camelCase of the slug)
  --lang {python,cpp} solution language (default: python)
  --link URL          LeetCode link (default: leetcode.com/problems/<slug>)
  --status STATUS     Solved / Unsolved / "Need Review" (default: all unchecked)
  --no-git            create files and update the log only, no commit/push
"""

import argparse
import datetime
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "logs" / "daily_log.md"
MAIN_PY = ROOT / "main.py"
MAIN_CPP = ROOT / "main.cpp"

TOTAL_DAYS = 180


# ---------------------------------------------------------------------------
# name helpers
# ---------------------------------------------------------------------------

def to_class_name(slug: str) -> str:
    return "".join(part.capitalize() for part in slug.split("-"))


def to_camel(slug: str) -> str:
    parts = slug.split("-")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def to_snake(slug: str) -> str:
    return slug.replace("-", "_")


def problem_title(slug: str) -> str:
    return slug.replace("-", " ").title()


def today_header() -> str:
    t = datetime.date.today()
    return f"{t.strftime('%A')}, {t.strftime('%d %b %Y')}"


# ---------------------------------------------------------------------------
# solution files
# ---------------------------------------------------------------------------

def python_solution(topic, subtopic, slug, method) -> Path:
    module = to_class_name(slug)
    path = ROOT / topic / subtopic / f"{module}.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"class Solution:\n"
        f"    def {method}(self, *args):\n"
        f"        # TODO: implement; add test cases in main.py\n"
        f"        raise NotImplementedError\n"
    )
    return path


def cpp_solution(topic, subtopic, slug, link) -> Path:
    ns = to_snake(slug)
    path = ROOT / topic / subtopic / f"{ns}.cpp"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"// Problem: {problem_title(slug)}\n"
        f"// Topic: {topic} / {subtopic}\n"
        f"// LeetCode: {link}\n"
        f"\n"
        f"namespace {ns} {{\n"
        f"\n"
        f"class Solution {{\n"
        f"public:\n"
        f"    // TODO: implement; add test cases to run_{slug}() in main.cpp.\n"
        f"    void solve() {{}}\n"
        f"}};\n"
        f"\n"
        f"}}  // namespace {ns}\n"
    )
    return path


# ---------------------------------------------------------------------------
# registration in the runners
# ---------------------------------------------------------------------------

def insert_into_dict(text: str, anchor: str, entry: str) -> str:
    open_idx = text.index(anchor)
    brace = text.index("{", open_idx)
    close_idx = text.index("\n}", brace)
    return text[:close_idx] + "\n" + entry + text[close_idx:]


def insert_line_after(text: str, anchor: str, line: str) -> str:
    anchor_idx = text.index(anchor)
    eol = text.index("\n", anchor_idx)
    return text[:eol] + "\n" + line + text[eol:]


def insert_before(text: str, anchor: str, block: str) -> str:
    anchor_idx = text.index(anchor)
    return text[:anchor_idx] + block + text[anchor_idx:]


def register_python(slug, topic, subtopic, method):
    text = MAIN_PY.read_text()

    module = to_class_name(slug)
    known_entry = (
        f'    "{slug}": ("{topic}.{subtopic}", "{module}", "{method}"),'
    )
    text = insert_into_dict(text, "KNOWN_PROBLEMS = {", known_entry)

    test_entry = f'    "{slug}": [],'
    text = insert_into_dict(text, "TEST_CASES: dict", test_entry)

    MAIN_PY.write_text(text)
    return module


def register_cpp(slug, topic, subtopic):
    text = MAIN_CPP.read_text()
    ns = to_snake(slug)
    path = f"{topic}/{subtopic}/{ns}.cpp"

    text = insert_line_after(
        text, "// ---- solution includes (pure Solution classes) ----", f'#include "{path}"'
    )
    text = insert_before(
        text,
        "// slug -> test function",
        f"void run_{ns}() {{\n"
        f"    {ns}::Solution s;\n"
        f"    // TODO: add your test cases\n"
        f"    (void)s;\n"
        f"}}\n"
        f"\n",
    )
    text = insert_into_dict(
        text, "PROBLEMS = {", f'    {{"{slug}", run_{ns}}},'
    )
    MAIN_CPP.write_text(text)
    return ns


# ---------------------------------------------------------------------------
# daily log
# ---------------------------------------------------------------------------

def parse_log(text: str):
    lines = text.splitlines()
    title = lines[0]

    idx = 1
    preamble = [title]
    while idx < len(lines) and lines[idx].strip() != "---":
        preamble.append(lines[idx])
        idx += 1
    preamble.append(lines[idx])  # the counter separator "---"
    idx += 1

    blocks = []
    tail = []
    cur = None
    for line in lines[idx:]:
        if cur is None:
            if line.startswith("## Day "):
                cur = [line]
            elif line.strip().startswith("<!--"):
                tail = lines[idx:][lines[idx:].index(line):]
                cur = "DONE"
                break
        else:
            cur.append(line)
            if line.strip() == "---":
                blocks.append(cur)
                cur = None
    if cur not in (None, "DONE"):
        blocks.append(cur)

    return title, preamble, blocks, tail


def block_date(block):
    m = re.match(r"^## Day \d+ — (.+)$", block[0])
    return m.group(1) if m else ""


def problem_count(block):
    return sum(1 for line in block if line.strip().startswith("### Problem:"))


def set_block_problem_count(block, n):
    for i, line in enumerate(block):
        if line.startswith("**Problems solved:**"):
            block[i] = f"**Problems solved:** {n}"


def problem_block(slug, topic, subtopic, module, link, status):
    lines = [
        f"### Problem: {problem_title(slug)}",
        f"- **Link:** [LeetCode]({link}) | [Solution](../{topic}/{subtopic}/{module}.py)",
        "- **Time taken:** —",
        "- **Approach:**",
        "  - <!-- What technique/heuristic did you use? -->",
        "- **Complexity:** Time O(?) / Space O(?)",
        "- **Mistakes made:**",
        "  - <!-- Edge cases missed, syntax slips, wrong initial idea... -->",
        "- **What I learned:**",
        "  - <!-- Pattern recognized, takeaway -->",
        "- **Next steps:**",
        "  - <!-- Revisit blindly, try the follow-up, think of a new approach... -->",
    ]
    if status:
        order = ["Solved", "Unsolved", "Need Review"]
        cells = ["☑" if s == status else "☐" for s in order]
        lines.insert(
            2, "- **Status:** " + " | ".join(f"{m} {s}" for m, s in zip(cells, order))
        )
    else:
        lines.insert(2, "- **Status:** ☐ Solved | ☐ Unsolved | ☐ Need Review")
    return lines


def update_log(slug, topic, subtopic, module, link, status):
    text = LOG_PATH.read_text()
    title, preamble, blocks, tail = parse_log(text)
    today = today_header()

    active = next(
        (b for b in blocks if block_date(b) == today), None
    )
    if active is None:
        day = (max((int(re.match(r"^## Day (\d+)", b[0]).group(1)) for b in blocks)) + 1) if blocks else 1
        new_lines = [
            f"## Day {day:02d} — {today}",
            "",
            f"**Topic:** — ({topic})",
            "**Subtopic:** —",
            "**Problems solved:** 1",
            "**Total time spent:** —",
            "",
            "### Summary",
            "",
        ] + problem_block(slug, topic, subtopic, module, link, status) + [
            "",
            "---",
        ]
        blocks.append(new_lines)
        active = new_lines
    else:
        if any(line.strip().startswith(f"### Problem: {problem_title(slug)}") for line in active):
            raise SystemExit(f"[!] {problem_title(slug)} already logged for {today}.")
        lines = problem_block(slug, topic, subtopic, module, link, status)
        insert_at = max(i for i, line in enumerate(active) if line.strip() == "---")
        if active[insert_at - 1].strip() != "":
            lines = [""] + lines
        lines = lines + [""]
        active[:] = active[:insert_at] + lines + active[insert_at:]
        set_block_problem_count(active, problem_count(active))

    total_problems = sum(problem_count(b) for b in blocks)

    block_str = "\n\n".join("\n".join(b) for b in blocks)
    tail_str = "\n".join(tail) if tail else ""

    # preserve the empty line that originally separated the last block from the tail
    tail_str = ("\n" + tail_str) if tail_str else ""

    new_text = (
        "\n".join(preamble)
        + "\n\n"
        + block_str
        + tail_str
        + "\n"
    )
    new_text = re.sub(
        r"> Total days: \*\*\d+ / \d+\*\*",
        f"> Total days: **{len(blocks):02d} / {TOTAL_DAYS}**",
        new_text,
    )
    new_text = re.sub(
        r"> Total problems solved: \*\*\d+\*\*",
        f"> Total problems solved: **{total_problems}**",
        new_text,
    )

    LOG_PATH.write_text(new_text)
    return len(blocks), total_problems


# ---------------------------------------------------------------------------
# git
# ---------------------------------------------------------------------------

def run_git(args, check=True):
    res = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if check and res.returncode != 0:
        raise SystemExit(f"[!] git {' '.join(args)} failed:\n{res.stderr.strip()}")
    return res


def commit_and_push(slug, day):
    name = run_git(["git", "config", "user.name"], check=False).stdout.strip()
    email = run_git(["git", "config", "user.email"], check=False).stdout.strip()
    if not name or not email:
        run_git(["git", "config", "user.name", "DSA-HOGA-ORG"])
        run_git(["git", "config", "user.email", "DSA-HOGA-ORG@users.noreply.github.com"])

    run_git(["git", "add", "-A"])
    run_git(["git", "commit", "-m", f"feat: add {slug} (Day {day:02d})"])
    run_git(["git", "push", "origin", "HEAD"])
    print(f"[✓] committed and pushed: feat: add {slug} (Day {day:02d})")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scaffold, register, log, and push a daily SDE problem."
    )
    parser.add_argument("slug", help="kebab-case problem slug, e.g. set-matrix-zeroes")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--subtopic", required=True)
    parser.add_argument("--method", help="Solution method name")
    parser.add_argument("--lang", choices=["python", "cpp"], default="python")
    parser.add_argument("--link")
    parser.add_argument("--status", choices=["Solved", "Unsolved", "Need Review"])
    parser.add_argument("--no-git", action="store_true", help="skip commit + push")
    args = parser.parse_args()

    slug = args.slug.strip().lower()
    link = args.link or f"https://leetcode.com/problems/{slug}/"
    method = args.method or to_camel(slug)

    if args.lang == "cpp":
        file = cpp_solution(args.topic, args.subtopic, slug, link)
        module = register_cpp(slug, args.topic, args.subtopic)
    else:
        file = python_solution(args.topic, args.subtopic, slug, method)
        module = register_python(slug, args.topic, args.subtopic, method)

    day, total = update_log(slug, args.topic, args.subtopic, module, link, args.status)

    print(f"[✓] Solution: {file.relative_to(ROOT)}")
    print(f"[✓] Registered in {MAIN_PY.name if args.lang == 'python' else MAIN_CPP.name}")
    print(f"[✓] Logged in logs/daily_log.md (Day {day:02d}) — total problems: {total}")

    if not args.no_git:
        commit_and_push(slug, day)


if __name__ == "__main__":
    main()