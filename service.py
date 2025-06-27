from database import DatabaseManager
from models import CombinedUniterm

class UnitermService:

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_all_saved_names(self) -> list[str]:
        return self.db_manager.get_all_names()

    def load_uniterm(self, name: str) -> CombinedUniterm | None:
        return self.db_manager.get_by_name(name)

    def save_uniterm(self, combined_uniterm: CombinedUniterm) -> bool:
        if not combined_uniterm.is_valid_for_save():
            print("Walidacja nieudana. Brak wymaganych danych do zapisu.")
            return False
        
        return self.db_manager.save(combined_uniterm)

    def delete_uniterm(self, name: str) -> bool:
        return self.db_manager.delete_by_name(name)

