# Standard Operating Procedure for Scientific Computing Software Development

## 1. Purpose

This document defines a standardized lifecycle for scientific computing software, covering project initiation, requirements engineering, algorithm design, software implementation, verification and validation, performance evaluation, release and delivery, maintenance, and retirement.

This SOP applies to software projects such as:

* Numerical simulation software;
* Scientific computing libraries;
* High-performance computing software;
* Quantum computing and quantum simulation software;
* Engineering computation software;
* Experimental control and data-processing software;
* CPU, GPU, and distributed computing backends;
* Research software intended for academic or industrial use.

The primary objectives of this SOP are to:

1. Prevent scientific software development from relying solely on individual experience and ad hoc decisions;
2. Integrate scientific correctness, numerical reliability, and software engineering quality into one lifecycle;
3. Establish a software engineering process that is verifiable, reproducible, releasable, and maintainable;
4. Define the inputs, activities, outputs, and exit criteria for each lifecycle stage;
5. Provide evidence for code review, release decisions, project retrospectives, and technical audits.

---

## 2. Fundamental Principles

Scientific computing software development shall follow the principles below.

### 2.1 Scientific correctness takes priority

The software shall correctly implement the intended mathematical models, physical models, and numerical algorithms.

A program that runs successfully is not necessarily scientifically correct. Passing conventional software tests does not, by itself, prove that the scientific conclusions are valid.

---

### 2.2 Requirements shall be verifiable

Every critical requirement shall have an explicit acceptance criterion.

The following expressions shall not be used as formal requirements without quantification:

* Supports large-scale computation;
* Provides high performance;
* Offers good scalability;
* Produces sufficiently accurate results;
* Delivers a good user experience.

These statements shall instead be rewritten into measurable forms, for example:

* The software shall support at least (N) computational entities on the specified hardware platform;
* The error relative to the reference solution shall not exceed (\epsilon);
* Peak memory consumption shall not exceed (M);
* When the problem size increases by a factor of (k), execution time shall remain within the specified growth range;
* Installation shall pass automated validation on all supported operating systems.

---

### 2.3 Testing, verification, numerical verification, and validation are distinct activities

Scientific computing software shall distinguish among the following activities:

* **Testing**: Determines whether the program behaves as expected under specified conditions;
* **Software verification**: Determines whether the software correctly implements its specifications and design;
* **Numerical verification**: Determines whether discretization error, iterative error, and floating-point error are controlled;
* **Scientific validation**: Determines whether the mathematical or physical model adequately represents the target problem.

---

### 2.4 Benchmarking shall span the entire lifecycle

Benchmarking shall not be postponed until release preparation.

Benchmarks should be introduced during:

* Technology selection;
* Algorithm prototyping;
* MVP development;
* Release candidate evaluation;
* Formal release;
* Subsequent upgrades.

Benchmarking should cover:

* Correctness;
* Performance;
* Memory consumption;
* Scalability;
* Stability;
* Performance regression.

---

### 2.5 Documentation and code shall evolve together

Documentation is part of the software system, not an afterthought.

The following documents shall be maintained alongside the source code:

* Requirements documentation;
* Architecture documentation;
* Numerical method specifications;
* API documentation;
* User documentation;
* Benchmark documentation;
* Release notes;
* Architecture decision records;
* Known limitations.

---

### 2.6 Development environments and computational results shall be reproducible

The software shall be able to record and reproduce:

* Source code version;
* Dependency versions;
* Compiler and runtime versions;
* Operating system;
* CPU, GPU, and driver information;
* Input parameters;
* Random seeds;
* Execution commands;
* Output files;
* Benchmark environment.

---

### 2.7 Automation shall be preferred

Quality-control activities that can be automated should not depend permanently on manual execution.

Automation should cover:

* Code formatting;
* Static analysis;
* Unit testing;
* Integration testing;
* Documentation builds;
* Installation testing;
* Benchmarking;
* Security scanning;
* Packaging;
* Release publication.

---

## 3. Lifecycle Overview

The standardized scientific computing software lifecycle consists of the following stages:

```text
Stage 0: Project Definition and Feasibility Analysis
    ↓
Stage 1: Requirements Engineering and Acceptance Design
    ↓
Stage 2: Mathematical Model, Numerical Method, and Software Architecture Design
    ↓
Stage 3: Engineering Baseline and Repository Setup
    ↓
Stage 4: Vertical Prototype and MVP Implementation
    ↓
Stage 5: Verification, Validation, and Benchmarking
    ↓
Stage 6: Productization and Release Preparation
    ↓
Stage 7: Release, Deployment, and Operational Acceptance
    ↓
Stage 8: Operations, Maintenance, and Continuous Evolution
    ↓
Stage 9: Retirement and Long-Term Archival
```

These stages shall not be interpreted as a strict waterfall process.

The project should repeatedly execute the following iterative loop:

```text
Requirements
    ↓
Design
    ↓
Implementation
    ↓
Testing and Verification
    ↓
Benchmarking
    ↓
Review
    ↓
Feedback and Correction
    └────────→ Next Iteration
```

---

# 4. Stage 0: Project Definition and Feasibility Analysis

