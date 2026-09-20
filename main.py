"""
main.py
=======
Entry point utama aplikasi Roblox Universal AFK Bot.
Secara default membuka Graphical User Interface (GUI).
Gunakan parameter --cli untuk menjalankan versi terminal.
"""

import sys

def main() -> None:
    if "--cli" in sys.argv:
        # Hapus flag --cli sebelum meneruskan argumen ke parser CLI
        sys.argv.remove("--cli")
        from cli_afk import main as run_cli
        run_cli()
    else:
        from gui_afk import run_gui
        run_gui()

if __name__ == "__main__":
    main()
