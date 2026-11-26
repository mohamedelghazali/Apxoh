"""Extensible security attack-class taxonomy mapped to Apxoh governance rules."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class AttackClassDefinition:
    """Declarative specification for one security investigation attack class."""

    id: str
    name: str
    domain_group: str
    summary: str
    related_rules: tuple[str, ...]
    entry_indicators: tuple[str, ...]
    sink_indicators: tuple[str, ...]
    defensive_invariants: tuple[str, ...]
    investigation_steps: tuple[str, ...]
    verification_hooks: tuple[str, ...]


_BUILTIN_CLASSES: tuple[AttackClassDefinition, ...] = (
    AttackClassDefinition(
        id="ai-llm-security",
        name="AI, Prompt, and Agent Tool Security",
        domain_group="ai-and-llm",
        summary=(
            "Indirect prompt injection, untrusted tool arguments, confused-deputy agency, "
            "and cross-session memory or MCP trust inheritance."
        ),
        related_rules=("SE-SEC-003", "SE-SEC-002", "SE-SEC-007"),
        entry_indicators=("prompt", "completion", "mcp", "tool_call", "agent"),
        sink_indicators=("subprocess", "eval", "exec", "execute"),
        defensive_invariants=(
            "Treat retrieved documents, tool outputs, and peer agent text as untrusted data.",
            "Validate tool arguments against strict schemas and principal authorization.",
        ),
        investigation_steps=(
            "Trace untrusted context into tool-call dispatchers and shell/database sinks.",
            "Verify human confirmation or policy gates before state-changing agent actions.",
        ),
        verification_hooks=("ast-sink-check", "tool-schema-boundary-check"),
    ),
    AttackClassDefinition(
        id="memory-binary-safety",
        name="Memory Safety and Binary Parsing",
        domain_group="memory-and-binary",
        summary=(
            "Out-of-bounds access, integer truncation or overflow, use-after-free, "
            "and unsafe FFI or native buffer parsing."
        ),
        related_rules=("SE-SEC-003", "SE-TST-004"),
        entry_indicators=("ctypes", "cffi", "unsafe", "struct.unpack", "mmap"),
        sink_indicators=("memcpy", "strcpy", "cast", "from_buffer"),
        defensive_invariants=(
            "Enforce explicit length bounds before buffer copies or native FFI calls.",
            "Validate integer widths and signedness prior to allocation arithmetic.",
        ),
        investigation_steps=(
            "Inspect native bindings, unsafe blocks, and binary frame length calculations.",
            "Check negative and truncated frame inputs with bounded local fixtures.",
        ),
        verification_hooks=("ffi-boundary-review", "bounded-fixture-check"),
    ),
    AttackClassDefinition(
        id="web-protocol-security",
        name="Web Application and HTTP Protocol Security",
        domain_group="web-protocol-and-auth",
        summary=(
            "HTTP framing ambiguity, cache poisoning or deception, host/forwarded header "
            "trust, header injection, and cross-site request forgery."
        ),
        related_rules=("SE-SEC-004", "SE-SEC-001", "SE-SEC-003"),
        entry_indicators=("request", "headers", "x-forwarded", "cookie", "redirect"),
        sink_indicators=("set_cookie", "location", "cache", "cors"),
        defensive_invariants=(
            "Ignore untrusted Host and X-Forwarded-* headers unless behind verified proxies.",
            "Enforce CSRF tokens or SameSite policies on cookie-authenticated mutations.",
        ),
        investigation_steps=(
            "Trace request headers into redirect URLs, cache keys, and session cookies.",
            "Verify CORS origin allowlists do not reflect arbitrary origins with credentials.",
        ),
        verification_hooks=("http-header-trust-check", "cors-csrf-policy-check"),
    ),
    AttackClassDefinition(
        id="authn-authz-boundaries",
        name="Authentication and Authorization Boundary Failures",
        domain_group="web-protocol-and-auth",
        summary=(
            "Broken object/function-level authorization, session fixation, missing "
            "deny-by-default guards, and privilege escalation."
        ),
        related_rules=("SE-SEC-001", "SE-SEC-002", "SE-SEC-006"),
        entry_indicators=("login", "session", "token", "admin", "role"),
        sink_indicators=("delete", "update", "grant", "impersonate"),
        defensive_invariants=(
            "Enforce server-side principal and role checks on every protected route.",
            "Rotate session identifiers on authentication state transitions.",
        ),
        investigation_steps=(
            "Compare sibling route handlers and admin endpoints for missing auth guards.",
            "Check password recovery token entropy, single-use invalidation, and TTL.",
        ),
        verification_hooks=("route-auth-guard-check", "session-lifecycle-check"),
    ),
    AttackClassDefinition(
        id="api-security",
        name="API Schema, Binding, and Endpoint Security",
        domain_group="api-and-rpc",
        summary=(
            "Mass assignment, undocumented shadow endpoints, schema-to-handler drift, "
            "and unauthenticated GraphQL or REST mutations."
        ),
        related_rules=("SE-API-001", "SE-SEC-002", "SE-SEC-003"),
        entry_indicators=("router", "endpoint", "graphql", "openapi", "payload"),
        sink_indicators=("setattr", "update_fields", "from_dict", "**payload"),
        defensive_invariants=(
            "Bind incoming API fields through explicit allowlisted DTOs or schemas.",
            "Version public APIs and enforce per-field authorization on mutations.",
        ),
        investigation_steps=(
            "Inspect request deserializers for wildcard attribute assignment into models.",
            "Compare OpenAPI or router registrations against middleware exclusions.",
        ),
        verification_hooks=("dto-allowlist-check", "api-route-inventory-check"),
    ),
    AttackClassDefinition(
        id="client-side-security",
        name="Client-Side DOM, Storage, and Cross-Origin Security",
        domain_group="client-side",
        summary=(
            "DOM XSS, prototype pollution, postMessage origin trust, WebSocket origin "
            "omission, and sensitive token exposure in browser storage."
        ),
        related_rules=("SE-SEC-003", "SE-SEC-004"),
        entry_indicators=("innerHTML", "dangerouslySetInnerHTML", "postMessage", "localStorage"),
        sink_indicators=("document.write", "eval", "Object.assign", "BroadcastChannel"),
        defensive_invariants=(
            "Render untrusted strings through context-aware escaping rather than raw HTML.",
            "Verify event.origin strictly in postMessage and WebSocket handshakes.",
        ),
        investigation_steps=(
            "Trace URL fragments, storage reads, and postMessage handlers to DOM sinks.",
            "Inspect deep-merge helpers for __proto__ and constructor key pollution.",
        ),
        verification_hooks=("dom-sink-check", "origin-validation-check"),
    ),
    AttackClassDefinition(
        id="supply-chain-release",
        name="Supply-Chain, Build, and CI Release Security",
        domain_group="supply-chain-and-release",
        summary=(
            "Privileged workflow injection, unpinned mutable build inputs, dependency "
            "namespace confusion, and unsigned or unverified release artifacts."
        ),
        related_rules=("SE-SEC-008", "SE-INF-001", "SE-SEC-GOV-001"),
        entry_indicators=("pull_request_target", "workflow_run", "pip install", "curl"),
        sink_indicators=("GITHUB_ENV", "GITHUB_PATH", "run:", "setup.py"),
        defensive_invariants=(
            "Never execute untrusted PR code or interpolate PR titles in privileged CI.",
            "Bind SBOMs and release attestations to the exact verified commit SHA.",
        ),
        investigation_steps=(
            "Review GitHub Actions triggers, permissions, and expression interpolations.",
            "Verify dependency lockfiles, registry pinning, and artifact digest checks.",
        ),
        verification_hooks=("ci-workflow-privilege-check", "sbom-provenance-check"),
    ),
    AttackClassDefinition(
        id="cloud-deployment-security",
        name="Cloud IAM, Container, and Deployment Security",
        domain_group="cloud-and-deployment",
        summary=(
            "Over-broad workload IAM roles, metadata service SSRF, privileged container "
            "capabilities, and public bucket or signed-URL misconfigurations."
        ),
        related_rules=("SE-INF-001", "SE-SEC-009", "SE-OBS-002"),
        entry_indicators=("Dockerfile", "terraform", "kubernetes", "iam", "169.254.169.254"),
        sink_indicators=("privileged: true", "Action: '*'", "0.0.0.0", "hostNetwork"),
        defensive_invariants=(
            "Run workloads as non-root with least-privilege IAM policies and private admin.",
            "Block untrusted outbound requests from reaching instance metadata endpoints.",
        ),
        investigation_steps=(
            "Inspect container specs, IaC roles, ingress bindings, and signed-URL scopes.",
            "Verify operational dashboards and diagnostics are restricted from public ingress.",
        ),
        verification_hooks=("iac-least-privilege-check", "container-hardening-check"),
    ),
    AttackClassDefinition(
        id="protocols-rpc-messaging",
        name="RPC, Framing, and Asynchronous Messaging Security",
        domain_group="protocols-rpc-and-messaging",
        summary=(
            "Envelope-vs-payload identity mismatch, gRPC interceptor bypass, streaming "
            "per-message authorization gaps, and broker spoofing."
        ),
        related_rules=("SE-SEC-002", "SE-SEC-003", "SE-API-001"),
        entry_indicators=("grpc", "protobuf", "kafka", "amqp", "webhook"),
        sink_indicators=("handler", "consumer", "deserialize", "dispatch"),
        defensive_invariants=(
            "Authenticate message producers and re-verify tenant authority per message.",
            "Ensure canonical schema validation agrees across gateway and worker parsers.",
        ),
        investigation_steps=(
            "Compare unary vs streaming RPC interceptors and async queue consumers.",
            "Verify webhook signature checks use constant-time HMAC over raw bytes.",
        ),
        verification_hooks=("rpc-interceptor-parity-check", "message-auth-check"),
    ),
    AttackClassDefinition(
        id="resource-exhaustion-availability",
        name="Resource Exhaustion and Algorithmic Availability",
        domain_group="resource-exhaustion",
        summary=(
            "Catastrophic regex backtracking, decompression or XML amplification, "
            "unbounded memory buffering, and pre-auth work amplification."
        ),
        related_rules=("SE-SEC-006", "SE-PRF-002", "SE-REL-001"),
        entry_indicators=("re.compile", "zipfile", "tarfile", "xml", "read()"),
        sink_indicators=("extractall", " ElementTree.fromstring", "findall", "while True"),
        defensive_invariants=(
            "Bound input byte size, decompression ratios, XML entities, and query limits.",
            "Rate-limit expensive pre-authentication and password-hashing endpoints.",
        ),
        investigation_steps=(
            "Inspect archive extraction, XML parsers, regexes on user input, and body reads.",
            "Verify timeouts and concurrency caps on external calls and worker loops.",
        ),
        verification_hooks=("parser-amplification-check", "bound-limit-check"),
    ),
    AttackClassDefinition(
        id="data-tenant-isolation",
        name="Data Ownership and Multi-Tenant Isolation",
        domain_group="data-isolation-and-lifecycle",
        summary=(
            "Missing tenant or owner predicates on queries, cache/search index namespace "
            "collisions, and cross-tenant object reference leaks."
        ),
        related_rules=("SE-DB-002", "SE-SEC-002"),
        entry_indicators=("tenant_id", "org_id", "owner_id", "user_id", "SELECT"),
        sink_indicators=("filter", "get_by_id", "cache_key", "search_index"),
        defensive_invariants=(
            "Scope every database read, mutation, cache key, and search query by tenant.",
            "Derive tenant context from authenticated session state, never request params.",
        ),
        investigation_steps=(
            "Audit repository/DAO methods and batch endpoints for unscoped primary-key lookups.",
            "Check shared caches, background exports, and search indexes for tenant prefixes.",
        ),
        verification_hooks=("tenant-predicate-check", "cache-key-isolation-check"),
    ),
    AttackClassDefinition(
        id="data-lifecycle-privacy",
        name="Data Lifecycle, Logging Redaction, Backup, and Deletion",
        domain_group="data-isolation-and-lifecycle",
        summary=(
            "Sensitive data or credentials leaked into logs, crash dumps, analytics, or "
            "unencrypted backups, and incomplete deletion across derived stores."
        ),
        related_rules=("SE-OBS-003", "SE-SEC-007", "SE-REL-004"),
        entry_indicators=("logger", "logging", "traceback", "coredump", "backup"),
        sink_indicators=("logger.info", "logger.error", "print(", "dump"),
        defensive_invariants=(
            "Redact passwords, tokens, keys, cookies, and PII from logs and error responses.",
            "Protect crash dumps and backups with encryption, access control, and retention.",
        ),
        investigation_steps=(
            "Trace auth payloads and exception handlers into logging and response serializers.",
            "Verify deletion and retention workflows purge replicas, caches, and exports.",
        ),
        verification_hooks=("log-redaction-check", "crash-dump-governance-check"),
    ),
    AttackClassDefinition(
        id="desktop-application-security",
        name="Desktop Client and Native Bridge Security",
        domain_group="desktop-mobile-ipc",
        summary=(
            "Electron or WebView nodeIntegration/preload bridge overreach, custom URI "
            "protocol handler injection, and unsafe local file-open authority."
        ),
        related_rules=("SE-SEC-003", "SE-SEC-009"),
        entry_indicators=("BrowserWindow", "nodeIntegration", "contextIsolation", "ipcMain"),
        sink_indicators=("shell.openExternal", "preload", "executeJavaScript"),
        defensive_invariants=(
            "Enable contextIsolation and sandbox while restricting preload IPC exposure.",
            "Validate custom protocol URLs and external shell schemes against strict allowlists.",
        ),
        investigation_steps=(
            "Inspect desktop window preferences, IPC handlers, and navigation guards.",
            "Trace untrusted deep links or opened documents into native shell helpers.",
        ),
        verification_hooks=("desktop-bridge-check", "uri-scheme-allowlist-check"),
    ),
    AttackClassDefinition(
        id="mobile-application-security",
        name="Mobile Deep-Link, Component, and Keychain Security",
        domain_group="desktop-mobile-ipc",
        summary=(
            "Exported mobile activities/receivers, ambiguous deep-link OAuth callbacks, "
            "WebView file access, and cleartext local credential storage."
        ),
        related_rules=("SE-SEC-001", "SE-SEC-004", "SE-SEC-005"),
        entry_indicators=("AndroidManifest.xml", "Info.plist", "exported=", "Intent"),
        sink_indicators=("SharedPreferences", "NSUserDefaults", "allowFileAccess", "loadUrl"),
        defensive_invariants=(
            "Disable unauthenticated exported components and verify App Links / Universal Links.",
            "Store tokens in OS-backed Keystore/Keychain and enforce TLS certificate checks.",
        ),
        investigation_steps=(
            "Audit manifest exported flags, intent filters, and OAuth redirect schemes.",
            "Inspect mobile WebView settings and local storage usage for secrets.",
        ),
        verification_hooks=("mobile-manifest-check", "webview-isolation-check"),
    ),
    AttackClassDefinition(
        id="local-ipc-trust",
        name="Local IPC, Socket, and Inter-Process Trust Boundaries",
        domain_group="desktop-mobile-ipc",
        summary=(
            "World-writable Unix domain sockets or named pipes, missing peer UID/PID "
            "verification, symlink/TOCTOU races in shared temp directories."
        ),
        related_rules=("SE-SEC-002", "SE-SEC-009"),
        entry_indicators=("AF_UNIX", "NamedPipe", "/tmp/", "mktemp", "chmod"),
        sink_indicators=("0o777", "0o666", "bind(", "symlink"),
        defensive_invariants=(
            "Create local IPC sockets and scratch directories with 0700/0600 permissions.",
            "Use O_NOFOLLOW and descriptor-pinned operations when crossing privilege boundaries.",
        ),
        investigation_steps=(
            "Inspect Unix socket permissions, peer credential checks, and /tmp file creation.",
            "Verify artifact promotion and file staging reject symlinks, FIFOs, and hardlinks.",
        ),
        verification_hooks=("ipc-permission-check", "toctou-nofollow-check"),
    ),
    AttackClassDefinition(
        id="cryptographic-implementation",
        name="Cryptographic Primitives and Password Hashing",
        domain_group="crypto-and-secrets",
        summary=(
            "Weak password hashing (MD5/SHA1/raw SHA256), static IV/nonce reuse, "
            "unauthenticated encryption, non-constant-time MAC comparison, and weak RNG."
        ),
        related_rules=("SE-SEC-001", "SE-SEC-004"),
        entry_indicators=("hashlib.md5", "hashlib.sha1", "random.", "AES.MODE_ECB"),
        sink_indicators=("md5(", "sha1(", "random.choice", "=="),
        defensive_invariants=(
            "Hash passwords with Argon2id, bcrypt, or scrypt and generate tokens via secrets.",
            "Use authenticated encryption (AES-GCM/ChaCha20-Poly1305) and hmac.compare_digest.",
        ),
        investigation_steps=(
            "Locate password, token, signature, and encryption helpers across the codebase.",
            "Verify random token generation uses CSPRNG and digest comparisons are constant-time.",
        ),
        verification_hooks=("crypto-primitive-check", "constant-time-compare-check"),
    ),
    AttackClassDefinition(
        id="secrets-credential-handling",
        name="Secrets, API Keys, Environment, and Git History Governance",
        domain_group="crypto-and-secrets",
        summary=(
            "Hardcoded credentials or private keys, committed .env files, ambient "
            "environment leakage to child processes, and unrotated exposed secrets."
        ),
        related_rules=("SE-SEC-005", "SE-SEC-010", "SE-DB-002"),
        entry_indicators=("API_KEY", "SECRET", "PASSWORD", "PRIVATE KEY", "os.environ"),
        sink_indicators=("subprocess", ".env", "headers=", "connect("),
        defensive_invariants=(
            "Never commit live secrets or pass unfiltered host environments to untrusted code.",
            "Scan Git history and revoke/rotate any exposed credential immediately.",
        ),
        investigation_steps=(
            "Scan source, configs, and fixtures for hardcoded secret literals or private keys.",
            "Inspect subprocess calls for ambient os.environ inheritance across boundaries.",
        ),
        verification_hooks=("hardcoded-secret-check", "env-allowlist-check"),
    ),
    AttackClassDefinition(
        id="injection-input-handling",
        name="Injection, Deserialization, and Path Traversal",
        domain_group="injection-and-input",
        summary=(
            "SQL injection, OS command injection, SSRF, unsafe deserialization "
            "(pickle/yaml.load), SSTI, XXE, and path traversal."
        ),
        related_rules=("SE-SEC-003", "SE-DB-002"),
        entry_indicators=("execute(", "subprocess", "pickle", "yaml.load", "open("),
        sink_indicators=("shell=True", "pickle.loads", "eval(", "exec(", "urllib.request"),
        defensive_invariants=(
            "Use parameterized queries, shell=False with fixed argv, and safe deserializers.",
            "Confine filesystem paths with resolve().relative_to(trusted_root) and O_NOFOLLOW.",
        ),
        investigation_steps=(
            "Trace dynamic string formatting into SQL, shell, template, and URL fetchers.",
            "Verify YAML/XML/serialization loaders reject arbitrary object instantiation.",
        ),
        verification_hooks=("ast-injection-check", "path-confinement-check"),
    ),
    AttackClassDefinition(
        id="configuration-infrastructure",
        name="Production Configuration, TLS, and Debug Surface Hardening",
        domain_group="configuration-and-infra",
        summary=(
            "Production debug modes enabled, disabled TLS certificate verification, "
            "exposed administrative/diagnostic endpoints, and permissive defaults."
        ),
        related_rules=("SE-SEC-004", "SE-SEC-009", "SE-OBS-002"),
        entry_indicators=("debug=True", "DEBUG = True", "verify=False", "CERT_NONE"),
        sink_indicators=("run(", "requests.", "httpx.", "ssl._create_unverified_context"),
        defensive_invariants=(
            "Disable interactive debuggers and verbose stack traces in production configs.",
            "Enforce TLS certificate chain and hostname verification on all outbound connections.",
        ),
        investigation_steps=(
            "Check web server launch flags, framework settings, and HTTP client TLS options.",
            "Inventory administrative, metrics, and sensitive static file routes.",
        ),
        verification_hooks=("tls-verification-check", "debug-flag-check"),
    ),
)


class AttackClassRegistry:
    """Immutable-by-default registry supporting extensible custom attack classes."""

    def __init__(
        self,
        definitions: tuple[AttackClassDefinition, ...] = _BUILTIN_CLASSES,
    ) -> None:
        by_id: dict[str, AttackClassDefinition] = {}
        for item in definitions:
            if not item.id or item.id in by_id:
                raise ValueError(f"invalid or duplicate attack class id: {item.id!r}")
            by_id[item.id] = item
        self._by_id: dict[str, AttackClassDefinition] = by_id

    def register(self, definition: AttackClassDefinition) -> None:
        """Register an additional project-specific attack class without shadowing."""
        if not definition.id or definition.id in self._by_id:
            raise ValueError(f"invalid or duplicate attack class id: {definition.id!r}")
        self._by_id[definition.id] = definition

    def get(self, class_id: str) -> AttackClassDefinition | None:
        return self._by_id.get(class_id)

    def require(self, class_id: str) -> AttackClassDefinition:
        found = self._by_id.get(class_id)
        if found is None:
            raise KeyError(f"unknown attack class: {class_id}")
        return found

    def all(self) -> tuple[AttackClassDefinition, ...]:
        return tuple(self._by_id[key] for key in sorted(self._by_id))

    def as_mapping(self) -> Mapping[str, AttackClassDefinition]:
        return MappingProxyType(dict(self._by_id))

    def __len__(self) -> int:
        return len(self._by_id)


DEFAULT_TAXONOMY = AttackClassRegistry()
