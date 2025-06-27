import mysql.connector
from mysql.connector import Error
import time
from models import Uniterm, CombinedUniterm

class DatabaseManager:

    def __init__(self, host, port, user, password, db_name):
        self.connection = None
        for i in range(5):
            try:
                self.connection = mysql.connector.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=db_name
                )
                if self.connection.is_connected():
                    print("Pomyślnie połączono z bazą danych MySQL")
                    self._create_table()
                    return
            except Error as e:
                print(f"Błąd podczas łączenia z MySQL: {e}")
                print(f"Próba ponownego połączenia za 5 sekund... ({i+1}/5)")
                time.sleep(5)
        
        if not self.connection or not self.connection.is_connected():
            raise ConnectionError("Nie można połączyć się z bazą danych MySQL.")

    def _create_table(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uniterms (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    uniterm1_val_a VARCHAR(255),
                    uniterm1_val_b VARCHAR(255),
                    uniterm1_separator VARCHAR(1),
                    uniterm2_val_a VARCHAR(255),
                    uniterm2_val_b VARCHAR(255),
                    uniterm2_separator VARCHAR(1),
                    combination_mode VARCHAR(20)
                )
            """)
            cursor.execute("SHOW COLUMNS FROM uniterms LIKE 'combination_mode'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE uniterms ADD COLUMN combination_mode VARCHAR(20)")
                print("Zaktualizowano tabelę 'uniterms', dodano kolumnę 'combination_mode'.")
            print("Tabela 'uniterms' została sprawdzona/utworzona.")
        except Error as e:
            print(f"Błąd podczas tworzenia/aktualizacji tabeli: {e}")
            raise

    def save(self, combined_uniterm: CombinedUniterm) -> bool:
        sql = """
            INSERT INTO uniterms (
                name, uniterm1_val_a, uniterm1_val_b, uniterm1_separator,
                uniterm2_val_a, uniterm2_val_b, uniterm2_separator,
                combination_mode
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                uniterm1_val_a=VALUES(uniterm1_val_a), uniterm1_val_b=VALUES(uniterm1_val_b),
                uniterm1_separator=VALUES(uniterm1_separator), uniterm2_val_a=VALUES(uniterm2_val_a),
                uniterm2_val_b=VALUES(uniterm2_val_b), uniterm2_separator=VALUES(uniterm2_separator),
                combination_mode=VALUES(combination_mode)
        """
        try:
            cursor = self.connection.cursor()
            data_tuple = (
                combined_uniterm.name,
                combined_uniterm.base_uniterm.val_a, combined_uniterm.base_uniterm.val_b, combined_uniterm.base_uniterm.separator,
                combined_uniterm.nested_uniterm.val_a, combined_uniterm.nested_uniterm.val_b, combined_uniterm.nested_uniterm.separator,
                combined_uniterm.combination_mode
            )
            cursor.execute(sql, data_tuple)
            self.connection.commit()
            print(f"Uniterm '{combined_uniterm.name}' został zapisany/zaktualizowany.")
            return True
        except Error as e:
            print(f"Błąd podczas zapisywania unitermu: {e}")
            return False

    def get_by_name(self, name: str) -> CombinedUniterm | None:
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM uniterms WHERE name = %s", (name,))
            record = cursor.fetchone()
            if record:
                return CombinedUniterm(
                    name=record['name'],
                    base_uniterm=Uniterm(record['uniterm1_val_a'], record['uniterm1_val_b'], record['uniterm1_separator']),
                    nested_uniterm=Uniterm(record['uniterm2_val_a'], record['uniterm2_val_b'], record['uniterm2_separator']),
                    combination_mode=record['combination_mode']
                )
            return None
        except Error as e:
            print(f"Błąd podczas pobierania unitermu '{name}': {e}")
            return None

    def get_all_names(self) -> list[str]:
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM uniterms ORDER BY name")
            return [record[0] for record in cursor.fetchall()]
        except Error as e:
            print(f"Błąd podczas pobierania nazw unitermów: {e}")
            return []

    def delete_by_name(self, name: str) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM uniterms WHERE name = %s", (name,))
            self.connection.commit()
            print(f"Uniterm '{name}' został usunięty.")
            return True
        except Error as e:
            print(f"Błąd podczas usuwania unitermu '{name}': {e}")
            return False

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Połączenie z bazą danych zostało zamknięte.")