## 4.1 Objective

Define why the project exists, what problem it addresses, who its users are, and whether the project is scientifically, technically, and operationally feasible.

---

## 4.2 Inputs

* Research requirements;
* Product requirements;
* Experimental requirements;
* Industry requirements;
* Existing software and algorithms;
* Initial technical concepts;
* Target deployment environments.

---

## 4.3 Main Activities

### 4.3.1 Define the problem

Specify:

* The scientific or engineering problem to be solved;
* The background of the problem;
* Limitations of current solutions;
* Expected value of the proposed software;
* Capabilities expected after successful completion.

---

### 4.3.2 Identify target users

Identify primary users, such as:

* Algorithm researchers;
* Physicists;
* Engineers;
* Software developers;
* Experimental operators;
* HPC users;
* Third-party integrators.

Different user groups may require different interfaces, documentation, usability levels, and compatibility commitments.

---

### 4.3.3 Define scope and non-goals

The project definition shall include both scope and non-goals.

#### Project scope

Specify the functions, models, platforms, and delivery forms included in the current phase.

#### Non-goals

Explicitly state what the current version will not address, for example:

* Distributed computing is not supported;
* Open-system simulation is not supported;
* Real-time control is not guaranteed;
* No graphical user interface will be provided;
* Windows is not supported;
* Public API stability is not guaranteed.

Non-goals are used to control scope expansion.

---

### 4.3.4 Investigate alternatives

The investigation should include:

* Existing open-source projects;
* Commercial products;
* Research prototypes;
* Standard algorithm libraries;
* Reusable modules;
* Cost differences among internal development, reuse, purchase, and integration.

The project should produce a Build, Buy, Reuse, or Integrate decision.

---

### 4.3.5 Perform risk analysis

Risks should be classified at least as follows:

| Risk category      | Typical question                                       |
| ------------------ | ------------------------------------------------------ |
| Scientific risk    | Is the model suitable for the target problem?          |
| Algorithmic risk   | Will the numerical method converge and remain stable?  |
| Performance risk   | Can the required scale and execution time be achieved? |
| Engineering risk   | Is the technology stack and deployment model feasible? |
| Compatibility risk | Are platforms, drivers, and hardware compatible?       |
| Legal risk         | Do licenses permit the intended use and distribution?  |
| Maintenance risk   | Is the project dependent on a single maintainer?       |
| Project risk       | Are schedule, staffing, and budget sufficient?         |

---

## 4.4 Deliverables

* Project charter;
* Problem statement;
* User and use-case description;
* Project scope;
* Non-goal list;
* Initial risk register;
* Alternative-solution analysis;
* Project success criteria;
* Preliminary delivery model.

---

## 4.5 Exit Criteria

The project may proceed when:

* The project objective is clear;
* Primary users have been identified;
* Scope and non-goals have been documented;
* Critical risks have been registered;
* The project has a clear technical, scientific, or business justification;
* Success criteria are measurable.

---

# 5. Stage 1: Requirements Engineering and Acceptance Design

## 5.1 Objective

Transform project goals into implementable, testable, and traceable software requirements.

---

## 5.2 Requirement Categories

### 5.2.1 Scientific requirements

Scientific requirements should describe:

* Mathematical models;
* Physical assumptions;
* Boundary conditions;
* Initial conditions;
* Applicable parameter ranges;
* Target observables;
* Model limitations.

---

### 5.2.2 Functional requirements

Functional requirements should describe:

* Inputs;
* Outputs;
* Core computational workflows;
* Data loading;
* Result storage;
* Configuration management;
* APIs;
* Command-line interfaces;
* Visualization;
* Error handling.

---

### 5.2.3 Non-functional requirements

Non-functional requirements should include:

* Numerical accuracy;
* Runtime performance;
* Memory limits;
* Scalability;
* Stability;
* Portability;
* Maintainability;
* Security;
* Reproducibility;
* Observability.

---

### 5.2.4 Interface requirements

Specify:

* Python APIs;
* Julia APIs;
* C or C++ ABIs;
* REST APIs;
* File formats;
* Data schemas;
* Frontend-backend communication protocols;
* Third-party integration interfaces.

---

### 5.2.5 Deployment requirements

Specify:

* Operating systems;
* CPU architectures;
* GPU models;
* CUDA or other runtimes;
* Container environments;
* HPC schedulers;
* Network requirements;
* Storage requirements.

---

## 5.3 Requirement Format

Each formal requirement should contain:

```text
Requirement ID
Requirement Name
Requirement Description
Requirement Source
Priority
Acceptance Method
Associated Tests
Associated Risks
Target Version
Status
```

Example:

```text
Requirement ID:
PERF-001

Requirement Name:
Single-Node GPU Solver Performance

Requirement Description:
On an NVIDIA H100 GPU with CUDA 12.x,
the reference workload shall complete within 60 seconds.

Acceptance Method:
Execute benchmark/gpu/reference_case ten times
and use the median execution time.

Target Version:
v1.0
```

---

## 5.4 Requirement Prioritization

The following classification may be used:

