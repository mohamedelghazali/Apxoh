# Web Application Example

A minimal TypeScript + React app governed by Apxoh.

Demonstrates:
- Frontend project structure (src/components, src/pages)
- Testing strategy (vitest + React Testing Library)
- Apxoh profile: `web-application`
- Governance: security, testing, and requirements gates

## What's Inside

```
web-application/
├── .arkhon/project.yaml
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

## Apxoh

```bash
arkhon inspect examples/web-application
arkhon verify examples/web-application --domain testing
```

Expected: testing evidence is evaluated by the configured verification profile. Security remains `BLOCKED` when required TSAR evidence or tooling is unavailable; no PASS is implied by this example alone.
