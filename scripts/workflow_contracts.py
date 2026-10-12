#!/usr/bin/env python3
# Vendored release toolkit; change the toolkit source, then render again.
# ruff: noqa
# mypy: ignore-errors
# pylint: skip-file
# fmt: off
"""Check the CI entry point and CodeQL compatibility before expensive validation."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml


QUALITY_GATE = "quality-gate.yml"
COMMIT_SHA_PATTERN = r"[0-9a-f]{40}"

class UniqueKeyLoader(yaml.BaseLoader):
    """Keep YAML scalars as strings and reject ambiguous mappings."""

    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in mapping:
                raise ValueError(f"Duplicate or non-string YAML key at {key_node.start_mark}")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def validate_codeql(workflows):
    """All CodeQL components in the repository share one immutable release."""
    repository_pins = set()
    for filename, workflow in workflows.items():
        for name, job in workflow.get("jobs", {}).items():
            pins = {
                step["uses"].rsplit("@", 1)[-1]
                for step in job.get("steps", [])
                if re.match(
                    r"github/codeql-action/(init|autobuild|analyze|upload-sarif)@",
                    step.get("uses", ""),
                )
            }
            if len(pins) > 1 or any(
                not re.fullmatch(COMMIT_SHA_PATTERN, pin) for pin in pins
            ):
                raise ValueError(
                    f"{filename}/{name}: CodeQL actions must share one full commit SHA"
                )
            repository_pins.update(pins)
    if len(repository_pins) > 1:
        raise ValueError(
            "CodeQL actions across workflows must share one full commit SHA"
        )


def yaml_member(node, name):
    """Locate one parsed YAML value without constructing Python objects."""
    if isinstance(node, yaml.MappingNode):
        return next((value for key, value in node.value if key.value == name), None)
    return None


def validate_codeql_update_metadata(sources):
    """Keep every CodeQL SHA discoverable by Renovate, including SARIF uploads."""
    versions = set()
    for filename, source in sources.items():
        root = yaml.compose(source, Loader=yaml.BaseLoader)
        jobs = yaml_member(root, "jobs")
        if not isinstance(jobs, yaml.MappingNode):
            continue
        lines = source.splitlines()
        for _, job in jobs.value:
            steps = yaml_member(job, "steps")
            if not isinstance(steps, yaml.SequenceNode):
                continue
            for step in steps.value:
                reference = yaml_member(step, "uses")
                if not isinstance(reference, yaml.ScalarNode) or not re.fullmatch(
                    r"github/codeql-action/(init|autobuild|analyze|upload-sarif)@"
                    + COMMIT_SHA_PATTERN, reference.value
                ):
                    continue
                mark = reference.end_mark
                tail = lines[mark.line][mark.column:] if mark.line < len(lines) else ""
                comment = re.match(r"[ \t]*#[ \t]*(v[0-9]+\.[0-9]+\.[0-9]+)(?:[ \t]|$)", tail)
                if comment is None:
                    raise ValueError(
                        f"{filename}:{reference.start_mark.line + 1}: "
                        "CodeQL SHA needs an inline full release comment for Renovate"
                    )
                versions.add(comment[1])
    if len(versions) > 1:
        raise ValueError("CodeQL version comments must name the same release")


def validate_workflow_pins(filename, workflow, pins):
    """Require immutable actions and compare canonical generator pins when present."""
    for job in workflow.get("jobs", {}).values():
        references = [job.get("uses", "")] + [
            step.get("uses", "") for step in job.get("steps", [])
        ]
        for reference in references:
            if not reference or reference.startswith("./"):
                continue
            action, _, revision = reference.partition("@")
            if not re.fullmatch(COMMIT_SHA_PATTERN, revision):
                raise ValueError(f"{filename}: {action} must use a full commit SHA")
            if pins is not None and (action not in pins or revision != pins[action]):
                raise ValueError(f"{filename}: {action} differs from generator pins")


def validate_generator_pins(directory, workflows):
    """Validate generated consumers and the toolkit's canonical pin manifest."""
    manifest = directory / ".github/action-pins.json"
    # Consumers vendor the generated scripts, not the generator or its manifest.
    # The canonical toolkit must retain the manifest consumed by its generator.
    if not manifest.exists() and (directory / "scripts/install_release.py").exists():
        raise ValueError("Missing generator action-pin manifest")
    pins = None if not manifest.exists() else {
        pin["packageName"]: pin["digest"] for pin in json.loads(manifest.read_text())
    }
    if pins is not None and any(not re.fullmatch(COMMIT_SHA_PATTERN, pin) for pin in pins.values()):
        raise ValueError("Generator pins must be full commit SHAs")
    for filename, workflow in workflows.items():
        if filename not in {QUALITY_GATE, "release-pipeline.yml"}:
            validate_workflow_pins(filename, workflow, None)
            continue
        source = (directory / ".github/workflows" / filename).read_text()
        if not source.startswith(
            "# Generated by venus-os-ci-toolkit/scripts/install_release.py;"
        ):
            raise ValueError(f"{filename}: missing generator marker")
        validate_workflow_pins(filename, workflow, pins)