* **Must**: Required for the target release;
* **Should**: Important but not release-blocking;
* **Could**: Implemented when resources permit;
* **Won't**: Explicitly excluded from the current release.

---

## 5.5 Requirements Traceability

The project should maintain the following mapping:

```text
Requirement
    ↓
Design Component
    ↓
Implementation Module
    ↓
Test Case
    ↓
Acceptance Result
```

Example traceability matrix:

| Requirement ID | Design document | Implementation module | Test case     | Acceptance status |
| -------------- | --------------- | --------------------- | ------------- | ----------------- |
| SCI-001        | NUM-001         | solver/core           | test_exact.py | Passed            |
| PERF-001       | ARCH-003        | backend/gpu           | bench_gpu.py  | Pending           |

---

## 5.6 Deliverables

* Software Requirements Specification;
* Use cases;
* Interface requirements;
* Deployment requirements;
* Acceptance criteria;
* Requirements Traceability Matrix;
* Version requirement list.

---

## 5.7 Exit Criteria

The stage is complete when:

* Core requirements have identifiers;
* Each critical requirement has an acceptance method;
* Non-functional requirements have been quantified;
* Scientific applicability has been defined;
* Requirements are associated with target versions.

---

# 6. Stage 2: Mathematical Model, Numerical Method, and Software Architecture Design

## 6.1 Objective

Define the mathematical model, numerical method, module structure, and major technical decisions before full-scale implementation.

---

## 6.2 Mathematical Model Design

The project shall document:

* Governing equations;
* State space;
* Parameter definitions;
* Unit system;
* Initial conditions;
* Boundary conditions;
* Conserved quantities;
* Symmetries;
* Model assumptions;
* Applicability;
* Known limitations.

---

## 6.3 Numerical Method Design

The project shall document:

* Discretization methods;
* Time-integration methods;
* Spatial discretization methods;
* Linear or nonlinear solvers;
* Error-estimation methods;
* Convergence criteria;
* Stability conditions;
* Preconditioning strategies;
* Stochastic algorithms;
* Numerical precision;
* Parallelization strategy;
* Computational complexity estimates.

---

## 6.4 Software Architecture Design

The architecture shall define:

* Module boundaries;
* Data flow;
* Control flow;
* Core objects;
* API layer;
* Computational backend;
* Scheduling layer;
* Data management;
* Logging and diagnostics;
* Plugin and extension mechanisms;
* Error handling;
* Deployment structure.

---

## 6.5 Technology Stack Selection

Technology selection shall be based on project constraints rather than personal familiarity alone.

Evaluation criteria should include:

| Dimension            | Typical question                                              |
| -------------------- | ------------------------------------------------------------- |
| Scientific ecosystem | Are mature numerical libraries available?                     |
| Performance          | Can CPU, GPU, or distributed performance requirements be met? |
| Interoperability     | Can the system integrate with other languages and tools?      |
| Deployment           | Can the software be packaged and installed reliably?          |
| Maintainability      | Can the team maintain the stack over time?                    |
| Licensing            | Are licensing conditions compatible with the project?         |
| Community            | Are critical dependencies actively maintained?                |
| Stability            | Are APIs and toolchains sufficiently mature?                  |

---

## 6.6 Architecture Decision Records

Important technical decisions shall be recorded using Architecture Decision Records.

Each ADR should contain:

```text
Title
Status
Context
Decision
Alternatives
Rationale
Trade-offs
Consequences
Date
```

Typical ADR topics include:

* Python as the user-facing interface;
* Julia as the numerical backend;
* HDF5 as the result format;
* GitHub Flow as the branching model;
* Containers as the standard runtime environment;
* Semantic Versioning;
* Selection of an open-source license.

---

## 6.7 Technical Prototypes

High-risk technical assumptions shall be evaluated through minimal prototypes, such as:

* Python-Julia interoperability;
* GPU backend feasibility;
* Large-scale memory consumption;
* Parallel scalability;
* Driver compatibility inside containers;
* File-format performance;
* Convergence of the core numerical algorithm.

The purpose of a technical prototype is to validate assumptions, not to deliver production functionality.

---

## 6.8 Deliverables

* Mathematical model specification;
* Numerical method specification;
* Software architecture document;
* Initial API specification;
* Data schema;
* Architecture Decision Records;
* Technical prototype report;
* Initial performance baseline.

---

## 6.9 Exit Criteria

The stage is complete when:

* The mathematical model is defined;
* Numerical methods are specified;
* Major error sources are identified;
* Module boundaries are clear;
* High-risk assumptions have been prototyped;
* Core interfaces have an initial design.

---

# 7. Stage 3: Engineering Baseline and Repository Setup

## 7.1 Objective

Establish the engineering foundation required for sustainable development, automated testing, automated builds, and reproducible deployment.

---

## 7.2 Recommended Repository Structure

```text
project/
├── src/                  # Core source code
├── tests/                # Automated tests
│   ├── unit/
│   ├── integration/
│   ├── numerical/
│   └── regression/
├── benchmarks/           # Benchmark suite
├── examples/             # Usage examples
├── docs/                 # Documentation
│   ├── requirements/
│   ├── architecture/
│   ├── numerical/
│   ├── api/
│   └── decisions/
├── scripts/              # Build and utility scripts
├── configs/              # Configuration templates
├── containers/           # Docker and development containers
├── data/                 # Small test datasets
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── CHANGELOG.md
├── CITATION.cff
└── pyproject.toml / Project.toml / CMakeLists.txt
```

