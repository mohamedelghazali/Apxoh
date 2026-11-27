# API Service Example

A minimal Go HTTP API governed by GENCODE-GOV.

Demonstrates:
- Health endpoint (required by `SE-OBS-001`)
- Handler with tests
- GENCODE-GOV profile: `api-service`
- Security gate remains blocked when required TSAR evidence is unavailable

## Structure

```
api-service/
├── .gencode-gov/project.yaml
├── go.mod
├── main.go
├── handlers/
│   ├── health.go
│   ├── health_test.go
│   ├── greet.go
│   └── greet_test.go
└── README.md
```

## Run

```bash
go test ./...
go run .
```

## GENCODE-GOV

```bash
gencode-gov verify examples/api-service --domain testing
```

Testing results depend on actual execution and evidence collection. Security must remain `BLOCKED` if required TSAR evidence is missing.
