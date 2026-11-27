# Enterprise System Example

A minimal Java enterprise-style service governed by GENCODE-GOV.

Demonstrates:
- Maven project structure
- JUnit 5 tests
- GENCODE-GOV profile: `enterprise`
- Full gate coverage (requirements, testing, security, release)

## Structure

```
enterprise-system/
├── .arkhon/project.yaml
├── pom.xml
└── src/
    ├── main/java/com/example/
    │   └── CustomerService.java
    └── test/java/com/example/
        └── CustomerServiceTest.java
```

## Run

```bash
mvn -B test
mvn -B package
```

## GENCODE-GOV

```bash
gencode-gov verify examples/enterprise-system --domain testing
```

Security remains `BLOCKED` until required TSAR evidence is available; release remains blocked until the required PRR evidence exists.
