import random
import sys
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtCore import QElapsedTimer, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class CellType(Enum):
    EMPTY = 0
    OBSTACLE = 1
    DIRT = 2


@dataclass
class VacuumAgent:
    x: int
    y: int
    dx: int
    dy: int


class VacuumWorld:
    def __init__(
        self,
        cols: int,
        rows: int,
        obstacle_ratio: float = 0.12,
        dirt_ratio: float = 0.18,
    ):
        self.cols = cols
        self.rows = rows
        self.grid = [[CellType.EMPTY for _ in range(cols)] for _ in range(rows)]
        self.obstacle_ratio = obstacle_ratio
        self.dirt_ratio = dirt_ratio

        self.agent = self._place_agent()
        self._place_obstacles()
        self._place_dirt()

    def _place_agent(self) -> VacuumAgent:
        # Spawn the vacuum in a random valid position.
        return VacuumAgent(
            x=random.randint(0, self.cols - 1),
            y=random.randint(0, self.rows - 1),
            dx=1,
            dy=0,
        )

    def _place_obstacles(self) -> None:
        obstacle_count = int(self.cols * self.rows * self.obstacle_ratio)
        placed = 0

        while placed < obstacle_count:
            x = random.randint(0, self.cols - 1)
            y = random.randint(0, self.rows - 1)

            # Never place an obstacle on top of the agent.
            if x == self.agent.x and y == self.agent.y:
                continue

            if self.grid[y][x] == CellType.EMPTY:
                self.grid[y][x] = CellType.OBSTACLE
                placed += 1

    def _place_dirt(self) -> None:
        dirt_count = int(self.cols * self.rows * self.dirt_ratio)
        placed = 0

        while placed < dirt_count:
            x = random.randint(0, self.cols - 1)
            y = random.randint(0, self.rows - 1)

            # Dirt can only be placed on free cells.
            if self.grid[y][x] == CellType.EMPTY and not (x == self.agent.x and y == self.agent.y):
                self.grid[y][x] = CellType.DIRT
                placed += 1

    def dirt_left(self) -> int:
        return sum(cell == CellType.DIRT for row in self.grid for cell in row)

    def _is_blocked(self, x: int, y: int) -> bool:
        # Cells outside the map are treated as blocked walls.
        if x < 0 or x >= self.cols or y < 0 or y >= self.rows:
            return True
        return self.grid[y][x] == CellType.OBSTACLE

    def _choose_new_direction(self) -> tuple[int, int]:
        # Candidate directions include cardinal and diagonal options.
        directions = [
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
        ]

        # Prioritize small random turns around current heading.
        random.shuffle(directions)
        for ndx, ndy in directions:
            nx = self.agent.x + ndx
            ny = self.agent.y + ndy
            if not self._is_blocked(nx, ny):
                return ndx, ndy

        # If all nearby options are blocked, keep current heading.
        return self.agent.dx, self.agent.dy

    def step(self) -> float:
        # Returns traveled distance in meters for this reflex cycle.
        traveled_meters = 0.0

        # Reflex rule 1: if current cell has dirt, clean it immediately.
        if self.grid[self.agent.y][self.agent.x] == CellType.DIRT:
            self.grid[self.agent.y][self.agent.x] = CellType.EMPTY

        nx = self.agent.x + self.agent.dx
        ny = self.agent.y + self.agent.dy

        # Reflex rule 2: if obstacle ahead, back off one cell and turn.
        if self._is_blocked(nx, ny):
            back_x = self.agent.x - self.agent.dx
            back_y = self.agent.y - self.agent.dy

            if not self._is_blocked(back_x, back_y):
                self.agent.x = back_x
                self.agent.y = back_y
                traveled_meters = ((self.agent.dx ** 2 + self.agent.dy ** 2) ** 0.5)

            self.agent.dx, self.agent.dy = self._choose_new_direction()
            return traveled_meters

        # Reflex rule 3: otherwise continue moving forward.
        self.agent.x = nx
        self.agent.y = ny
        traveled_meters = ((self.agent.dx ** 2 + self.agent.dy ** 2) ** 0.5)
        return traveled_meters


