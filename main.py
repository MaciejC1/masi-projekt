import tkinter as tk
from tkinter import messagebox
from database import DatabaseManager
from service import UnitermService
from ui import UnitermApp

def main():
    try:
        db_manager = DatabaseManager(
            host='127.0.0.1',
            port=3307,
            user='uniterm_user',
            password='uniterm_password',
            db_name='uniterm_db'
        )

        uniterm_service = UnitermService(db_manager)

        root = tk.Tk()
        app = UnitermApp(root, uniterm_service)
        
        root.mainloop()

    except ConnectionError as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Błąd krytyczny", str(e))
        root.destroy()
    except Exception as e:
        messagebox.showerror("Nieoczekiwany błąd", f"Wystąpił błąd: {e}")


if __name__ == "__main__":
    main()
