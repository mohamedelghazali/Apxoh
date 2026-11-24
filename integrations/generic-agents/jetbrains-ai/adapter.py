"""jetbrains-ai adapter boundary; not yet verified."""
class Adapter:
    name = "jetbrains-ai"
    status = "scaffolded"
    def capabilities(self) -> dict[str,bool]:
        return {"discovery":False,"activation":False,"verified":False}
