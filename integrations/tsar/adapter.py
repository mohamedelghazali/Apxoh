"""Optional TSAR adapter contract; no TSAR execution is implied."""
def verify_contract(config: dict) -> bool:
    if not {"source_version","target_version"}.issubset(config):
        raise ValueError("TSAR version contract is incomplete")
    return False