The exact structure may be adapted to project size and language ecosystem.

---

## 7.3 Git Workflow

For individual or small-team projects, a simplified GitHub Flow is usually appropriate:

```text
main
  ├── feature/*
  ├── fix/*
  ├── docs/*
  └── release/*
```

Recommended rules:

* `main` shall remain buildable and testable;
* Features shall be developed on separate branches;
* All merges shall use Pull Requests;
* Pull Requests shall pass CI before merging;
* Direct development on `main` shall be prohibited;
* Releases shall use immutable Git tags;
* Major changes shall reference an Issue or design record.

---

## 7.4 Development Environment

The project shall provide at least one standardized development environment:

* Locked local environment;
* Docker;
* Development Container;
* Conda;
* Nix;
* HPC environment modules.

The environment documentation shall define:

* Language versions;
* Compiler versions;
* System dependencies;
* GPU dependencies;
* Package managers;
* Installation steps;
* Test commands;
* Documentation build commands.

---

## 7.5 Dependency Management

Dependencies shall be managed according to the following rules:

* Declare explicit version constraints;
* Use lock files where supported;
* Avoid undocumented system dependencies;
* Upgrade dependencies periodically;
* Scan for known vulnerabilities;
* Record dependency licenses;
* Avoid unnecessary large dependencies;
* Prepare alternatives for critical dependencies.

---

## 7.6 CI Baseline

Each Pull Request should execute at least:

```text
Code formatting checks
Static analysis
Unit tests
Integration tests
Documentation builds
Installation tests
Multi-version compatibility tests
```

Depending on project requirements, CI may also include:

```text
CPU tests
GPU tests
Numerical regression tests
Performance regression tests
Container builds
Dependency vulnerability scans
License scans
```

---

## 7.7 Version Management

Semantic Versioning is recommended:

```text
MAJOR.MINOR.PATCH
```

* `MAJOR`: Incompatible API changes;
* `MINOR`: Backward-compatible features;
* `PATCH`: Backward-compatible bug fixes.

Pre-release examples:

```text
0.1.0-alpha.1
0.1.0-beta.1
1.0.0-rc.1
```

---

## 7.8 Deliverables

* Standardized repository;
* Reproducible development environment;
* Locked dependencies;
* CI pipeline;
* Test framework;
* Documentation framework;
* Packaging system;
* Versioning policy;
* Contribution guidelines;
* Security policy.

---

## 7.9 Exit Criteria

The engineering baseline is complete when:

* A new environment can install the project from documentation;
* Minimal source code can be built;
* Tests can run automatically;
* Documentation can be generated automatically;
* Pull Requests are protected by quality gates;
* Dependency and version policies are defined.

---

# 8. Stage 4: Vertical Prototype and MVP Implementation

## 8.1 Objective

Implement a minimal end-to-end workflow covering input, computation, and output.

The MVP should be a vertical slice of the system rather than a collection of isolated modules.

---

## 8.2 MVP Scope

The MVP should:

* Cover one core user scenario;
* Use real data structures;
* Invoke the actual core algorithm;
* Produce verifiable results;
* Include minimal error handling;
* Provide minimal documentation and examples;
* Run in the standardized environment.

---

## 8.3 Development Requirements

Each feature should include:

* Implementation code;
* Unit tests;
* Required integration tests;
* Documentation;
* Examples;
* Change description.

The project should avoid accumulating long-term debt under a “implement first, test and document later” approach.

---

## 8.4 Code Review Requirements

Code review should examine:

* Requirement compliance;
* Algorithm correctness;
* Boundary conditions;
* Error handling;
* Test adequacy;
* API consistency;
* Dependency impact;
* Performance impact;
* Documentation updates;
* Compatibility impact.

Individual projects should still use Pull Requests for self-review and traceability.

---

## 8.5 MVP User Review

At least one representative user should execute a realistic workflow.

The review should evaluate:

* Interface usability;
* Parameter clarity;
* Error-message quality;
* Result usefulness;
* Documentation adequacy;
* Architectural blockers.

---

## 8.6 Deliverables

* Runnable MVP;
* Core tests;
* Example programs;
* Minimal user documentation;
* MVP review record;
* Known issues;
* Requirements for the next phase.

---

## 8.7 Exit Criteria

The stage is complete when:

* The core workflow runs end to end;
* Critical results have initial validation evidence;
* A non-developer can run the MVP using the documentation;
* No issue requires immediate replacement of the overall architecture;
* Known limitations are documented.

---

# 9. Stage 5: Verification, Validation, and Benchmarking

## 9.1 Objective

Establish systematic evidence for software correctness, numerical reliability, scientific validity, and performance.

---

## 9.2 Software Testing Framework

### 9.2.1 Unit testing

Unit tests should cover:

* Mathematical functions;
* Data transformations;
* Parameter validation;
* Boundary conditions;
* Exception handling;
* Utility functions.

