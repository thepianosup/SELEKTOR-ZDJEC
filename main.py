import sys
import os
import shutil
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QGridLayout, QSlider
)
from PyQt6.QtGui import QPixmap, QKeySequence, QShortcut, QTransform, QImage, QImageReader, QPainter, QFont, QColor, QFontMetrics, QPen
from PIL import Image, ExifTags
import datetime
from PyQt6.QtCore import Qt, QRect

STATE_FILE = "state.json"

class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_pixmap = None
        self.date_text = ""
        self.message = "Wybierz foldery, aby rozpocząć.\n\nStrzałka w PRAWO -> skopiuj\nStrzałka w LEWO -> odrzuć\nGÓRA/DÓŁ -> obróć zdjęcie i zapisz\nCMD + Z -> cofnij"
        self.is_dragging = False
        self.is_resizing = False
        self.drag_start_pos = None
        self.start_rel_x = 0
        self.start_rel_y = 0
        self.start_font_size = 0
        self.text_screen_rect = None
        self.resize_screen_rect = None
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
    def set_message(self, msg):
        self.base_pixmap = None
        self.message = msg
        self.update()
        
    def set_image(self, pixmap, date_text):
        self.base_pixmap = pixmap
        self.date_text = date_text
        self.message = ""
        self.update()
        
    def snap_to_corner(self, corner):
        if not self.base_pixmap or not self.date_text: return
        win = self.window()
        base_dim = max(self.base_pixmap.width(), self.base_pixmap.height())
        font_size = max(10, int(base_dim * (win.font_size_pct / 100.0)))
        font = QFont("Arial", font_size, QFont.Weight.Bold)
        fm = QFontMetrics(font)
        text_rect = fm.boundingRect(self.date_text)
        
        margin = int(font_size * 0.8)
        
        if corner == 'TL':
            px = margin
            py = margin + text_rect.height()
        elif corner == 'TR':
            px = self.base_pixmap.width() - text_rect.width() - margin
            py = margin + text_rect.height()
        elif corner == 'BL':
            px = margin
            py = self.base_pixmap.height() - margin
        elif corner == 'BR':
            px = self.base_pixmap.width() - text_rect.width() - margin
            py = self.base_pixmap.height() - margin
            
        win.rel_x = px / self.base_pixmap.width()
        win.rel_y = py / self.base_pixmap.height()
        win.save_state()
        self.update()

    def paintEvent(self, event):
        if not self.base_pixmap:
            painter = QPainter(self)
            painter.setPen(QColor("#888888") if "Wybierz foldery" in self.message else QColor("#ff5555" if "Nie można" in self.message else "#aaffaa"))
            font = QFont("Arial", 20 if "Wybierz foldery" in self.message else 24)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.message)
            pen = QPen(QColor("#444444"), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRoundedRect(1, 1, self.width()-2, self.height()-2, 10, 10)
            painter.end()
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        pixmap_size = self.base_pixmap.size()
        scaled_size = pixmap_size.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        img_x = (self.width() - scaled_size.width()) // 2
        img_y = (self.height() - scaled_size.height()) // 2
        
        painter.drawPixmap(img_x, img_y, scaled_size.width(), scaled_size.height(), self.base_pixmap)
        
        win = self.window()
        if self.date_text and win.current_date_corner:
            sx = img_x + win.rel_x * scaled_size.width()
            sy = img_y + win.rel_y * scaled_size.height()
            
            base_dim = max(scaled_size.width(), scaled_size.height())
            font_size = max(10, int(base_dim * (win.font_size_pct / 100.0)))
            font = QFont("Arial", font_size, QFont.Weight.Bold)
            painter.setFont(font)
            
            fm = painter.fontMetrics()
            text_rect = fm.boundingRect(self.date_text)
            
            painter.setPen(QColor(0, 0, 0, 150))
            painter.drawText(int(sx)+2, int(sy)+2, self.date_text)
            painter.setPen(QColor("white"))
            painter.drawText(int(sx), int(sy), self.date_text)
            
            self.text_screen_rect = QRect(int(sx) + text_rect.x() - 5, int(sy) + text_rect.y() - 5, text_rect.width() + 10, text_rect.height() + 10)
            self.resize_screen_rect = QRect(self.text_screen_rect.right() - 5, self.text_screen_rect.bottom() - 5, 10, 10)
            
            if self.underMouse() and self.text_screen_rect:
                painter.setPen(QPen(QColor(255, 255, 255, 100), 1, Qt.PenStyle.DashLine))
                painter.drawRect(self.text_screen_rect)
                painter.setBrush(QColor(255, 255, 255, 200))
                painter.drawEllipse(self.resize_screen_rect.center(), 4, 4)
        painter.end()
                
    def mousePressEvent(self, event):
        win = self.window()
        if not win.current_date_corner: return
        
        if self.resize_screen_rect and self.resize_screen_rect.contains(event.pos()):
            self.is_resizing = True
            self.drag_start_pos = event.pos()
            self.start_font_size = win.font_size_pct
        elif self.text_screen_rect and self.text_screen_rect.contains(event.pos()):
            self.is_dragging = True
            self.drag_start_pos = event.pos()
            self.start_rel_x = win.rel_x
            self.start_rel_y = win.rel_y
            
    def mouseMoveEvent(self, event):
        win = self.window()
        if self.is_resizing:
            dy = event.pos().y() - self.drag_start_pos.y()
            win.font_size_pct = max(0.5, min(20.0, self.start_font_size + dy * 0.1))
            self.update()
        elif self.is_dragging:
            if not self.base_pixmap: return
            pixmap_size = self.base_pixmap.size()
            scaled_size = pixmap_size.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
            dx = event.pos().x() - self.drag_start_pos.x()
            dy = event.pos().y() - self.drag_start_pos.y()
            
            win.rel_x = self.start_rel_x + dx / scaled_size.width()
            win.rel_y = self.start_rel_y + dy / scaled_size.height()
            self.update()
        else:
            if self.resize_screen_rect and self.resize_screen_rect.contains(event.pos()):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif self.text_screen_rect and self.text_screen_rect.contains(event.pos()):
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()
            
    def mouseReleaseEvent(self, event):
        if self.is_dragging or self.is_resizing:
            self.is_dragging = False
            self.is_resizing = False
            self.window().save_state()
            self.setCursor(Qt.CursorShape.ArrowCursor)

class PhotoSelectorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Selektor Zdjęć")
        self.resize(1000, 800)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")

        self.source_folder = ""
        self.dest_folder = ""
        self.image_files = []
        self.current_image_index = 0

        self.processed_files = set()
        self.history = []

        self.font_size_pct = 2.5
        self.rel_x = 0.02
        self.rel_y = 0.02

        self.load_state()
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Buttons layout
        btn_layout = QHBoxLayout()
        
        self.btn_source = QPushButton("Wybierz folder źródłowy")
        self.btn_source.setStyleSheet(self.btn_style())
        self.btn_source.clicked.connect(self.select_source_folder)
        btn_layout.addWidget(self.btn_source)

        self.btn_dest = QPushButton("Wybierz folder docelowy")
        self.btn_dest.setStyleSheet(self.btn_style())
        self.btn_dest.clicked.connect(self.select_dest_folder)
        btn_layout.addWidget(self.btn_dest)

        self.btn_reset = QPushButton("Resetuj historię")
        self.btn_reset.setStyleSheet(self.btn_style(color="#c0392b"))
        self.btn_reset.clicked.connect(self.reset_state)
        btn_layout.addWidget(self.btn_reset)

        layout.addLayout(btn_layout)

        # Info layout to hold date grid and labels
        info_layout = QHBoxLayout()
        
        # Date position widget (2x2 grid)
        date_pos_layout = QGridLayout()
        date_pos_layout.setSpacing(5)
        
        self.btn_pos_tl = QPushButton()
        self.btn_pos_tr = QPushButton()
        self.btn_pos_bl = QPushButton()
        self.btn_pos_br = QPushButton()
        
        self.pos_buttons = [self.btn_pos_tl, self.btn_pos_tr, self.btn_pos_bl, self.btn_pos_br]
        self.positions = ['TL', 'TR', 'BL', 'BR']
        self.current_date_corner = None
        
        for i, btn in enumerate(self.pos_buttons):
            btn.setFixedSize(30, 30)
            btn.setCheckable(True)
            btn.setStyleSheet(self.pos_btn_style())
            btn.clicked.connect(lambda checked, idx=i: self.set_date_position(idx))
            
        date_pos_layout.addWidget(self.btn_pos_tl, 0, 0)
        date_pos_layout.addWidget(self.btn_pos_tr, 0, 1)
        date_pos_layout.addWidget(self.btn_pos_bl, 1, 0)
        date_pos_layout.addWidget(self.btn_pos_br, 1, 1)
        
        date_widget = QWidget()
        date_widget.setLayout(date_pos_layout)
        date_widget.setFixedSize(80, 80)
        
        info_layout.addWidget(date_widget)
        
        # Labels layout
        labels_layout = QVBoxLayout()
        
        # Labels for current folders
        self.lbl_folders = QLabel("Źródło: Brak\nCel: Brak")
        self.lbl_folders.setStyleSheet("color: #aaaaaa; font-size: 13px; margin-bottom: 5px;")
        self.lbl_folders.setAlignment(Qt.AlignmentFlag.AlignCenter)
        labels_layout.addWidget(self.lbl_folders)

        # Stats label
        self.lbl_stats = QLabel("Dodane: 0 | Odrzucone: 0")
        self.lbl_stats.setStyleSheet("color: #3498db; font-size: 15px; font-weight: bold; margin-bottom: 10px;")
        self.lbl_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        labels_layout.addWidget(self.lbl_stats)

        # Similar label
        self.lbl_similar = QLabel("")
        self.lbl_similar.setStyleSheet("color: white; background-color: #e67e22; font-size: 13px; font-weight: bold; padding: 4px 8px; border-radius: 6px;")
        self.lbl_similar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_similar.hide()
        labels_layout.addWidget(self.lbl_similar)
        
        labels_widget = QWidget()
        labels_widget.setLayout(labels_layout)
        info_layout.addWidget(labels_widget, stretch=1)
        
        # Spacer on right to balance the grid
        right_spacer = QWidget()
        right_spacer.setFixedSize(80, 80)
        info_layout.addWidget(right_spacer)
        
        layout.addLayout(info_layout)

        # Image display
        self.lbl_image = ImageLabel(self)
        self.lbl_image.setMinimumSize(400, 300)
        layout.addWidget(self.lbl_image, stretch=1)

        # Update labels if loaded from state
        self.update_folder_labels()
        if self.source_folder and self.dest_folder:
            self.load_images_from_source()

        # Shortcuts
        self.shortcut_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self.shortcut_right.activated.connect(self.action_move)

        self.shortcut_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.shortcut_left.activated.connect(self.action_reject)

        # In PyQt on macOS, 'Ctrl+Z' handles Cmd+Z native behavior automatically
        self.shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.shortcut_undo.activated.connect(self.action_undo)

        self.shortcut_up = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        self.shortcut_up.activated.connect(self.action_rotate_right)

        self.shortcut_down = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        self.shortcut_down.activated.connect(self.action_rotate_left)

    def btn_style(self, color="#2980b9"):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self.lighten_color(color)};
            }}
        """

    def lighten_color(self, hex_color):
        if hex_color == "#2980b9": return "#3498db"
        if hex_color == "#c0392b": return "#e74c3c"
        return hex_color

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    self.processed_files = set(state.get("processed_files", []))
                    self.history = state.get("history", [])
                    self.source_folder = state.get("last_source_folder", "")
                    self.dest_folder = state.get("last_dest_folder", "")
                    self.font_size_pct = state.get("font_size_pct", 2.5)
                    self.rel_x = state.get("rel_x", 0.02)
                    self.rel_y = state.get("rel_y", 0.02)
                    self.current_date_corner = state.get("current_date_corner", None)
            except Exception as e:
                print("Error loading state:", e)

    def save_state(self):
        state = {
            "processed_files": list(self.processed_files),
            "history": self.history,
            "last_source_folder": self.source_folder,
            "last_dest_folder": self.dest_folder,
            "font_size_pct": getattr(self, "font_size_pct", 2.5),
            "rel_x": getattr(self, "rel_x", 0.02),
            "rel_y": getattr(self, "rel_y", 0.02),
            "current_date_corner": getattr(self, "current_date_corner", None)
        }
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("Error saving state:", e)

    def reset_state(self):
        reply = QMessageBox.question(self, 'Reset', 'Czy na pewno chcesz zresetować historię? Zdjęcia zaczną się pokazywać od nowa.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.processed_files.clear()
            self.history.clear()
            self.save_state()
            self.load_images_from_source()

    def update_folder_labels(self):
        src_text = self.source_folder if self.source_folder else "Brak"
        dst_text = self.dest_folder if self.dest_folder else "Brak"
        self.lbl_folders.setText(f"Źródło: {src_text}\nCel: {dst_text}")
        self.update_stats()

    def update_stats(self):
        added = sum(1 for item in self.history if item.get("action") in ["copied", "moved"])
        rejected = sum(1 for item in self.history if item.get("action") == "rejected")
        left = max(0, len(self.image_files) - self.current_image_index)
        self.lbl_stats.setText(f"Do wyboru: {left} | Dodane: {added} | Odrzucone: {rejected}")
        
        if hasattr(self, 'image_datetimes') and self.current_image_index < len(self.image_files):
            similar_count = 0
            for j in range(self.current_image_index + 1, len(self.image_files)):
                diff = (self.image_datetimes[j] - self.image_datetimes[j-1]).total_seconds()
                if diff <= 30 and diff >= -30:
                    similar_count += 1
                else:
                    break
            if similar_count > 0:
                self.lbl_similar.setText(f"Podobne w kolejce: {similar_count}")
                self.lbl_similar.show()
            else:
                self.lbl_similar.hide()
        elif hasattr(self, 'lbl_similar'):
            self.lbl_similar.hide()

    def select_source_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Wybierz folder źródłowy", self.source_folder)
        if folder:
            self.source_folder = folder
            self.save_state()
            self.load_images_from_source(show_msg=True)
            self.update_folder_labels()

    def select_dest_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Wybierz folder docelowy", self.dest_folder)
        if folder:
            self.dest_folder = folder
            self.save_state()
            self.load_images_from_source(show_msg=True)
            self.update_folder_labels()

    def load_images_from_source(self, show_msg=False):
        if not self.source_folder or not os.path.exists(self.source_folder):
            return

        valid_exts = {".jpg", ".jpeg", ".png", ".heic"}
        self.image_files = []
        
        # Set of file names already in destination
        dest_files = set()
        if self.dest_folder and os.path.exists(self.dest_folder):
            dest_files = set(f for f in os.listdir(self.dest_folder) if not f.startswith('.'))
        
        skipped_count = 0
        files_with_dates = []
        for f in os.listdir(self.source_folder):
            if f.startswith('.'):
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_exts:
                if f in dest_files:
                    skipped_count += 1
                    continue

                full_path = os.path.join(self.source_folder, f)
                if full_path not in self.processed_files:
                    dt = self.get_image_datetime(full_path)
                    files_with_dates.append((full_path, dt))
        
        files_with_dates.sort(key=lambda x: x[1])
        self.image_files = [x[0] for x in files_with_dates]
        self.image_datetimes = [x[1] for x in files_with_dates]
        
        self.current_image_index = 0
        self.update_stats()
        self.show_current_image()

        if show_msg and skipped_count > 0:
            QMessageBox.information(self, "Pominięto zdjęcia", f"Znaleziono {skipped_count} zdjęć, które są już w folderze docelowym.\\nZostały one od razu pominięte w propozycjach.")

    def get_image_datetime(self, image_path):
        try:
            with Image.open(image_path) as img:
                exif = img._getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        if tag == 'DateTimeOriginal':
                            return datetime.datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
        except Exception:
            pass
        
        try:
            mtime = os.path.getmtime(image_path)
            return datetime.datetime.fromtimestamp(mtime)
        except Exception:
            return datetime.datetime.min

    def show_current_image(self):
        if not self.source_folder or not self.dest_folder:
            return

        if self.current_image_index < len(self.image_files):
            img_path = self.image_files[self.current_image_index]
            
            reader = QImageReader(img_path)
            reader.setAutoTransform(True)
            image = reader.read()
            
            if image.isNull():
                self.lbl_image.set_message("Nie można załadować zdjęcia.\nFormat może nie być wspierany (np. HEIC).")
            else:
                pixmap = QPixmap.fromImage(image)
                date_str = self.get_exif_date(img_path) if self.current_date_corner else ""
                self.lbl_image.set_image(pixmap, date_str)
                
            self.setWindowTitle(f"Selektor Zdjęć - {os.path.basename(img_path)}")
        else:
            self.lbl_image.set_message("Brak kolejnych zdjęć do pokazywania")
            self.setWindowTitle("Selektor Zdjęć")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.show_current_image()

    def action_move(self):
        if not self.source_folder or not self.dest_folder:
            return
        if self.current_image_index >= len(self.image_files):
            return

        src_path = self.image_files[self.current_image_index]
        filename = os.path.basename(src_path)
        dest_path = os.path.join(self.dest_folder, filename)

        # Handle duplicate filename in dest folder
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(self.dest_folder, f"{base}_{counter}{ext}")
            counter += 1

        try:
            if self.current_date_corner:
                reader = QImageReader(src_path)
                reader.setAutoTransform(True)
                image = reader.read()
                date_str = self.get_exif_date(src_path)
                image = self.draw_date_on_image(image, date_str)
                image.save(dest_path, quality=100)
            else:
                shutil.copy2(src_path, dest_path)
            
            self.history.append({
                "source_path": src_path,
                "action": "copied",
                "dest_path": dest_path
            })
            self.processed_files.add(src_path)
            self.save_state()
            
            self.current_image_index += 1
            self.update_stats()
            self.show_current_image()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można skopiować pliku:\n{e}")

    def action_reject(self):
        if not self.source_folder or not self.dest_folder:
            return
        if self.current_image_index >= len(self.image_files):
            return

        src_path = self.image_files[self.current_image_index]
        
        self.history.append({
            "source_path": src_path,
            "action": "rejected",
            "dest_path": None
        })
        self.processed_files.add(src_path)
        self.save_state()

        self.current_image_index += 1
        self.update_stats()
        self.show_current_image()

    def action_undo(self):
        if not self.history:
            return

        last_action = self.history.pop()
        src_path = last_action["source_path"]
        action = last_action["action"]
        dest_path = last_action["dest_path"]

        if action == "copied":
            try:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie można cofnąć operacji kopiowania:\n{e}")
                self.history.append(last_action)
                return
        elif action == "moved":
            try:
                if os.path.exists(dest_path):
                    shutil.move(dest_path, src_path)
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie można cofnąć operacji przeniesienia:\n{e}")
                self.history.append(last_action)
                return

        if src_path in self.processed_files:
            self.processed_files.remove(src_path)
        
        self.save_state()
        self.update_stats()
        self.load_images_from_source()

    def action_rotate_right(self):
        self.rotate_current_image(90)

    def action_rotate_left(self):
        self.rotate_current_image(-90)

    def rotate_current_image(self, angle):
        if not self.source_folder or not self.dest_folder:
            return
        if self.current_image_index >= len(self.image_files):
            return

        src_path = self.image_files[self.current_image_index]
        reader = QImageReader(src_path)
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            QMessageBox.warning(self, "Błąd", "Nie można obrócić tego zdjęcia (nieobsługiwany format?).")
            return
        
        transform = QTransform().rotate(angle)
        rotated_image = image.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        rotated_image.save(src_path, quality=100)
        
        self.show_current_image()

    def pos_btn_style(self):
        return """
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 4px;
                color: #aaa;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333;
                border: 1px solid #555;
            }
            QPushButton:checked {
                background-color: #3498db;
                border: 1px solid #2980b9;
                color: white;
            }
        """

    def set_date_position(self, idx):
        btn = self.pos_buttons[idx]
        if not btn.isChecked():
            self.current_date_corner = None
        else:
            self.current_date_corner = self.positions[idx]
            for i, b in enumerate(self.pos_buttons):
                if i != idx:
                    b.setChecked(False)
            self.lbl_image.snap_to_corner(self.current_date_corner)
        self.save_state()
        self.show_current_image()

    def get_exif_date(self, image_path):
        try:
            with Image.open(image_path) as img:
                exif = img._getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        if tag == 'DateTimeOriginal':
                            date_part = value.split(' ')[0]
                            parts = date_part.split(':')
                            if len(parts) == 3:
                                return f"{parts[2]}-{parts[1]}-{parts[0]}"
        except Exception:
            pass
        
        try:
            mtime = os.path.getmtime(image_path)
            dt = datetime.datetime.fromtimestamp(mtime)
            return dt.strftime("%d-%m-%Y")
        except Exception:
            return ""

    def draw_date_on_image(self, image, date_str):
        if not date_str: return image
        
        painter = QPainter(image)
        base_dim = max(image.width(), image.height())
        font_size = max(10, int(base_dim * (self.font_size_pct / 100.0)))
        font = QFont("Arial", font_size, QFont.Weight.Bold)
        painter.setFont(font)
        
        x = self.rel_x * image.width()
        y = self.rel_y * image.height()
        
        painter.setPen(QColor(0, 0, 0, 150))
        painter.drawText(int(x)+2, int(y)+2, date_str)
        painter.setPen(QColor("white"))
        painter.drawText(int(x), int(y), date_str)
        
        painter.end()
        return image

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PhotoSelectorApp()
    window.show()
    sys.exit(app.exec())
