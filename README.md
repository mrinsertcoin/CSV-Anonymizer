# CSV Anonymizer MVP

A small on-premise CSV anonymization tool. It supports profile-based pseudonymization, masking, column removal, simple generalization and audit logging.

## Project goal

The project turns manual CSV anonymization into a repeatable, auditable workflow:

- automated processing of sensitive CSV files
- fully on-premise; no cloud processing and no telemetry
- deterministic pseudonymization with local key material
- masking and profile-based rules for business departments
- audit trail for traceability and CI/batch integration

This is intentionally scoped to CSV files and pragmatic anonymization operations. Complex algorithms such as k-anonymity or differential privacy are out of scope for this MVP.

## Core concepts

### Pseudonymization

The tool uses **HMAC-SHA256** for deterministic pseudonymization. Same input + same key produces the same pseudonym. The original value is not recoverable from the pseudonym.

This is not encryption and not full legal anonymization. It is pseudonymization and masking for controlled business workflows.

### Profiles

Profiles are YAML files that define how columns should be handled:

- `pseudonymize`
- `mask`
- `drop`
- `keep`
- `generalize`

Profiles are versionable and business-specific, e.g. `crm-basic-1.0.0.yaml`.

### Audit

Each run writes a JSONL audit entry with metadata such as:

- input/output file checksums
- profile id/version/hash
- key version
- row counts
- operations applied
- exit code and duration

The audit log does **not** store plaintext data.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -e .[dev]
```

## Run tests

```bash
pytest -q
```

## CLI usage

```bash
anonymize run \
  --input examples/customers_raw.csv \
  --output out/customers_anonymized.csv \
  --profile profiles/crm-basic-1.0.0.yaml \
  --keyfile keys/key-v1.example.json \
  --audit audit/audit-log.jsonl
```

Output:

- anonymized CSV: `out/customers_anonymized.csv`
- audit log: `audit/audit-log.jsonl`

## GUI usage

A minimal Tkinter GUI is included:

```bash
python -m anonymizer.gui
```

The GUI lets users select an input CSV, output path, profile, keyfile and audit path.

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | OK |
| 2 | Profile invalid |
| 3 | I/O error |
| 4 | Key error |
| 5 | Transformation error |
| 6 | Audit error |

## Docker deployment idea

The application can be delivered as a Docker container for customer environments. The container would run locally or inside the customer network, mounting data, profiles, keys and audit logs as volumes.

Example concept:

```bash
docker run --rm \
  -v ./examples:/data \
  -v ./profiles:/profiles \
  -v ./keys:/keys \
  -v ./audit:/audit \
  csv-anonymizer \
  anonymize run \
  --input /data/customers_raw.csv \
  --output /data/customers_anonymized.csv \
  --profile /profiles/crm-basic-1.0.0.yaml \
  --keyfile /keys/key-v1.example.json \
  --audit /audit/audit-log.jsonl
```

Docker is only a packaging and deployment option. Data processing remains on-premise.

## Security notes

- Do not commit real key files.
- Do not process real customer data in public demos.
- Keep audit logs free of plaintext personal data.
- Pseudonymized data may still count as personal data under GDPR if re-identification is possible with additional information.

## License

MIT License. See `LICENSE`.