def _callable_workflow(workflows, visited, filename, chain=()):
    """Traverse callable workflows, retaining cycle detection before visited pruning."""
    if filename in chain:
        raise ValueError(f"Recursive validation: {chain} -> {filename}")
    if filename in visited:
        return
    workflow = workflows[filename]
    triggers = workflow.get("on", {})
    if not isinstance(triggers, dict) or "workflow_call" not in triggers:
        raise ValueError(f"{filename}: missing workflow_call")
    if set(triggers) - {"workflow_call", "workflow_dispatch"}:
        raise ValueError(f"{filename}: validation must start through Quality gate")
    visited.add(filename)
    for name, job in workflow.get("jobs", {}).items():
        reference = job.get("uses", "")
        if reference.startswith("./.github/workflows/"):
            _callable_workflow(workflows, visited, reference.rsplit("/", 1)[-1], (*chain, filename))
        elif "runs-on" in job and "timeout-minutes" not in job:
            raise ValueError(f"{filename}/{name}: an explicit timeout is required")


def validate_graph(workflows, validators):
    """Walk callable validators and enforce one orchestration entry point."""
    visited = set()

    for filename in validators:
        _callable_workflow(workflows, visited, filename)
    return visited


def validate(directory: Path, *, actions_only=False) -> None:
    """Reject duplicate validation triggers, missing gate jobs and mixed CodeQL pins."""
    policy = json.loads((directory / ".release-policy.json").read_text())
    workflows = {
        # UniqueKeyLoader inherits BaseLoader: no Python object construction.
        path.name: yaml.load(path.read_text(), Loader=UniqueKeyLoader)  # nosec B506
        for path in (directory / ".github/workflows").glob("*.y*ml")
    }
    validate_codeql(workflows)
    validate_codeql_update_metadata({
        path.name: path.read_text()
        for path in (directory / ".github/workflows").glob("*.y*ml")
    })
    validate_generator_pins(directory, workflows)
    if actions_only:
        return
    visited = validate_graph(workflows, policy["validation_workflows"])
    for filename, workflow in workflows.items():
        if (
            "pull_request" in workflow.get("on", {})
            and filename not in visited
            and filename
            not in {QUALITY_GATE, "auto-approve.yml", "auto-merge.yml"}
        ):
            raise ValueError(f"{filename}: PR validator is outside the required gate")
    gate = workflows[QUALITY_GATE]["jobs"]
    expected = {
        f"./.github/workflows/{filename}" for filename in policy["validation_workflows"]
    }
    actual = {job.get("uses") for job in gate.values() if "uses" in job}
    if actual != expected or set(gate["gate"].get("needs", [])) != set(gate) - {"gate"}:
        raise ValueError(
            "CI gate must require every configured validator and contract job"
        )
    if "workflow-contracts" not in gate:
        raise ValueError("CI gate must include its configuration contracts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actions-only", action="store_true")
    validate(Path.cwd(), actions_only=parser.parse_args().actions_only)
    print("CI entry point, timeouts and CodeQL pins are consistent.")
