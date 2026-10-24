import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://lcxnr-like.vercel.app"
KEY = "LCXNR"
UID_FILE = "uid.txt"
SERVER_NAME = "BD"
MAX_WORKERS = 10      # request paralel untuk SEND
DELAY = 0.3           # jeda kecil tiap worker

COMMON_HEADERS = {
    "accept": "*/*",
    "accept-language": "en,ja;q=0.9,id;q=0.8,ko;q=0.7",
    "dnt": "1",
    "priority": "u=1, i",
    "sec-ch-ua": '"Google Chrome";v="155", "Chromium";v="155", "Not(A:Brand";v="24"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": (
        "Mozilla/5.0 (Linux; Android 16; Pixel 10) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/155.0.0.0 Mobile Safari/537.36"
    ),
}


# ---------- STEP 1 : RELOAD (cuma 1x) ----------
def refresh_jwt():
    headers = {
        **COMMON_HEADERS,
        "content-type": "application/json",
        "origin": BASE,
        "referer": f"{BASE}/master",
    }
    r = requests.post(
        f"{BASE}/master/api/jwt-refresh",
        params={"key": KEY},
        headers=headers,
        json={"key": KEY},
        timeout=30,
    )
    r.raise_for_status()
    return r


# ---------- STEP 2 : SEND REQUESTS ----------
def send_like(uid):
    time.sleep(DELAY)
    return requests.get(
        f"{BASE}/nmcdx&like",
        params={"uid": uid, "server_name": SERVER_NAME, "key": KEY},
        headers={**COMMON_HEADERS, "referer": f"{BASE}/"},
        timeout=30,
    )


def baca_uid(path=UID_FILE):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            uid = line.strip()
            if uid and not uid.startswith("#"):
                yield uid


if __name__ == "__main__":
    # ===== RELOAD JWT (sekali saja) =====
    try:
        r1 = refresh_jwt()
        print(f"[RELOAD] {r1.status_code} -> {r1.text[:150]}")
    except requests.RequestException as e:
        print(f"[RELOAD] ERROR: {e}")

    # ===== SEND REQUESTS (paralel) =====
    uids = list(baca_uid())
    total = len(uids)
    print(f"[SEND] memproses {total} UID dengan {MAX_WORKERS} worker")
    sukses = gagal = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(send_like, uid): uid for uid in uids}
        for i, fut in enumerate(as_completed(futures), 1):
            uid = futures[fut]
            try:
                r = fut.result()
                status = "OK" if r.ok else f"HTTP {r.status_code}"
                print(f"[{i}/{total}] uid={uid} -> {status}")
                sukses += 1
            except requests.RequestException as e:
                print(f"[{i}/{total}] uid={uid} -> ERROR: {e}")
                gagal += 1

    print(f"\nSelesai. Total: {total} | Sukses: {sukses} | Gagal: {gagal}")
