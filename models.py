from dataclasses import dataclass, field

@dataclass
class Uniterm:
    val_a: str = ""
    val_b: str = ""
    separator: str = ":"

    def is_complete(self) -> bool:
        return bool(self.val_a and self.val_b)

@dataclass
class CombinedUniterm:
    name: str = ""
    base_uniterm: Uniterm = field(default_factory=Uniterm)
    nested_uniterm: Uniterm = field(default_factory=Uniterm)
    combination_mode: str | None = None

    def is_valid_for_save(self) -> bool:
        return (
            bool(self.name) and
            self.base_uniterm.is_complete() and
            self.nested_uniterm.is_complete()
        )
