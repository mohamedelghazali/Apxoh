# Web Application Example

A minimal TypeScript + React app governed by GENCODE-GOV.

Demonstrates:
- Frontend project structure (src/components, src/pages)
- Testing strategy (vitest + React Testing Library)
- GENCODE-GOV profile: `web-application`
- Governance: security, testing, and requirements gates

## What's Inside

```
web-application/
├── .gencode-gov/project.yaml
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── src/
│   ├── main.tsx
│   └── components/
│       └── Greeting.tsx
└── tests/
    └── Greeting.test.tsx
```

## Run

```bash
npm install
npm test
npx tsc --noEmit
npm run build
```

## GENCODE-GOV

```bash
gencode-gov inspect examples/web-application
gencode-gov verify examples/web-application --domain testing
```

Expected: testing evidence is evaluated by the configured verification profile. Security remains `BLOCKED` when required TSAR evidence or tooling is unavailable; no PASS is implied by this example alone.
