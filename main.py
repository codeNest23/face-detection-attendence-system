from opencv.fr import FR
from opencv.fr.search.schemas import SearchRequest, SearchMode

import cv2
import tempfile
import os
from pathlib import Path
import time
from datetime import datetime

BACKEND_URL = "https://us.opencv.fr"
DEVELOPER_KEY = "elaBl7xMjVlNGI2ZmUtZTA1YS00MWRiLWE3N2QtMjdiMDhhY2M5NTc4"

sdk = FR(BACKEND_URL, DEVELOPER_KEY)

person_memory = {}

API_COOLDOWN = 1.2
EVENT_COOLDOWN = 2.5
LINE_Y = 240

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def search_frame(frame):
    temp_path = None

    try:
        frame = cv2.resize(frame, (640, 480))

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            temp_path = tmp.name

        cv2.imwrite(temp_path, frame)

        search_request = SearchRequest(
            [Path(temp_path)],
            min_score=0.6,
            collection_id=None,
            search_mode=SearchMode.FAST
        )

        return sdk.search.search(search_request)

    except Exception as e:
        print("🔥 API Error:", e)

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    return None


def detect_face_y(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return None

    (x, y, w, h) = faces[0]
    return y + h // 2


def update_logic(results, centroid_y):
    now_str = datetime.now().strftime("%H:%M:%S")
    current_time = time.time()

    if not results or centroid_y is None:
        return

    current_side = "inside" if centroid_y < LINE_Y else "outside"

    for match in results:
        person = match.person
        person_id = person.id
        name = person.name

        if person_id not in person_memory:
            person_memory[person_id] = {
                "name": name,
                "last_side": current_side,
                "last_event_time": 0,
                "entry_count": 0,
                "exit_count": 0
            }

            print(f"[{now_str}] 🆕 Detected → {name}")
            continue

        prev_side = person_memory[person_id]["last_side"]
        last_event_time = person_memory[person_id]["last_event_time"]

        if prev_side != current_side:

            if current_time - last_event_time > EVENT_COOLDOWN:

                if prev_side == "inside" and current_side == "outside":
                    person_memory[person_id]["exit_count"] += 1
                    print(f"[{now_str}] 🚪 EXIT → {name}")

                elif prev_side == "outside" and current_side == "inside":
                    person_memory[person_id]["entry_count"] += 1
                    print(f"[{now_str}] 🏢 ENTRY → {name}")

                person_memory[person_id]["last_event_time"] = current_time

        person_memory[person_id]["last_side"] = current_side


def compute_counts():
    inside = sum(1 for p in person_memory.values() if p["last_side"] == "inside")
    outside = sum(1 for p in person_memory.values() if p["last_side"] == "outside")
    return inside, outside


def run_camera():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Cannot open camera")
        return

    print("🚀 Live Recognition Started | Press 'q' to quit")

    last_api_call = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (640, 480))

        current_time = time.time()
        centroid_y = detect_face_y(frame)

        if current_time - last_api_call > API_COOLDOWN:
            results = search_frame(frame)
            update_logic(results, centroid_y)
            last_api_call = current_time

        inside_count, outside_count = compute_counts()

        # ✅ Draw divider line
        cv2.line(frame, (0, LINE_Y), (640, LINE_Y), (0, 0, 255), 2)

        # ✅ Date & Time
        now_text = datetime.now().strftime("%d %b %Y | %H:%M:%S")
        cv2.putText(frame, now_text, (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # ✅ Totals
        cv2.putText(frame, f"Inside: {inside_count}", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.putText(frame, f"Outside: {outside_count}", (10, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)

        # ✅ Per-person counters
        y_offset = 110

        for data in person_memory.values():

            label = f'{data["name"]} | IN: {data["entry_count"]} OUT: {data["exit_count"]}'

            cv2.putText(frame, label, (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            y_offset += 25

        cv2.imshow("Office Entry/Exit System", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_camera()