---

### 9.2.2 Integration testing

Integration tests should cover interactions among:

* Frontend and backend;
* Solvers and data models;
* CPU and GPU implementations;
* File I/O components;
* External libraries;
* Containerized environments.

---

### 9.2.3 System testing

System tests should cover complete workflows:

```text
Input
    ↓
Model Construction
    ↓
Solver Execution
    ↓
Result Storage
    ↓
Result Loading
    ↓
Analysis
```

---

### 9.2.4 Regression testing

Regression tests prevent corrected defects from reappearing.

Every significant defect correction should introduce a corresponding regression test.

---

## 9.3 Software Verification

Software verification answers:

> Does the software correctly implement the specified design and requirements?

Verification methods include:

* Requirement-to-test mapping;
* Code review;
* Interface consistency checks;
* Test coverage analysis;
* Static analysis;
* Boundary testing;
* Exception-path testing;
* Cross-platform testing.

---

## 9.4 Numerical Verification

Numerical verification should include the following activities.

### 9.4.1 Analytical-solution comparison

For problems with analytical solutions, numerical results shall be compared against them.

---

### 9.4.2 Convergence testing

The project should test:

* Time-step convergence;
* Grid convergence;
* Truncation-order convergence;
* Iterative residual convergence;
* Sample-size convergence.

---

### 9.4.3 Stability testing

The project should test:

* Long-time integration stability;
* Extreme parameter values;
* Stiff systems;
* Ill-conditioned systems;
* Sensitivity to numerical precision;
* Sensitivity to parallel execution.

---

### 9.4.4 Invariant testing

Depending on the model, tests may include:

* Probability normalization;
* Energy conservation;
* Particle-number conservation;
* Positive definiteness;
* Hermiticity;
* Symmetry preservation;
* Constraint preservation.

---

### 9.4.5 Floating-point sensitivity testing

Tests should compare:

* Float32 and Float64;
* CPU and GPU;
* Different thread counts;
* Different execution orders;
* Different BLAS implementations;
* Different hardware architectures.

Numerical comparison should use justified tolerances rather than requiring bitwise identity by default.

---

## 9.5 Scientific Validation

Scientific validation answers:

> Does the model and numerical implementation adequately represent the target problem?

Validation evidence may include:

* Experimental data;
* Published results;
* Independently validated software;
* Independent implementations;
* Standard reference cases;
* Expert review.

---

## 9.6 Benchmark Categories

### 9.6.1 Correctness benchmarks

Correctness benchmarks should record:

* Test case;
* Reference answer;
* Error tolerance;
* Data source;
* Applicable software version.

---

### 9.6.2 Performance benchmarks

Performance benchmarks should measure:

* Total runtime;
* Core kernel runtime;
* Throughput;
* Latency;
* Compilation time;
* Peak memory usage;
* I/O time;
* CPU and GPU utilization.

---

### 9.6.3 Scalability benchmarks

Scalability benchmarks should evaluate:

* Problem-size scaling;
* Strong scaling;
* Weak scaling;
* Multithreading;
* Multiprocessing;
* Multi-GPU execution;
* Multi-node execution.

---

### 9.6.4 Performance regression benchmarks

Example thresholds:

```text
Runtime regression above 10%: Warning
Runtime regression above 20%: Block merge
Memory regression above 15%: Mandatory review
```

Thresholds shall be based on benchmark variability and hardware stability.

---

## 9.7 Benchmark Recording Requirements

Each formal benchmark run should record:

```text
Software version
Git commit
Execution date
Operating system
CPU
GPU
Memory
Driver version
Compiler
Language runtime
Dependency versions
Input data
Configuration parameters
Thread count
Random seed
Warm-up procedure
Number of repetitions
Statistical method
Raw results
Aggregated results
```

---

## 9.8 Deliverables

* Test report;
* Software verification report;
* Numerical verification report;
* Scientific validation report;
* Benchmark specification;
* Benchmark baseline;
* Error analysis;
* Performance analysis.

---

## 9.9 Exit Criteria

The stage is complete when:

* Core requirements have test coverage;
* Critical reference cases pass;
* Major numerical errors are understood;
* Performance claims are supported by reproducible experiments;
* Critical platforms pass compatibility testing;
* No unresolved correctness issue blocks release.

---

# 10. Stage 6: Productization and Release Preparation

## 10.1 Objective

Convert a validated development version into software that can be installed, delivered, used, and maintained.

---

## 10.2 Release Scope Freeze

Before release, define:

* Included features;
* Deferred features;
* Known limitations;
* Supported platforms;
* API stability level;
* Data format version;
* Dependency constraints;
* Performance envelope.

---

## 10.3 API Stability Review

Review:

* Naming consistency;
* Parameter clarity;
* Default values;
* Return-value stability;
* Exception behavior;
* Duplicate interfaces;
* Temporary or deprecated APIs.

Version `1.0` generally implies a defined public API compatibility commitment, not merely a large feature set.

---

## 10.4 Documentation Completeness

A formal release should provide at least:

