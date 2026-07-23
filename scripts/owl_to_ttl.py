#!/usr/bin/env python3
"""Convert OWL/XML ontology modules to RITSO-style Turtle."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"

# OWL filename -> (pattern ttl, shacl ttl, ontology document IRI suffix for shacl)
MODULES: dict[str, tuple[str, str, str]] = {
    "Core.owl": (
        "core-pattern.ttl",
        "core-shacl.ttl",
        "https://w3id.org/citydata/part1/v1/Core/shacl",
    ),
    "ActivityPattern.owl": (
        "activity-pattern.ttl",
        "activity-shacl.ttl",
        "https://w3id.org/citydata/part1/v1/ActivityPattern/shacl",
    ),
    "AgentPattern.owl": (
        "agent-pattern.ttl",
        "agent-shacl.ttl",
        "https://w3id.org/citydata/part1/v1/AgentPattern/shacl",
    ),
    "AgreementPattern.owl": (
        "agreement-pattern.ttl",
        "agreement-shacl.ttl",
        "https://w3id.org/citydata/part1/v1/AgreementPattern/shacl",
    ),
    "ChangePattern.owl": (
        "change-pattern.ttl",
        "change-shacl.ttl",
        "https://w3id.org/citydata/part1/v1/ChangePattern/shacl",
    ),
    "CityUnitsPattern.owl": (
        "city-units-pattern.ttl",
        "city-units-shacl.ttl",
        "https://w3id.org/citydata/part1/v1/CityUnitsPattern/shacl",
    ),
    "GenericPropertiesPattern.owl": (
        "generic-properties-pattern.ttl",
        "generic-properties-shacl.ttl",
        "https://w3id.org/citydata/part1/v1/GenericPropertiesPattern/shacl",
    ),
    "MereologyPattern.owl": (
        "mereology-pattern.ttl",
        "mereology-shacl.ttl",
        "https://w3id.org/citydata/part1/v1/MereologyPattern/shacl",
    ),
    "OrganizationStructurePattern.owl": (
        "organization-structure-pattern.ttl",
        "organization-structure-shacl.ttl",
        "https://w3id.org/citydata/part1/v1/OrganizationStructurePattern/shacl",
    ),
    "RecurringEventPattern.owl": (
        "recurring-event-pattern.ttl",
        "recurring-event-shacl.ttl",
        "https://w3id.org/citydata/part1/v1/RecurringEventPattern/shacl",
    ),
    "ResourcePattern.owl": (
        "resource-pattern.ttl",
        "resource-shacl.ttl",
        "https://w3id.org/citydata/part1/v1/ResourcePattern/shacl",
    ),
    "SpatialLocPattern.owl": (
        "spatial-loc-pattern.ttl",
        "spatial-loc-shacl.ttl",
        "https://w3id.org/citydata/part1/v1/SpatialLocPattern/shacl",
    ),
}

MASTER_OWL = "5087-1.owl"
MASTER_TTL = "cdm1.ttl"

STANDARD_PREFIX_URIS: dict[str, str] = {
    "cdm1": "https://w3id.org/citydata/part1/v1/",
    "cc": "http://creativecommons.org/ns#",
    "dcterms": "http://purl.org/dc/terms/",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "sh": "http://www.w3.org/ns/shacl#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "vann": "http://purl.org/vocab/vann/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}

# Ontology document IRIs that omit the trailing slash in the source OWL files.
ONTOLOGY_IRI_NO_TRAILING_SLASH = frozenset({"Core", "ChangePattern"})


def ontology_document_iri(local_name: str) -> str:
    base = f"https://w3id.org/citydata/part1/v1/{local_name}"
    if local_name in ONTOLOGY_IRI_NO_TRAILING_SLASH:
        return base
    return f"{base}/"


SHACL_IMPORTS = [
    "https://w3id.org/citydata/part1/v1/Core/shacl",
    "https://w3id.org/citydata/part1/v1/ActivityPattern/shacl",
    "https://w3id.org/citydata/part1/v1/AgentPattern/shacl",
    "https://w3id.org/citydata/part1/v1/AgreementPattern/shacl",
    "https://w3id.org/citydata/part1/v1/ChangePattern/shacl",
    "https://w3id.org/citydata/part1/v1/CityUnitsPattern/shacl",
    "https://w3id.org/citydata/part1/v1/GenericPropertiesPattern/shacl",
    "https://w3id.org/citydata/part1/v1/MereologyPattern/shacl",
    "https://w3id.org/citydata/part1/v1/OrganizationStructurePattern/shacl",
    "https://w3id.org/citydata/part1/v1/RecurringEventPattern/shacl",
    "https://w3id.org/citydata/part1/v1/ResourcePattern/shacl",
    "https://w3id.org/citydata/part1/v1/SpatialLocPattern/shacl",
]


def prefix_block(extra: dict[str, str] | None = None) -> str:
    merged = dict(STANDARD_PREFIX_URIS)
    if extra:
        merged.update(extra)
    lines = [f"@prefix {name}: <{uri}> ." for name, uri in sorted(merged.items())]
    lines.append("")
    lines.append("@base <https://w3id.org/citydata/part1/v1/> .")
    lines.append("")
    return "\n".join(lines)


def riot_to_ttl(owl_path: Path) -> str:
    result = subprocess.run(
        ["riot", "--output=TTL", str(owl_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def external_prefixes(raw: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in raw.splitlines():
        match = re.match(r"^PREFIX\s+(\w*):\s+<([^>]+)>\s*$", line)
        if not match:
            continue
        name, uri = match.group(1), match.group(2)
        if name == "" or name in STANDARD_PREFIX_URIS:
            continue
        found[name] = uri
    return found


def normalize_pattern_ttl(raw: str) -> str:
    """Replace riot's PREFIX/BASE block with RITSO-style prefixes using cdm1:."""
    extras = external_prefixes(raw)
    body = re.sub(r"^#.*\n", "", raw, count=1, flags=re.MULTILINE)
    body = re.sub(r"^BASE\s+<[^>]+>\s*\n", "", body, count=1, flags=re.MULTILINE)
    body = re.sub(r"^PREFIX\s+[^\n]+\n", "", body, flags=re.MULTILINE)

    # riot emits ':' local names; use cdm1: for the default namespace.
    body = re.sub(r"(?<![\w:]):(?=[\w])", "cdm1:", body)
    # riot also emits base-relative subjects/objects like <ActivityPattern/>.
    body = re.sub(r"<([^:>/]+)/>", r"cdm1:\1", body)
    body = re.sub(r"cdm1:mainModule\s+\"true\"", "cdm1:mainModule true", body)
    body = fix_ontology_document_iris(body)
    return prefix_block(extras) + body.lstrip()


