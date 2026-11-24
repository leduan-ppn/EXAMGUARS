"""EXAMGUARS application entry point."""

import sqlite3
import sys
from urllib.parse import parse_qs, urlparse
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from core.configuration import PROJECT_ROOT
from interface.launcher import LauncherWindow
from services.database import DatabaseService
from services.logger import get_logger

logger = get_logger("application")


def resource_path(relative_path: str) -> Path:
    """Resolve bundled resources for both source and PyInstaller builds."""
    bundle_root = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
    return bundle_root / relative_path


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("EXAMGUARS")
    app.setOrganizationName("EXAMGUARS")

    icon_path = resource_path("assets/icon.ico")
    if icon_path.is_file() and icon_path.stat().st_size:
        app.setWindowIcon(QIcon(str(icon_path)))
    stylesheet = resource_path("assets/styles/main.qss")
    try:
        if stylesheet.is_file():
            app.setStyleSheet(stylesheet.read_text(encoding="utf-8"))
        database = DatabaseService()
    except (OSError, sqlite3.Error) as exc:
        logger.exception("Không thể khởi tạo ứng dụng")
        QMessageBox.critical(None, "Lỗi khởi động", str(exc))
        return 1
    launch_server = ""
    launch_grant_id = ""
    launch_grant_secret = ""
    for argument in sys.argv[1:]:
        if argument.startswith("examguars://launch/"):
            parsed = urlparse(argument)
            launch_grant_id = parsed.path.strip("/")
            launch_server = parse_qs(parsed.query).get("server", [""])[0]
            launch_grant_secret = parse_qs(parsed.query).get("secret", [""])[0]
            break
    launcher = LauncherWindow(
        database,
        launch_server=launch_server,
        launch_grant_id=launch_grant_id,
        launch_grant_secret=launch_grant_secret,
    )
    launcher.show()
    logger.info("EXAMGUARS 1.0 khởi động")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())