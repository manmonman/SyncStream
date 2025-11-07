# sync_client_final_host_only_listener_count_v0_2.py
import subprocess
import yt_dlp
import asyncio
import websockets
import json
import ssl
import certifi
import time
import sys
import os
from colorama import Fore, Style, init



from dotenv import load_dotenv

load_dotenv()  # load variables from .env
SERVER_URL = os.getenv("SERVER_URL")

ssl_context = ssl.create_default_context(cafile=certifi.where())
init(autoreset=True)

listener_count = 0  # Only used by host
current_proc = None  # Track currently playing process


def format_time(sec):
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"


def draw_progress_bar(offset, duration, bar_len=30):
    """Draw inline progress bar (host only shows listener count)"""
    filled_len = int(bar_len * offset / duration) if duration > 0 else 0
    bar = "#" * filled_len + "-" * (bar_len - filled_len)
    sys.stdout.write(
        f"\r[{bar}] {format_time(offset)} / {format_time(duration)}"
        + (f"  🎧 {listener_count} people listening" if listener_count > 0 else "")
    )
    sys.stdout.flush()


def play_audio(url: str, offset=0, duration=0):
    """Play audio via ffplay (blocking) with quiet output and progress bar."""
    global current_proc
    try:
        ydl_opts = {"format": "bestaudio/best", "quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info["url"]
            duration = duration or info.get("duration", 0)
            title = info.get("title", "Unknown Track")

        cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]
        if offset > 0:
            cmd += ["-ss", str(offset)]
        cmd.append(audio_url)

        print(f"\nNow playing: {title}\n")
        current_proc = subprocess.Popen(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        start = time.time() - offset

        while current_proc.poll() is None:
            elapsed = time.time() - start
            if duration > 0 and elapsed >= duration:
                current_proc.terminate()
                break
            draw_progress_bar(min(elapsed, duration), duration)
            time.sleep(1)

        sys.stdout.write("\n")
    except Exception as e:
        print(f"Error playing audio: {e}")


async def play_audio_async(url, offset=0, duration=0):
    """Run blocking play_audio() in background"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, play_audio, url, offset, duration)


async def host_mode():
    """Host a song while also receiving listener updates"""
    global listener_count, current_proc
    async with websockets.connect(SERVER_URL, ssl=ssl_context) as ws:

        async def listen_server():
            """Listen for server messages (listener count + status)"""
            global listener_count
            while True:
                try:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    status = data.get("status")

                    if status == "listeners":
                        listener_count = data.get("count", 0)
                        print(Fore.CYAN + f"\n[Host] 🎧 {listener_count} people connected")
                    else:
                        pass  # ignore other messages

                except websockets.exceptions.ConnectionClosed:
                    print("\nServer disconnected.")
                    break
                except Exception as e:
                    print(f"Listener error in host: {e}")
                    await asyncio.sleep(1)

        listener_task = asyncio.create_task(listen_server())

        while True:
            url = input("\nEnter YouTube URL to host (or 'q' to quit): ").strip()
            if url.lower() == "q":
                listener_task.cancel()
                break

            # Stop current playback if running
            if current_proc and current_proc.poll() is None:
                current_proc.terminate()
                time.sleep(0.5)

            # Extract duration
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(url, download=False)
                duration = info.get("duration", 0)

            # Tell server to start new song
            await ws.send(json.dumps({"type": "HOST", "url": url, "duration": duration}))
            print(f"\nHosting URL: {url} ({duration:.0f}s)\n")
            await play_audio_async(url, 0, duration)


async def listen_mode():
    """Listener mode: plays songs, but does NOT show listener count"""
    global current_proc
    while True:
        try:
            async with websockets.connect(SERVER_URL, ssl=ssl_context) as ws:
                print(Fore.YELLOW + "Connected to server. Waiting for song...\n")
                while True:
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        status = data.get("status")

                        if status == "playing":
                            url = data["url"]
                            start_time = data.get("start_time", 0)
                            duration = data.get("duration", 0)
                            offset = max(0, time.time() - start_time)

                            # Stop current playback if running
                            if current_proc and current_proc.poll() is None:
                                current_proc.terminate()
                                await asyncio.sleep(0.2)

                            print(f"\nSynced offset: {offset:.1f}s")
                            asyncio.create_task(play_audio_async(url, offset, duration))

                        elif status == "nothing_hosted":
                            # Stop current playback if running
                            if current_proc and current_proc.poll() is None:
                                current_proc.terminate()
                            sys.stdout.write("\rNo active host. Waiting for someone to start a song...   ")
                            sys.stdout.flush()
                            await asyncio.sleep(2)

                        else:
                            pass  # ignore other statuses

                    except websockets.exceptions.ConnectionClosed:
                        print("\nServer disconnected. Reconnecting in 2s...")
                        await asyncio.sleep(2)
                        break
                    except Exception as e:
                        print(f"Listener error: {e}")
                        await asyncio.sleep(1)

        except Exception as e:
            print(f"Connection error: {e}. Retrying in 2s...")
            await asyncio.sleep(2)


async def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Fore.CYAN + "╔══════════════════════════════════════╗")
    print(Fore.CYAN + "║ " + Fore.MAGENTA + "SyncStream" + Fore.CYAN + "                           ║")
    print(Fore.CYAN + "║  " + Fore.YELLOW + "Listen together. Stay in sync." + Fore.CYAN + "      ║")
    print(Fore.CYAN + "║  Version 0.2                         ║")
    print(Fore.CYAN + "╚══════════════════════════════════════╝" + Style.RESET_ALL)
    print()

    print("Select mode:")
    print("1. Host a song")
    print("2. Listen to a song")
    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        await host_mode()
    elif choice == "2":
        await listen_mode()
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    asyncio.run(main())
