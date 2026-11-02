# API Service Example

A minimal Go HTTP API governed by Apxoh.

Demonstrates:
- Health endpoint (required by `SE-OBS-001`)
- Handler with tests
- Apxoh profile: `api-service`
- Security gate remains blocked when required TSAR evidence is unavailable

## Structure

```
api-service/
├── .arkhon/project.yaml
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

## Apxoh

```bash
arkhon verify examples/api-service --domain testing
```

Testing results depend on actual execution and evidence collection. Security must remain `BLOCKED` if required TSAR evidence is missing.