* Installation guide;
* Quick Start;
* Tutorials;
* API reference;
* Core concepts;
* Examples;
* Configuration guide;
* Benchmark description;
* Known limitations;
* Troubleshooting guide;
* Contribution guide;
* Citation instructions.

---

## 10.5 Installation and Packaging Tests

Depending on project type, test:

* Python wheels;
* Conda packages;
* Julia packages;
* Docker images;
* Binary distributions;
* HPC modules;
* Source builds.

Installation tests shall run in clean environments to avoid hidden dependencies from developer machines.

---

## 10.6 Software Supply Chain Security

Before release, perform at least:

* Dependency vulnerability scanning;
* License review;
* Secret scanning;
* Build-permission review;
* SBOM generation;
* Artifact verification;
* Release-permission minimization;
* Artifact signing or provenance recording.

---

## 10.7 Release Candidate

Release candidates may use versions such as:

```text
v1.0.0-rc.1
v1.0.0-rc.2
```

During the Release Candidate stage, changes should generally be limited to:

* Bug fixes;
* Documentation fixes;
* Release-engineering fixes;
* Essential compatibility corrections.

Major new functionality should not normally be introduced.

---

## 10.8 Release Quality Gate

Before formal release, verify:

```text
[ ] Core requirements completed
[ ] All release-blocking defects closed
[ ] CI fully passing
[ ] Numerical verification completed
[ ] Benchmarks meet thresholds
[ ] Installation tests pass
[ ] Documentation completed
[ ] License review completed
[ ] Security scans completed
[ ] CHANGELOG updated
[ ] Release Notes completed
[ ] Version number confirmed
[ ] Release artifacts are reproducible
```

---

## 10.9 Deliverables

* Release Candidate;
* Release Notes;
* CHANGELOG;
* Installable packages;
* Container images;
* Documentation site;
* SBOM;
* Security review results;
* User acceptance record;
* Release approval record.

---

## 10.10 Exit Criteria

The stage is complete when:

* The Release Candidate passes all quality gates;
* Users can install and run the software in a clean environment;
* Release artifacts are traceable;
* Documentation matches the software version;
* Critical defects are closed or explicitly documented.

---

# 11. Stage 7: Release, Deployment, and Operational Acceptance

## 11.1 Objective

Deliver the software in a traceable, immutable, and recoverable form.

---

## 11.2 Release Workflow

A standard release workflow is:

```text
Confirm Version
    ↓
Update CHANGELOG
    ↓
Create Git Tag
    ↓
Build Artifacts in CI
    ↓
Run Release Tests
    ↓
Generate Signatures, Checksums, and SBOM
    ↓
Publish Packages and Images
    ↓
Publish Documentation
    ↓
Create Archival Record
    ↓
Publish Release Announcement
```

---

## 11.3 Release Artifacts

Depending on project type, release:

* Source archives;
* Software packages;
* Binary files;
* Container images;
* Documentation;
* Examples;
* Benchmark datasets;
* Checksums;
* SBOM;
* Signatures;
* Citation metadata.

---

## 11.4 Deployment Acceptance

For services or experimental systems, verify:

* Deployment environment;
* Networking;
* Storage;
* GPU and driver configuration;
* Environment variables;
* Permissions;
* Logging;
* Monitoring;
* Backup;
* Rollback.

---

## 11.5 Smoke Testing

After deployment, execute a minimal operational test:

* The software starts successfully;
* Core APIs are callable;
* A reference case completes;
* Outputs can be read;
* Logging functions correctly;
* No abnormal performance degradation is observed.

---

## 11.6 Version Archival and Citation

Formal research software releases should:

* Use immutable Git tags;
* Create a GitHub Release;
* Archive the version on a long-term preservation platform;
* Obtain a DOI where appropriate;
* Provide `CITATION.cff`;
* Record related papers or technical reports.

---

## 11.7 Deliverables

* Formal release;
* Release artifacts;
* Deployment record;
* Operational acceptance report;
* Release announcement;
* Citable archive;
* Known-issues list.

---

## 11.8 Exit Criteria

The stage is complete when:

* Artifacts are published successfully;
* Installation and deployment tests pass;
* Critical users can operate the software;
* The version is traceable;
* Rollback procedures are valid;
* Release records are complete.

---

# 12. Stage 8: Operations, Maintenance, and Continuous Evolution

## 12.1 Objective

Maintain correctness, compatibility, security, and maintainability during the operational lifetime of the software.

---

## 12.2 Defect Management

Defects may be classified as:

| Severity | Meaning                                                                |
| -------- | ---------------------------------------------------------------------- |
| Critical | Incorrect scientific results, security compromise, or complete failure |
| High     | Core functionality severely impaired                                   |
| Medium   | Functional issue with a viable workaround                              |
| Low      | Minor defect or usability issue                                        |

A defect report should include:

* Reproduction steps;
* Environment;
* Input;
* Expected result;
* Actual result;
* Logs;
* Severity;
* Target fix version;
* Regression test.

---

## 12.3 Performance Monitoring

Continuously monitor:

* Benchmark trends;
* Memory trends;
* Startup time;
* Compilation time;
* GPU performance;
* Dependency-version impact;
* Hardware-specific behavior.

