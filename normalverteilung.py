import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


# Globale Standardparameter
N = 5
MU = 0.0
SIGMA = 1.0
ITERATIONS = 100
DELAY_MS = 450
BINS = 15
SEED = None


class NormalDistributionAnimation:
    def __init__(
        self,
        master,
        n=6,
        iterations=100,
        mu=0.0,
        sigma=1.0,
        delay_ms=400,
        bins=15,
        seed=None,
    ):
        self.master = master
        self.master.title("Normalverteilung und Stichprobenmittel")
        self.master.geometry("1100x750")

        self.n = n
        self.iterations = iterations
        self.mu = mu
        self.sigma = sigma
        self.delay_ms = delay_ms
        self.bins = bins
        self.rng = np.random.default_rng(seed)

        self.current_iteration = 0
        self.sample_means = []
        self.after_id = None
        self.waiting_for_click = False
        self.finished = False

        self._build_gui()
        self._draw_static_elements()
        self.start_animation()

    def _build_gui(self):
        root_frame = ttk.Frame(self.master, padding=10)
        root_frame.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(root_frame)
        control_frame.pack(fill=tk.X, pady=(0, 8))

        self.info_var = tk.StringVar(
            value="Initialisierung ..."
        )
        self.status_var = tk.StringVar(
            value=""
        )

        ttk.Label(
            control_frame,
            textvariable=self.info_var,
            font=("Arial", 11, "bold"),
        ).pack(side=tk.LEFT)

        ttk.Label(
            control_frame,
            textvariable=self.status_var,
            foreground="#8B0000",
            font=("Arial", 10),
        ).pack(side=tk.RIGHT)

        fig = Figure(figsize=(11, 7), dpi=100)
        gs = fig.add_gridspec(2, 1, height_ratios=[2, 1])
        self.ax_top = fig.add_subplot(gs[0])
        self.ax_bottom = fig.add_subplot(gs[1])
        fig.tight_layout(pad=3.0)

        self.canvas = FigureCanvasTkAgg(fig, master=root_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.fig = fig
        self.canvas_widget.bind("<Button-1>", self._on_click)

    def _draw_static_elements(self):
        self.x = np.linspace(self.mu - 4 * self.sigma, self.mu + 4 * self.sigma, 600)
        self.pdf = (
            1.0 / (self.sigma * np.sqrt(2 * np.pi))
            * np.exp(-0.5 * ((self.x - self.mu) / self.sigma) ** 2)
        )

        self.ax_top.clear()
        self.ax_top.plot(self.x, self.pdf, linewidth=2.2, label="Normalverteilung")
        self.ax_top.set_title("Normalverteilung und Histogramm der bisherigen Stichprobenmittelwerte")
        self.ax_top.set_xlabel("x")
        self.ax_top.set_ylabel("Dichte")
        self.ax_top.grid(True, alpha=0.3)
        self.ax_top.set_xlim(self.mu - 4 * self.sigma, self.mu + 4 * self.sigma)
        y_max = 1.05 * np.max(self.pdf)
        self.ax_top.set_ylim(0, y_max)

        self.ax_bottom.clear()
        self.ax_bottom.set_title(f"Aktuelle Stichprobe (n={self.n}, blau) und ihr Mittelwert (orange)")
        self.ax_bottom.set_xlabel("x")
        self.ax_bottom.set_yticks([])
        self.ax_bottom.set_xlim(self.mu - 4 * self.sigma, self.mu + 4 * self.sigma)
        self.ax_bottom.set_ylim(-1.0, 1.0)
        self.ax_bottom.grid(True, axis="x", alpha=0.3)

        self.canvas.draw_idle()

    def start_animation(self):
        self.info_var.set(
            f"Starte Animation: n={self.n}, Iterationen={self.iterations}, μ={self.mu:.2f}, σ={self.sigma:.2f}"
        )
        self.status_var.set("")
        self._run_next_iteration()

    def _run_next_iteration(self):
        if self.finished or self.waiting_for_click:
            return

        if self.current_iteration >= self.iterations:
            self.finished = True
            self.info_var.set(
                f"Fertig. {self.iterations} Iterationen abgeschlossen."
            )
            self.status_var.set("Animation beendet.")
            return

        sample = self.rng.normal(loc=self.mu, scale=self.sigma, size=self.n)
        sample_mean = float(np.mean(sample))
        self.sample_means.append(sample_mean)
        self.current_iteration += 1

        self._update_plots(sample, sample_mean)

        if self.current_iteration == 1:
            self.waiting_for_click = True
            self.status_var.set("Pause nach Iteration 1: Bitte in das Fenster klicken, um fortzusetzen.")
            return

        self.after_id = self.master.after(self.delay_ms, self._run_next_iteration)

    def _update_plots(self, sample, sample_mean):
        self.ax_top.clear()
        self.ax_top.plot(self.x, self.pdf, linewidth=2.2, label="Normalverteilung")

        hist_bins = min(self.bins, max(5, len(self.sample_means)))
        self.ax_top.hist(
            self.sample_means,
            bins=hist_bins,
            density=True,
            alpha=0.45,
            label="Histogramm der Mittelwerte",
        )

        mean_sigma = self.sigma / np.sqrt(self.n)
        mean_pdf = (
            1.0 / (mean_sigma * np.sqrt(2 * np.pi))
            * np.exp(-0.5 * ((self.x - self.mu) / mean_sigma) ** 2)
        )
        self.ax_top.plot(
            self.x,
            mean_pdf,
            linestyle="--",
            linewidth=1.8,
            label="Theorie für Mittelwerte",
        )

        self.ax_top.axvline(sample_mean, linestyle=":", linewidth=2, label="Aktueller Mittelwert")
        self.ax_top.set_title(rf"Normalverteilung ($\mu={MU},\sigma={SIGMA}$) und Histogramm der bisherigen Stichprobenmittelwerte")
        self.ax_top.set_xlabel("x")
        self.ax_top.set_ylabel("Dichte")
        self.ax_top.grid(True, alpha=0.3)
        self.ax_top.set_xlim(self.mu - 4 * self.sigma, self.mu + 4 * self.sigma)
        base_max = np.max(self.pdf)
        mean_max = np.max(mean_pdf)
        y_max = 1.05 * max(base_max, mean_max)
        self.ax_top.set_ylim(0, y_max)
        self.ax_top.legend(loc="upper right")

        self.ax_bottom.clear()
        self.ax_bottom.set_title(f"Aktuelle Stichprobe (n={self.n}, blau) und ihr Mittelwert (orange)")

        # Die Stichprobe stammt direkt aus derselben Normalverteilung wie oben.
        # Zur besseren Sichtbarkeit erhalten die Punkte eine kleine feste vertikale Staffelung.
        y_positions = np.linspace(0.18, 0.18, len(sample))
        self.ax_bottom.scatter(sample, y_positions, s=70, label="Zufallswerte")
        self.ax_bottom.scatter([sample_mean], [0.18], s=180, marker="D", label="Mittelwert")

        self.ax_bottom.set_xlabel("x")
        self.ax_bottom.set_yticks([])
        self.ax_bottom.set_xlim(self.mu - 4 * self.sigma, self.mu + 4 * self.sigma)
        self.ax_bottom.set_ylim(0.0, 0.38)
        self.ax_bottom.grid(True, axis="x", alpha=0.3)
        self.ax_bottom.legend(loc="upper right")

        self.info_var.set(
            f"Iteration {self.current_iteration}/{self.iterations} | "
            #f"Stichprobe: {np.array2string(sample, precision=3, separator=', ')} | "
            f"Mittelwert: {sample_mean:.3f}"
        )

        self.canvas.draw_idle()

    def _on_click(self, _event):
        if self.waiting_for_click and not self.finished:
            self.waiting_for_click = False
            self.status_var.set("Fortsetzung der Animation ...")
            self.after_id = self.master.after(self.delay_ms, self._run_next_iteration)

    def stop(self):
        if self.after_id is not None:
            self.master.after_cancel(self.after_id)
            self.after_id = None


def main():
    root = tk.Tk()
    app = NormalDistributionAnimation(
        root,
        n=N,
        iterations=ITERATIONS,
        mu=MU,
        sigma=SIGMA,
        delay_ms=DELAY_MS,
        bins=BINS,
        seed=SEED,
    )

    def on_close():
        app.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