def fix_ontology_document_iris(body: str) -> str:
    """Align ontology subjects and pattern imports with published ontology IRIs."""
    body = re.sub(
        r"^cdm1:\s+rdf:type\s+owl:Ontology",
        "<https://w3id.org/citydata/part1/v1/>  rdf:type  owl:Ontology",
        body,
        count=1,
        flags=re.MULTILINE,
    )
    for local in (
        "ActivityPattern",
        "AgentPattern",
        "AgreementPattern",
        "ChangePattern",
        "CityUnitsPattern",
        "GenericPropertiesPattern",
        "MereologyPattern",
        "OrganizationStructurePattern",
        "RecurringEventPattern",
        "ResourcePattern",
        "SpatialLocPattern",
        "Core",
    ):
        iri = ontology_document_iri(local)
        body = re.sub(
            rf"^cdm1:{local}\s+rdf:type\s+owl:Ontology",
            f"<{iri}>  rdf:type  owl:Ontology",
            body,
            count=1,
            flags=re.MULTILINE,
        )
        body = re.sub(
            rf"owl:imports\s+cdm1:{local}\s*([;.])",
            rf"owl:imports <{iri}> \1",
            body,
        )
    return body


def pattern_ontology_iri(pattern_ttl: str) -> str | None:
    match = re.search(
        r"^<([^>]+)>\s+rdf:type\s+owl:Ontology\s*;",
        pattern_ttl,
        flags=re.MULTILINE,
    )
    if match:
        return match.group(1)
    match = re.search(
        r"^cdm1:(\S+)\s+rdf:type\s+owl:Ontology\s*;",
        pattern_ttl,
        flags=re.MULTILINE,
    )
    if not match:
        return None
    local = match.group(1).rstrip("/")
    if local in ("", "<>"):
        return "https://w3id.org/citydata/part1/v1/"
    return ontology_document_iri(local)