---

## 12.4 Dependency Upgrades

Dependency upgrades should follow:

```text
Compatibility Assessment
    ↓
Upgrade on Separate Branch
    ↓
Full CI
    ↓
Numerical Regression Testing
    ↓
Benchmarking
    ↓
Merge
```

Core numerical dependencies shall not be upgraded in bulk without validation.

---

## 12.5 API Compatibility Policy

A recommended API deprecation process is:

```text
Version N:
Mark as deprecated and provide replacement

Version N+1:
Retain interface and emit warnings

Later major version:
Remove deprecated interface
```

Breaking changes shall include a migration guide.

---

## 12.6 Technical Debt Management

Technical debt shall be explicitly recorded, including:

* Temporary implementations;
* Missing tests;
* Performance bottlenecks;
* Excessive coupling;
* Obsolete dependencies;
* Missing documentation;
* Architectural deviations;
* Manual release steps.

Technical debt shall not remain only in developers' memory.

---

## 12.7 Roadmap Management

The roadmap should be based on:

* User demand;
* Scientific value;
* Technical risk;
* Maintenance cost;
* Product or project priority;
* Current architectural capability.

Roadmap items should be marked as:

* Confirmed;
* Planned;
* Under exploration;
* Not currently planned.

A roadmap is not necessarily a firm delivery-date commitment.

---

## 12.8 Deliverables

* Defect records;
* Maintenance releases;
* Performance trends;
* Security updates;
* Dependency-upgrade records;
* Technical debt register;
* Roadmap;
* API migration guidance.

---

# 13. Stage 9: Retirement and Long-Term Archival

## 13.1 Objective

When maintenance ends, ensure that users can migrate and that essential scientific and engineering records are preserved.

---

## 13.2 Retirement Conditions

Retirement may be triggered when:

* Project objectives have been completed;
* A superior replacement exists;
* Critical dependencies are no longer maintained;
* The architecture cannot evolve further;
* Maintenance resources are unavailable;
* Security or compliance risks cannot be resolved;
* The project is merged into a successor system.

---

## 13.3 Retirement Process

```text
Define Retirement Plan
    ↓
Publish End-of-Maintenance Notice
    ↓
Provide Migration Path
    ↓
Resolve Final Critical Issues
    ↓
Publish Final Release
    ↓
Freeze Repository
    ↓
Archive Source, Documentation, and Artifacts
    ↓
Identify Replacement Project
```

---

## 13.4 Long-Term Preservation Content

At minimum, preserve:

* Final source code;
* Git history;
* Release artifacts;
* Documentation;
* Benchmarks;
* Reference datasets;
* Dependency information;
* Build instructions;
* License;
* Citation information;
* Migration guide.

---

## 13.5 Deliverables

* Retirement notice;
* Final release;
* Migration guide;
* Archived repository;
* Long-term preservation record;
* Replacement-project reference.

---

# 14. Continuous Quality Gates

Projects should establish continuous quality gates.

## 14.1 Pull Request Gate

```text
[ ] Requirement or Issue linked
[ ] Formatting checks pass
[ ] Static analysis passes
[ ] Unit tests pass
[ ] Integration tests pass
[ ] Numerical tests pass
[ ] Documentation updated
[ ] No unexplained performance regression
[ ] No unreviewed dependency introduced
[ ] Review completed
```

---

## 14.2 Release Gate

```text
[ ] Release scope frozen
[ ] All release-blocking defects closed
[ ] Requirement acceptance completed
[ ] Verification completed
[ ] Validation completed
[ ] Benchmarks meet requirements
[ ] Multi-platform tests pass
[ ] Installation tests pass
[ ] Documentation complete
[ ] Security review complete
[ ] SBOM generated
[ ] Version and CHANGELOG consistent
[ ] Rollback plan validated
```

---

# 15. Documentation System

A scientific computing project should maintain at least the following documentation:

| Document            | Main content                                   |
| ------------------- | ---------------------------------------------- |
| README              | Project positioning and entry point            |
| Project Charter     | Goals, scope, and success criteria             |
| Requirements        | Requirements and acceptance criteria           |
| Architecture        | Software architecture and module relationships |
| Numerical Methods   | Mathematical models and numerical methods      |
| ADR                 | Major technical decisions                      |
| API Reference       | Interface definitions                          |
| User Guide          | User workflows                                 |
| Developer Guide     | Development and build instructions             |
| Verification Report | Software and numerical verification            |
| Validation Report   | Scientific validation                          |
| Benchmark Report    | Performance and scalability                    |
| CONTRIBUTING        | Contribution process                           |
| SECURITY            | Security reporting process                     |
| CHANGELOG           | Version history                                |
| Release Notes       | Release-specific changes                       |
| CITATION            | Software citation instructions                 |

---

# 16. Recommended Metrics

## 16.1 Quality Metrics

* Automated test pass rate;
* Number of regression defects;
* Number of unresolved severe defects;
* Critical requirement coverage;
* Numerical verification coverage;
* Documentation build success rate.

---

## 16.2 Performance Metrics

