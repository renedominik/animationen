import tkinter as tk
import time
import queue
import threading

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


schema = [
    [10, 1, ["Ein", "2", "3", "4", "Halten", "2", "3", "4", "Aus", "2", "3", "4", "Halten", "2", "3", "4"]],
    [1, 30, ["Halten", "30"]],
]

WINDOW_TITLE = "Atemschema"
WINDOW_SIZE = "800x800"

BG_COLOR = "white"
TEXT_COLOR = "black"
FACE_FILL = "#FFD54F"
FACE_OUTLINE = "black"

MIN_RADIUS = 70
MAX_RADIUS = 240

ANIMATION_FPS = 60
ANIMATION_INTERVAL_MS = int(1000 / ANIMATION_FPS)


def classify_keyword(token: str):
    token = str(token).strip()
    if token == "Ein":
        return "grow"
    if token == "Aus":
        return "shrink"
    if token == "Halten":
        return "hold"
    return None


def parse_phase_items(items):
    """
    Aus:
      ["Ein","2","3","4","Halten","2","3","4","Aus","2","3","4"]
    wird:
      [
        {"phase":"grow", "texts":["Ein","2","3","4"]},
        {"phase":"hold", "texts":["Halten","2","3","4"]},
        {"phase":"shrink", "texts":["Aus","2","3","4"]},
      ]
    """
    phases = []
    i = 0

    while i < len(items):
        token = str(items[i]).strip()
        phase = classify_keyword(token)

        if phase is None:
            phases.append({
                "phase": "hold",
                "texts": [token],
            })
            i += 1
            continue

        texts = [token]
        j = i + 1
        while j < len(items) and classify_keyword(items[j]) is None:
            texts.append(str(items[j]).strip())
            j += 1

        phases.append({
            "phase": phase,
            "texts": texts,
        })
        i = j

    return phases


def compile_schema(schema_definition):
    """
    Ergebnis:
      Liste von Phasen mit
      - phase
      - texts
      - step_duration
      - total_duration
    """
    compiled = []

    for block in schema_definition:
        if not isinstance(block, list) or len(block) != 3:
            raise ValueError(f"Ungültiger Block: {block}")

        repeat_count, step_duration, items = block

        if not isinstance(repeat_count, int) or repeat_count < 1:
            raise ValueError(f"Wiederholungen müssen int >= 1 sein: {block}")
        if not isinstance(step_duration, (int, float)) or step_duration <= 0:
            raise ValueError(f"Schrittdauer muss > 0 sein: {block}")
        if not isinstance(items, list) or not items:
            raise ValueError(f"Items müssen eine nichtleere Liste sein: {block}")

        block_phases = parse_phase_items(items)

        for _ in range(repeat_count):
            for ph in block_phases:
                compiled.append({
                    "phase": ph["phase"],
                    "texts": ph["texts"],
                    "step_duration": float(step_duration),
                    "total_duration": float(step_duration) * len(ph["texts"]),
                })

    return compiled


def speech_worker(q: queue.Queue):
    """
    Robuste serielle Sprachausgabe.
    Kein clear(), kein stop() pro Wort.
    """
    if pyttsx3 is None:
        while True:
            item = q.get()
            if item is None:
                break
        return

    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 160)
        voices = engine.getProperty("voices")
        if voices:
            engine.setProperty("voice", voices[0].id)

        while True:
            text = q.get()
            if text is None:
                break
            try:
                engine.say(str(text))
                engine.runAndWait()
            except Exception as e:
                print("Sprachfehler:", repr(e))
    except Exception as e:
        print("Fehler beim Initialisieren von pyttsx3:", repr(e))


