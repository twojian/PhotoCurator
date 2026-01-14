from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class StatusPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        title = QLabel("System Status")
        title.setStyleSheet("font-weight: bold;")

        self.total_label = QLabel("Total: 0")
        self.pending_label = QLabel("Pending: 0")
        self.running_label = QLabel("Running: 0")
        self.done_label = QLabel("Done: 0")

        layout.addWidget(title)
        layout.addWidget(self.total_label)
        layout.addWidget(self.pending_label)
        layout.addWidget(self.running_label)
        layout.addWidget(self.done_label)
        layout.addStretch()

    def update_counts(self, total, pending, running, done):
        self.total_label.setText(f"Total: {total}")
        self.pending_label.setText(f"Pending: {pending}")
        self.running_label.setText(f"Running: {running}")
        self.done_label.setText(f"Done: {done}")
        self.update()  # 强制刷新