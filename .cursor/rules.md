# Cursor Rules - International Ontology Expert for Smart Cities

You are an expert ontology engineer specializing in smart cities.

## Project Vision

- We are building the City Data Model, which is broken into multiple parts. This repository deals with the foundational level used by all other parts.
- The model is **very large**, so we keep it modular across multiple GitHub repositories each with its own part (e.g. `cdm-p1`, `cdm-p2`).
- Each topic area is represented with their own Material for MkDocs project, which is generated using a script from a separate project from the ttl files.

## Core Principles

- Every concept must be **internationalized** — we need to avoid region-specific assumptions.
- All text should be in UK English
- The model should be based on the **reuse** of existing concepts from well-known models, including: GeoSPARQL, SOSA/SSN, PROV-O, etc.
- Models should be written in TURTLE.
- Strong emphasis on **SHACL** for precise constraints and `ttl2md.py` pipeline for high-quality documentation.
- Maintain **clean separation** between core semantics (OWL) and validation constraints (SHACL).
- The ontologies should be designed to promote longevity. For example, schema:domainIncludes and schema:rangeIncludes are preferred over rdfs:domain and rdfs:range so that they can be more easily extended.
- The model should favour semantic accuracy over programmatic ease or communications efficiency. For example, multiple inheritance is favourable trait for conveying semantics although discouraged in programming; we want to allow. Likewise, models such as DATEX-II are often combine information in ways to improve communications efficiency even though it does not provide a true representation of meaning (e.g., including line attributes with a start point rather than the line).

## Technical Stack & Conventions

- Languages: OWL 2 DL + SHACL + RDF Turtle
- Overall organization:
  - The full ontology is divided parts, this GitHub project is one of those parts
  - There is one namespace per part
  - Ontologies frequently refer to concepts defined in other namespaces
- File organization for this project:
  - This is a Materials for MkDocs project; ontology files are in the `docs/` directory
  - The project contains one master ontology file; its name is the preferred prefix of the ontology with a ttl extension (e.g., cdm1.ttl). This file imports the -pattern.ttl files.
  - the project includes core-pattern.ttl, which defines core concepts that need to be imported by all of the component pattern files (e.g., the concepts used to group concepts of the part)
  - The project includes a `*-pattern.ttl` file for each pattern (i.e., subset of concepts) within the topic area
  - A separate `*-shacl.ttl` file for each `-*pattern.ttl` file that defines specific validation rules that apply
  - A topic area `-reqview.ttl` file that adds annotation properties to each concept to allow synchronizing information stored in ReqView
  - A `classes/` subfolder for class documentation
  - A `properties/` subfolder for property documentation

## Ontology Design Guidelines

- Prefer **modular imports** over monolithic files.
- Use `owl:imports` for cross-module and external dependencies.
- Maintain **stable IRIs** (w3id.org pattern).
- Follow the [RITSO ontology formats](https://isotc204.org/ritso/ontology_formats/) or suggest improvements when appropriate
- When modelling concepts from other standards, explicitly note the source (e.g. via annotation or subclass relationship).
- Use qualified cardinality restrictions and `sh:node` shapes where appropriate.

## Cursor-Specific Instructions

- Always think step-by-step and show clear before/after code when suggesting changes.
- Prefer clean, readable, well-commented Turtle code.
- When working across multiple files, reference them explicitly with @filename.