class WorldWidget(QWidget):
    def __init__(self, world: VacuumWorld, cell_size: int = 28):
        super().__init__()
        self.world = world
        self.cell_size = cell_size
        self.setMinimumSize(world.cols * cell_size, world.rows * cell_size)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dark palette with strong contrast for map readability.
        bg_color = QColor("#0f172a")
        obstacle_color = QColor("#475569")
        dirt_color = QColor("#22c55e")
        agent_color = QColor("#60a5fa")
        grid_color = QColor("#1e293b")

        painter.fillRect(self.rect(), bg_color)

        for row in range(self.world.rows):
            for col in range(self.world.cols):
                x = col * self.cell_size
                y = row * self.cell_size
                cell = self.world.grid[row][col]

                if cell == CellType.OBSTACLE:
                    painter.fillRect(x, y, self.cell_size, self.cell_size, obstacle_color)
                elif cell == CellType.DIRT:
                    # Dirt is shown as a centered small circle.
                    radius = self.cell_size * 0.36
                    offset = (self.cell_size - radius) / 2
                    painter.setBrush(dirt_color)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(QRectF(x + offset, y + offset, radius, radius))

                painter.setPen(QPen(grid_color, 1))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(x, y, self.cell_size, self.cell_size)

        # Draw the vacuum robot as a circle with a small direction indicator.
        agent_cx = self.world.agent.x * self.cell_size + self.cell_size / 2
        agent_cy = self.world.agent.y * self.cell_size + self.cell_size / 2
        agent_radius = self.cell_size * 0.38

        painter.setBrush(agent_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            QRectF(
                agent_cx - agent_radius,
                agent_cy - agent_radius,
                2 * agent_radius,
                2 * agent_radius,
            )
        )

        # Direction indicator line to visualize current heading.
        painter.setPen(QPen(QColor("white"), 2))
        head_x = agent_cx + self.world.agent.dx * (agent_radius * 0.8)
        head_y = agent_cy + self.world.agent.dy * (agent_radius * 0.8)
        painter.drawLine(int(agent_cx), int(agent_cy), int(head_x), int(head_y))