* Runtime;
* Peak memory usage;
* Throughput;
* Latency;
* CPU and GPU utilization;
* Strong-scaling efficiency;
* Weak-scaling efficiency.

---

## 16.3 Maintainability Metrics

* Build success rate;
* Dependency-upgrade frequency;
* Number of technical debt items;
* Mean time to resolve defects;
* Number of breaking API changes;
* Number of manual release steps.

Metrics should be used for trend and risk analysis rather than as isolated performance targets.

---

# 17. Minimum Baseline for Individual Projects

Individual or early-stage scientific software projects do not need to adopt full enterprise-level process immediately.

The minimum recommended baseline is:

```text
1. Project goals, scope, and non-goals
2. Requirements and acceptance criteria
3. Architecture and numerical method documentation
4. Git branches and Pull Requests
5. Automated formatting and static analysis
6. Unit, integration, and numerical tests
7. At least one correctness benchmark
8. At least one performance benchmark
9. Reproducible development environment
10. Locked dependencies
11. CI-based build and test automation
12. README, LICENSE, CHANGELOG, and CITATION
13. Release Candidate quality gate
14. Automated release workflow
15. Runtime environment and parameter recording
```

Individual projects may simplify approvals and role assignments, but should not omit essential evidence and automated quality control.

---

# 18. Recommended Roles and Responsibilities

For medium or large projects, the following responsibilities may be defined:

| Role                           | Main responsibility                                |
| ------------------------------ | -------------------------------------------------- |
| Project Lead                   | Scope, priorities, and resources                   |
| Scientific Lead                | Model validity and scientific correctness          |
| Numerical Methods Lead         | Numerical methods, stability, and error control    |
| Software Architect             | System architecture and interfaces                 |
| Developer                      | Implementation and testing                         |
| V&V Lead                       | Verification and validation                        |
| Release Manager                | Versioning and release management                  |
| DevOps, MLOps, or HPC Engineer | Build, deployment, and runtime infrastructure      |
| Security Lead                  | Dependencies, artifacts, and supply chain security |

In small projects, one person may hold multiple roles. However, reviews should explicitly distinguish among the roles being exercised so that implementation judgment is not automatically treated as independent validation.

---

# 19. SOP Tailoring Principles

The SOP should be tailored according to project risk.

## 19.1 Low-risk research prototype

The following may be simplified:

* Formal requirements specification;
* Independent security review;
* Multi-platform support;
* Full release engineering.

The following should still be retained:

* Numerical verification;
* Environment recording;
* Source versioning;
* Minimal testing;
* Model and algorithm documentation.

---

## 19.2 Public open-source software

The following should be strengthened:

* Licensing;
* Documentation;
* API stability;
* Installation testing;
* Contribution workflow;
* Security policy;
* Version management;
* Citability.

---

## 19.3 Production or experimental-control software

The following should be strengthened:

* Risk analysis;
* Requirements traceability;
* System testing;
* Error recovery;
* Security;
* Monitoring;
* Rollback;
* Operational acceptance;
* Audit records.

---

## 19.4 High-performance computing software

The following should be strengthened:

* Correctness benchmarking;
* Performance benchmarking;
* Strong and weak scaling;
* Hardware compatibility;
* Compiler compatibility;
* Numerical consistency;
* Performance regression testing.

---

# 20. References and Standards

1. NASA, *NASA Software Engineering Requirements*, NPR 7150.2.
2. NASA, *Systems Engineering Handbook*.
3. NIST SP 800-218, *Secure Software Development Framework, Version 1.1*.
4. ISO/IEC/IEEE 12207, *Systems and Software Engineering — Software Life Cycle Processes*.
5. ISO/IEC/IEEE 29148, *Requirements Engineering*.
6. ISO/IEC 25010, *Systems and Software Quality Models*.
7. Barker, M. et al., “Introducing the FAIR Principles for Research Software,” *Scientific Data*, 2022.
8. FAIR for Research Software Working Group, *FAIR4RS Principles*.
9. Software Sustainability Institute, *Software Development Best Practice*.
10. Journal of Open Source Software, *Review Criteria*.
11. GitHub Documentation, *Artifact Attestations and Software Supply Chain Security*.
12. Semantic Versioning Specification.
13. Smith, A. M. et al., “Software Citation Principles,” *PeerJ Computer Science*, 2016.
14. Wilson, G. et al., “Best Practices for Scientific Computing,” *PLoS Biology*, 2014.

---

# 21. Conclusion

A standardized scientific computing software process is not primarily about mechanically dividing a project into sequential stages.

Its purpose is to establish a continuous quality system that covers:

* Scientific problem definition;
* Requirements and acceptance;
* Mathematical modeling;
* Numerical methods;
* Software architecture;
* Engineering automation;
* Software testing;
* Numerical verification;
* Scientific validation;
* Benchmarking;
* Reproducibility;
* Software supply chain security;
* Release and deployment;
* Operations and maintenance;
* Retirement.

The quality of scientific computing software shall not be judged only by code size, feature count, or test coverage.

The central criterion is:

> Whether the software produces trustworthy scientific or engineering results, within a clearly defined applicability range, in a reproducible, verifiable, and maintainable manner.
