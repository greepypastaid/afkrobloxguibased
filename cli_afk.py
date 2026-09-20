"""
cli_afk.py
==========
Versi Command Line Interface (CLI) untuk Roblox Universal AFK Bot.
Mendukung Mode Background Multitasking, Auto Fish, Clicker, Spammer, dan Walk & Jump.
"""

import sys
import time
import argparse
from afk_engine import (
    AFKEngine,
    AFKConfig,
    AFKMode,
    WalkPattern,
    MouseButton
)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def safe_print(text: str):
    """Mencetak teks ke console dengan fallback aman dari UnicodeEncodeError."""
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"), flush=True)

def main():
    parser = argparse.ArgumentParser(
        description="Roblox Universal AFK Bot (Background Multitask & Multi-Mode)",
        allow_abbrev=False
    )

    parser.add_argument(
        "--mode", "-m",
        type=str,
        default="auto_fish",
        choices=["auto_fish", "walk_jump", "auto_clicker", "key_spammer"],
        help="Pilihan mode AFK: auto_fish, walk_jump, auto_clicker, key_spammer (default: auto_fish)"
    )
    parser.add_argument(
        "--foreground", "-fg",
        action="store_true",
        help="Gunakan mode Foreground (secara default bot berjalan di mode Background / Multitask)"
    )
    parser.add_argument(
        "--target", "-t",
        type=str,
        default="roblox",
        help="Kata kunci judul jendela target (default: 'roblox')"
    )
    parser.add_argument(
        "--countdown", "-c",
        type=int,
        default=2,
        help="Waktu hitung mundur sebelum mulai dalam detik (default: 2)"
    )

    # Argumen Auto Fish
    parser.add_argument("--cast-time", type=float, default=0.6, help="Auto Fish: durasi tahan lempar joran (s)")
    parser.add_argument("--wait-bite", type=float, default=3.2, help="Auto Fish: durasi tunggu ikan makan (s)")
    parser.add_argument("--reel-time", type=float, default=4.2, help="Auto Fish: durasi tarik ikan (s)")

    # Argumen Auto Clicker
    parser.add_argument("--click-interval", type=float, default=0.25, help="Auto Clicker: jeda antar klik (s)")
    parser.add_argument("--click-btn", type=str, default="left", choices=["left", "right"], help="Auto Clicker: tombol mouse")

    # Argumen Key Spammer
    parser.add_argument("--key", "-k", type=str, default="e", help="Key Spammer: tombol keyboard yang diulang (e, f, space, 1, dll)")
    parser.add_argument("--key-interval", type=float, default=0.5, help="Key Spammer: jeda antar penekanan tombol (s)")

    # Argumen Walk & Jump
    parser.add_argument("--walk-interval", "-i", type=float, default=6.0, help="Walk: jeda antar langkah (s)")
    parser.add_argument("--walk-duration", "-d", type=float, default=0.8, help="Walk: lama tombol ditahan (s)")
    parser.add_argument("--pattern", "-p", type=str, default="ping_pong", choices=["ping_pong", "square", "left_right", "random"], help="Walk: pola jalan")
    parser.add_argument("--jump-chance", "-j", type=int, default=80, help="Walk: peluang melompat (0-100)")

    args = parser.parse_args()

    config = AFKConfig(
        mode=AFKMode(args.mode),
        background_mode=not args.foreground,
        target_title=args.target,
        countdown_sec=args.countdown,

        # Auto Fish
        fish_cast_duration=args.cast_time,
        fish_wait_bite=args.wait_bite,
        fish_reel_duration=args.reel_time,

        # Auto Clicker
        clicker_interval=args.click_interval,
        clicker_button=MouseButton(args.click_btn),

        # Key Spammer
        spam_key=args.key,
        spam_interval=args.key_interval,

        # Walk & Jump
        walk_interval=args.walk_interval,
        walk_duration=args.walk_duration,
        pattern=WalkPattern(args.pattern),
        jump_chance=args.jump_chance
    )


    engine = AFKEngine(config)

    def log_handler(msg: str):
        now = time.strftime("%H:%M:%S")
        safe_print(f"[{now}] {msg}")

    engine.on_log = log_handler

    safe_print("=" * 65)
    safe_print("     ROBLOX UNIVERSAL AFK BOT (MULTI-MODE & BACKGROUND CLI)")
    safe_print("=" * 65)
    safe_print(f" [•] Mode Aktif       : {config.mode.upper()}")
    safe_print(f" [•] Background Mode  : {'AKTIF (Multitasking Bebas)' if config.background_mode else 'NONAKTIF (Foreground)'}")
    safe_print(f" [•] Target Jendela   : '{config.target_title}'")
    safe_print(f" [•] Hitung Mundur    : {config.countdown_sec} detik")
    safe_print("-" * 65)
    safe_print(" 💡 Tekan Ctrl+C di terminal ini untuk berhenti kapan saja.")
    safe_print("=" * 65)

    try:
        engine.start()
        while engine.is_running():
            time.sleep(0.5)
    except KeyboardInterrupt:
        safe_print("\n[!] Menerima sinyal Ctrl+C...")
    finally:
        engine.stop()
        safe_print("[✔] Bot telah berhenti dengan aman. Semua tombol dilepaskan.")


if __name__ == "__main__":
    main()