class RealSpeedDialog(QDialog):
    """Dialog shown at the end to translate simulation results to real vacuum time."""

    def __init__(self, total_distance_cm: float, sim_seconds: float, parent=None):
        super().__init__(parent)
        self.total_distance_cm = total_distance_cm
        self.sim_seconds = sim_seconds

        self.setWindowTitle("Translate to your vacuum's speed")
        self.setMinimumWidth(420)

        info_label = QLabel(
            f"The simulation finished in <b>{sim_seconds:.2f} s</b> "
            f"covering a total distance of <b>{total_distance_cm / 100:.2f} m</b>.<br><br>"
            "Enter your real vacuum's speed to find out how long it would actually take:"
        )
        info_label.setWordWrap(True)

        self.real_speed_input = QDoubleSpinBox()
        self.real_speed_input.setRange(1.0, 100000000000.0)
        self.real_speed_input.setSingleStep(10.0)
        self.real_speed_input.setDecimals(1)
        self.real_speed_input.setValue(30.0)
        self.real_speed_input.setSuffix(" cm/s")

        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("font-size: 14px; font-weight: 600; padding-top: 8px;")

        self.real_speed_input.valueChanged.connect(self._update_result)

        form = QFormLayout()
        form.addRow("Your vacuum's speed:", self.real_speed_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(info_label)
        layout.addLayout(form)
        layout.addWidget(self.result_label)
        layout.addWidget(buttons)

        self._update_result(self.real_speed_input.value())

    def _update_result(self, speed: float) -> None:
        real_seconds = self.total_distance_cm / speed
        real_minutes = real_seconds / 60
        real_hours = real_minutes / 60

        if real_hours >= 1:
            time_str = f"{real_hours:.2f} hours ({real_minutes:.1f} minutes)"
        elif real_minutes >= 1:
            time_str = f"{real_minutes:.2f} minutes ({real_seconds:.1f} seconds)"
        else:
            time_str = f"{real_seconds:.2f} seconds"

        self.result_label.setText(
            f"At {speed:.1f} cm/s your real vacuum would take: {time_str}"
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Reactive Vacuum Agent (Simple Reflex Agent)")
        self.cm_per_cell = 100.0
        self.minimum_tick_interval_ms = 30
        self.default_speed_cm_s = 120.0
        self.tick_interval_ms = self._tick_interval_from_speed(self.default_speed_cm_s)

        self.world = VacuumWorld(cols=24, rows=24)
        self.world_widget = WorldWidget(self.world, cell_size=32)
        self.world_widget.setStyleSheet("background-color: #0f172a;")

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 15px; font-weight: 600; padding: 8px;")

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self._toggle_play_pause)
        self.regenerate_button = QPushButton("Regenerate")
        self.regenerate_button.clicked.connect(self._regenerate_world)

        self.speed_label = QLabel("Vacuum speed (cm/s):")
        self.speed_input = QDoubleSpinBox()
        self.speed_input.setRange(1.0, 100000000000.0)
        self.speed_input.setSingleStep(10.0)
        self.speed_input.setDecimals(1)
        self.speed_input.setValue(self.default_speed_cm_s)
        self.speed_input.valueChanged.connect(self._on_speed_changed)

        self.grid_size_label = QLabel("Grid size (N×N):")
        self.grid_size_input = QSpinBox()
        self.grid_size_input.setRange(4, 64)
        self.grid_size_input.setSingleStep(1)
        self.grid_size_input.setValue(24)

        controls_layout = QHBoxLayout()
        controls_layout.addStretch()
        controls_layout.addWidget(self.grid_size_label)
        controls_layout.addWidget(self.grid_size_input)
        controls_layout.addWidget(self.speed_label)
        controls_layout.addWidget(self.speed_input)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.regenerate_button)
        controls_layout.addStretch()

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.world_widget)
        layout.addLayout(controls_layout)
        layout.addWidget(self.status_label)
        self.setCentralWidget(central)
        self._apply_dark_theme()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

        # Track active running time only (excluding pauses).
        self.run_time_ms = 0
        self.run_segment_timer = QElapsedTimer()
        self.is_running = False
        self.is_finished = False
        self.total_distance_cm = 0.0

        self._update_status()

    def _apply_dark_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background-color: #020617;
                color: #e2e8f0;
            }
            QLabel {
                color: #e2e8f0;
            }
            QPushButton {
                background-color: #1d4ed8;
                color: #f8fafc;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
            QDoubleSpinBox {
                background-color: #0f172a;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px 8px;
                min-width: 90px;
            }
            QSpinBox {
                background-color: #0f172a;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px 8px;
                min-width: 60px;
            }
            """
        )

    def _tick_interval_from_speed(self, speed_cm_s: float) -> int:
        # One movement cycle is modeled as one cell (1 meter = 100 centimeters).
        ideal_ms = (self.cm_per_cell / speed_cm_s) * 1000
        return max(self.minimum_tick_interval_ms, int(ideal_ms))

    def _on_speed_changed(self, value: float) -> None:
        self.tick_interval_ms = self._tick_interval_from_speed(value)
        if self.is_running:
            self.timer.start(self.tick_interval_ms)
        self._update_status()

    def _elapsed_seconds(self) -> float:
        if self.is_running:
            return (self.run_time_ms + self.run_segment_timer.elapsed()) / 1000
        return self.run_time_ms / 1000

    def _toggle_play_pause(self) -> None:
        if self.is_finished:
            return

        if self.is_running:
            self.run_time_ms += self.run_segment_timer.elapsed()
            self.is_running = False
            self.timer.stop()
            self.play_button.setText("Play")
            self._update_status()
            return

        self.is_running = True
        self.run_segment_timer.start()
        self.timer.start(self.tick_interval_ms)
        self.play_button.setText("Pause")

    def _regenerate_world(self) -> None:
        self.timer.stop()
        self.is_running = False
        self.is_finished = False
        self.run_time_ms = 0
        self.total_distance_cm = 0.0
        self.play_button.setText("Play")
        self.play_button.setEnabled(True)

        n = self.grid_size_input.value()
        self.world = VacuumWorld(cols=n, rows=n)
        self.world_widget.world = self.world
        self.world_widget.setMinimumSize(n * self.world_widget.cell_size, n * self.world_widget.cell_size)
        self.world_widget.update()
        self.adjustSize()
        self._update_status()

    def _update_status(self) -> None:
        elapsed_seconds = self._elapsed_seconds()
        dirt_left = self.world.dirt_left()
        state = "Running" if self.is_running else "Paused"
        speed = self.speed_input.value()
        self.status_label.setText(
            f"State: {state} | Time: {elapsed_seconds:0.1f} s | Dirt left: {dirt_left} | Speed: {speed:0.1f} cm/s"
        )

    def _tick(self) -> None:
        if self.world.dirt_left() == 0:
            self.run_time_ms += self.run_segment_timer.elapsed()
            self.is_running = False
            self.is_finished = True
            self.timer.stop()
            self.play_button.setText("Play")
            self.play_button.setEnabled(False)
            elapsed_seconds = self._elapsed_seconds()
            speed_cm_s = self.speed_input.value()
            self.status_label.setText(
                f"Done in {elapsed_seconds:.1f} s (simulation) | "
                f"Distance: {self.total_distance_cm / 100:.2f} m | Speed: {speed_cm_s:.1f} cm/s"
            )
            dialog = RealSpeedDialog(self.total_distance_cm, elapsed_seconds, parent=self)
            dialog.exec()
            return

        traveled_meters = self.world.step()
        self.total_distance_cm += traveled_meters * self.cm_per_cell
        self.world_widget.update()
        self._update_status()


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
