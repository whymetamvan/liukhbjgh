import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = "https://lcxnr-like.up.railway.app"
KEY = "LCXNR"
UID_FILE = "uid.txt"
LOG_FILE = "log.txt"
SERVER_NAME = "BD"
REQUEST_TIMEOUT = 30

JWT_REFRESH_DELAY = 7 * 60
LIKE_DELAY = 5 * 60

WIB = ZoneInfo("Asia/Jakarta")

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


def log(msg, fh):
    print(msg)
    fh.write(msg + "\n")
    fh.flush()


def wait_delay(seconds, label, fh):
    if seconds <= 0:
        return
    log(f"[WAIT] {label} menunggu {seconds} detik...", fh)
    time.sleep(seconds)


def refresh_jwt():
    headers = {
        **COMMON_HEADERS,
        "content-type": "application/json",
        "origin": BASE,
        "referer": f"{BASE}/master",
    }
    return requests.post(
        f"{BASE}/master/api/jwt-refresh",
        params={"key": KEY},
        headers=headers,
        json={"key": KEY},
        timeout=REQUEST_TIMEOUT,
    )


def send_like(uid):
    return requests.get(
        f"{BASE}/nmcdx&like",
        params={"uid": uid, "server_name": SERVER_NAME, "key": KEY},
        headers={**COMMON_HEADERS, "referer": f"{BASE}/"},
        timeout=REQUEST_TIMEOUT,
    )


def baca_uid(path=UID_FILE):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            uid = line.strip()
            if uid and not uid.startswith("#"):
                yield uid


def ringkas(text, limit=200):
    text = (text or "").replace("\n", " ").strip()
    return text if len(text) <= limit else text[:limit] + "..."


if __name__ == "__main__":
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        ts = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S WIB")
        log(f"\n===== RUN {ts} =====", fh)

        # ----- RELOAD JWT with delay -----
        try:
            wait_delay(JWT_REFRESH_DELAY, "REFRESH JWT", fh)
            r1 = refresh_jwt()
            log(f"[RELOAD] {r1.status_code} -> {ringkas(r1.text)}", fh)
        except requests.RequestException as e:
            log(f"[RELOAD] ERROR: {e}", fh)

        # ----- SEND REQUESTS sequentially with delay per UID -----
        uids = list(baca_uid())
        total = len(uids)
        log(f"[SEND] memproses {total} UID secara berurutan dengan delay {LIKE_DELAY} detik per UID", fh)
        sukses = gagal = 0

        for i, uid in enumerate(uids, 1):
            if i > 1:
                wait_delay(LIKE_DELAY, f"UID {uid}", fh)
            else:
                # delay before first UID too, to keep spacing consistent
                wait_delay(LIKE_DELAY, f"UID {uid}", fh)

            try:
                r = send_like(uid)
                status = "OK" if r.ok else f"HTTP {r.status_code}"
                log(f"[{i}/{total}] uid={uid} -> {status} | {ringkas(r.text)}", fh)
                sukses += 1
            except requests.RequestException as e:
                log(f"[{i}/{total}] uid={uid} -> ERROR: {e}", fh)
                gagal += 1

        log(f"Summary: Total={total} | Sukses={sukses} | Gagal={gagal}", fh)
        log(f"===== END RUN =====", fh)
