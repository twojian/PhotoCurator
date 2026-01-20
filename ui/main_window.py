from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout
from ui.components.gallery import Gallery
from ui.components.status_panel import StatusPanel
from ui.components.tool_panel import ToolPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotoCurator V1.4")

        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)

        self.status_panel = StatusPanel()
        self.gallery = Gallery()
        self.tool_panel = ToolPanel()

        self.status_panel.setFixedWidth(220)
        self.tool_panel.setFixedWidth(260)

        layout.addWidget(self.status_panel)
        layout.addWidget(self.gallery, stretch=1)
        layout.addWidget(self.tool_panel)
