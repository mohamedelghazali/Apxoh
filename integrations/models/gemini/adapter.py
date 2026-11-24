"""gemini adapter boundary; not yet verified."""
class Adapter:
    name = "gemini"
    status = "scaffolded"
    def capabilities(self) -> dict[str,bool]:
        return {"discovery":False,"activation":False,"verified":False}