class AtemApp:
    def __init__(self, root, compiled_phases):
        self.root = root
        self.phases = compiled_phases
        self.phase_index = 0

        self.current_radius = MIN_RADIUS

        self.anim_after_id = None
        self.next_phase_after_id = None
        self.text_after_ids = []

        self.phase_start_time = None
        self.phase_start_radius = MIN_RADIUS
        self.phase_end_radius = MIN_RADIUS
        self.phase_duration = 0.0

        self.speech_queue = queue.Queue()
        self.speech_thread = threading.Thread(
            target=speech_worker,
            args=(self.speech_queue,),
            daemon=True,
        )
        self.speech_thread.start()

        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.configure(bg=BG_COLOR)

        self.label = tk.Label(
            root,
            text="Bereit",
            font=("Arial", 36, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR
        )
        self.label.pack(pady=20)

        self.canvas = tk.Canvas(
            root,
            width=700,
            height=560,
            bg=BG_COLOR,
            highlightthickness=0
        )
        self.canvas.pack(expand=True, fill="both")

        self.info_label = tk.Label(
            root,
            text="",
            font=("Arial", 14),
            bg=BG_COLOR,
            fg="gray30"
        )
        self.info_label.pack(pady=10)

        self.root.update()

        self.cx = self.canvas.winfo_width() / 2
        self.cy = self.canvas.winfo_height() / 2

        self.create_smiley()
        self.update_smiley(self.current_radius)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_smiley(self):
        r = self.current_radius

        self.face_id = self.canvas.create_oval(
            self.cx - r, self.cy - r,
            self.cx + r, self.cy + r,
            fill=FACE_FILL,
            outline=FACE_OUTLINE,
            width=max(2, int(r * 0.03))
        )

        self.left_eye_id = self.canvas.create_oval(0, 0, 1, 1, fill="black", outline="black")
        self.right_eye_id = self.canvas.create_oval(0, 0, 1, 1, fill="black", outline="black")

        self.mouth_id = self.canvas.create_arc(
            0, 0, 1, 1,
            start=200,
            extent=140,
            style=tk.ARC,
            outline="black",
            width=max(3, int(r * 0.045))
        )

    def update_smiley(self, radius):
        cx, cy = self.cx, self.cy

        self.canvas.coords(
            self.face_id,
            cx - radius, cy - radius,
            cx + radius, cy + radius
        )
        self.canvas.itemconfig(
            self.face_id,
            width=max(2, int(radius * 0.03))
        )

        eye_r = radius * 0.09
        eye_dx = radius * 0.35
        eye_y = cy - radius * 0.22

        left_ex = cx - eye_dx
        right_ex = cx + eye_dx

        self.canvas.coords(
            self.left_eye_id,
            left_ex - eye_r, eye_y - eye_r,
            left_ex + eye_r, eye_y + eye_r
        )
        self.canvas.coords(
            self.right_eye_id,
            right_ex - eye_r, eye_y - eye_r,
            right_ex + eye_r, eye_y + eye_r
        )

        mouth_w = radius * 0.95
        mouth_h = radius * 0.60
        mx1 = cx - mouth_w / 2
        my1 = cy - mouth_h / 2 + radius * 0.18
        mx2 = cx + mouth_w / 2
        my2 = cy + mouth_h / 2 + radius * 0.18

        self.canvas.coords(self.mouth_id, mx1, my1, mx2, my2)
        self.canvas.itemconfig(
            self.mouth_id,
            width=max(3, int(radius * 0.045))
        )

    def speak(self, text):
        self.speech_queue.put(str(text))

    def set_text(self, text):
        self.label.config(text=str(text))
        self.speak(text)

    def clear_scheduled_texts(self):
        for after_id in self.text_after_ids:
            try:
                self.root.after_cancel(after_id)
            except Exception:
                pass
        self.text_after_ids.clear()

    def schedule_phase_texts(self, texts, step_duration):
        self.clear_scheduled_texts()

        if not texts:
            return

        self.set_text(texts[0])

        for i, txt in enumerate(texts[1:], start=1):
            after_id = self.root.after(
                int(i * step_duration * 1000),
                lambda t=txt: self.set_text(t)
            )
            self.text_after_ids.append(after_id)

    def phase_target_radius(self, phase_name):
        if phase_name == "grow":
            return MAX_RADIUS
        if phase_name == "shrink":
            return MIN_RADIUS
        return self.current_radius

    def start(self):
        self.start_next_phase()

    def start_next_phase(self):
        self.clear_scheduled_texts()

        if self.phase_index >= len(self.phases):
            self.label.config(text="Fertig")
            self.info_label.config(text="Ablauf abgeschlossen")
            return

        phase = self.phases[self.phase_index]
        self.phase_index += 1

        phase_name = phase["phase"]
        texts = phase["texts"]
        step_duration = phase["step_duration"]
        total_duration = phase["total_duration"]

        self.phase_start_radius = self.current_radius
        self.phase_end_radius = self.phase_target_radius(phase_name)
        self.phase_duration = total_duration
        self.phase_start_time = time.perf_counter()

        self.info_label.config(
            text=(
                f"Phase {self.phase_index} / {len(self.phases)} | "
                f"{phase_name} | {len(texts)} Schritte | "
                f"{step_duration:.2f} s pro Schritt"
            )
        )

        self.schedule_phase_texts(texts, step_duration)
        self.animate_phase()

        self.next_phase_after_id = self.root.after(
            int(total_duration * 1000),
            self.finish_phase
        )

    def animate_phase(self):
        elapsed = time.perf_counter() - self.phase_start_time
        t = min(1.0, elapsed / self.phase_duration if self.phase_duration > 0 else 1.0)

        # harmonische Interpolation
        smooth_t = t * t * (3 - 2 * t)

        radius = self.phase_start_radius + (self.phase_end_radius - self.phase_start_radius) * smooth_t
        self.current_radius = radius
        self.update_smiley(radius)

        if t < 1.0:
            self.anim_after_id = self.root.after(ANIMATION_INTERVAL_MS, self.animate_phase)
        else:
            self.current_radius = self.phase_end_radius
            self.update_smiley(self.current_radius)
            self.anim_after_id = None

    def finish_phase(self):
        self.current_radius = self.phase_end_radius
        self.update_smiley(self.current_radius)
        self.start_next_phase()

    def on_close(self):
        self.clear_scheduled_texts()

        if self.anim_after_id is not None:
            try:
                self.root.after_cancel(self.anim_after_id)
            except Exception:
                pass

        if self.next_phase_after_id is not None:
            try:
                self.root.after_cancel(self.next_phase_after_id)
            except Exception:
                pass

        self.speech_queue.put(None)
        self.root.destroy()


def main():
    compiled_phases = compile_schema(schema)

    root = tk.Tk()
    app = AtemApp(root, compiled_phases)
    root.after(200, app.start)
    root.mainloop()


if __name__ == "__main__":
    main()