def shacl_shell(pattern_ttl_name: str, shacl_ttl_name: str, shacl_iri: str, pattern_iri: str) -> str:
    label = pattern_ttl_name.replace("-pattern.ttl", "").replace("-", " ").title()
    return f"""@prefix cdm1: <https://w3id.org/citydata/part1/v1/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix vann: <http://purl.org/vocab/vann/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<{shacl_iri}>
    rdf:type owl:Ontology ;
    dcterms:title "City Data Model Part 1 - {label} - SHACL constraints" ;
    skos:definition "SHACL validation shapes for the {label} pattern module." ;
    vann:preferredNamespaceUri "https://w3id.org/citydata/part1/v1/" ;
    vann:preferredNamespacePrefix "cdm1" ;
    owl:imports <{pattern_iri}> .
"""


def shacl_import_block() -> str:
    lines = [f"        owl:imports <{iri}> ;" for iri in SHACL_IMPORTS]
    lines.append("        .")
    return "\n".join(lines)


def write_master_ttl() -> None:
    raw = riot_to_ttl(DOCS / MASTER_OWL)
    body = normalize_pattern_ttl(raw)

    body = re.sub(
        r"(owl:imports\s+<https://w3id.org/citydata/part1/v1/RecurringEventPattern/>)\s*\.(\s*)$",
        r"\1 ;\n" + shacl_import_block() + r"\2",
        body,
        count=1,
        flags=re.MULTILINE,
    )
    (DOCS / MASTER_TTL).write_text(body, encoding="utf-8")


def write_catalog() -> None:
    entries = [
        ('duplicate:https://w3id.org/citydata/part1/v1/', MASTER_TTL),
    ]
    for pattern_ttl, shacl_ttl, _ in MODULES.values():
        entries.append(('duplicate:https://w3id.org/citydata/part1/v1/', pattern_ttl))
        entries.append((f"shacl:{pattern_ttl}", shacl_ttl))
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<catalog prefer="public" xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">',
        '    <group id="Folder Repository, directory=file:./, recursive=false, prefer="public" xml:base="">',
    ]
    for name, uri in entries:
        lines.append(f'        <uri name="{name}" uri="{uri}"/>')
    lines.extend(["    </group>", "</catalog>", ""])
    (DOCS / "catalog-v001.xml").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    for owl_name, (pattern_ttl, shacl_ttl, shacl_iri) in MODULES.items():
        owl_path = DOCS / owl_name
        if not owl_path.exists():
            print(f"Missing {owl_path}", file=sys.stderr)
            return 1
        raw = riot_to_ttl(owl_path)
        pattern_body = normalize_pattern_ttl(raw)
        (DOCS / pattern_ttl).write_text(pattern_body, encoding="utf-8")

        pattern_iri = pattern_ontology_iri(pattern_body)
        if not pattern_iri:
            print(f"Could not find ontology IRI in {pattern_ttl}", file=sys.stderr)
            return 1
        shacl_body = shacl_shell(pattern_ttl, shacl_ttl, shacl_iri, pattern_iri)
        (DOCS / shacl_ttl).write_text(shacl_body, encoding="utf-8")
        print(f"Wrote {pattern_ttl}, {shacl_ttl}")

    write_master_ttl()
    print(f"Wrote {MASTER_TTL}")
    write_catalog()
    print("Wrote catalog-v001.xml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
