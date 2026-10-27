"""macOS launcher and isolated legacy GUI entry point."""
import os
import sys
import runpy
import subprocess
from pathlib import Path

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
BIN = ROOT / 'bin'

def configure_runtime():
    os.environ['PATH'] = str(BIN) + os.pathsep + os.environ.get('PATH', '')
    os.environ.setdefault('CLUSTERARCH_RESOURCE_DIR', str(ROOT))
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))


def run_legacy():
    configure_runtime()
    # Some legacy code expects resources relative to the current directory.
    # The app bundle is read-only; work products should be written to user folders.
    runpy.run_module('main', run_name='__main__')


def main():
    configure_runtime()
    if '--legacy-ui' in sys.argv:
        sys.argv = [sys.argv[0]]
        run_legacy()
        return
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QTextEdit, QMessageBox
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    w = QWidget()
    w.setWindowTitle('clusterArch — Analysis Workspace')
    w.resize(740, 440)
    w.setStyleSheet('QWidget {background:#f4f6fa;color:#15253b;font-size:14px;} QPushButton {background:#1768c1;color:white;border:0;border-radius:7px;padding:12px;} QTextEdit {background:white;border:1px solid #d6dfec;border-radius:7px;}')
    layout = QVBoxLayout(w)
    title = QLabel('clusterArch')
    title.setStyleSheet('font-size:32px;font-weight:bold;')
    layout.addWidget(title)
    layout.addWidget(QLabel('Biosynthetic gene cluster discovery and analysis'))
    folder = [Path.home() / 'Documents']
    status = QTextEdit()
    status.setReadOnly(True)
    def choose():
        p = QFileDialog.getExistingDirectory(w, 'Select working directory', str(folder[0]))
        if p:
            folder[0] = Path(p)
            status.append('Workspace: ' + p)
    def launch():
        try:
            # Separate process avoids double QApplication initialization.
            args = [sys.executable, '--legacy-ui'] if getattr(sys, 'frozen', False) else [sys.executable, str(Path(__file__).resolve()), '--legacy-ui']
            env = dict(os.environ)
            env['CLUSTERARCH_WORKSPACE'] = str(folder[0])
            subprocess.Popen(args, cwd=str(folder[0]), env=env)
            status.append('Started original clusterArch analysis interface.')
        except Exception as e:
            QMessageBox.critical(w, 'Launch failed', str(e))
    open_button = QPushButton('Open analysis interface')
    open_button.clicked.connect(launch)
    layout.addWidget(open_button)
    folder_button = QPushButton('Choose workspace folder')
    folder_button.clicked.connect(choose)
    layout.addWidget(folder_button)
    layout.addWidget(status)
    status.append('Bundled command-line tools are available through the application PATH.')
    status.append('Workspace: ' + str(folder[0]))
    w.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
