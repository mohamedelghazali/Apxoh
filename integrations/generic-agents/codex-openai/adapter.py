"""codex-openai adapter boundary; not yet verified."""
class Adapter:
    name = "codex-openai"
    status = "scaffolded"
    def capabilities(self) -> dict[str,bool]:
        return {"discovery":False,"activation":False,"verified":False}
