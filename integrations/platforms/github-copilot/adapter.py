"""github-copilot adapter boundary; not yet verified."""
class Adapter:
    name = "github-copilot"
    status = "scaffolded"
    def capabilities(self) -> dict[str,bool]:
        return {"discovery":False,"activation":False,"verified":False}
