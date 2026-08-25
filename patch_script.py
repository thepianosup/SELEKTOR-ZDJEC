import re

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Imports and ImageLabel class
imports_target = """from PyQt6.QtGui import QPixmap, QKeySequence, QShortcut, QTransform, QImage, QImageReader, QPainter, QFont, QColor
from PIL import Image, ExifTags
import datetime
from PyQt6.QtCore import Qt

STATE_FILE = "state.json"

class PhotoSelectorApp(QMainWindow):"""

imports_replacement = """from PyQt6.QtGui import QPixmap, QKeySequence, QShortcut, QTransform, QImage, QImageReader, QPainter, QFont, QColor, QFontMetrics, QPen
from PIL import Image, ExifTags
import datetime
from PyQt6.QtCore import Qt, QRect

STATE_FILE = "state.json"

class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_pixmap = None
        self.date_text = ""
        self.message = "Wybierz foldery, aby rozpocząć.\\n\\nStrzałka w PRAWO -> skopiuj\\nStrzałka w LEWO -> odrzuć\\nGÓRA/DÓŁ -> obróć zdjęcie i zapisz\\nCMD + Z -> cofnij"
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

class PhotoSelectorApp(QMainWindow):"""
text = text.replace(imports_target, imports_replacement)

# 2. State vars in __init__
init_target = """        self.font_size_pct = 2.5
        self.margin_x_pct = 2.0
        self.margin_y_pct = 2.0

        self.load_state()"""
init_replacement = """        self.font_size_pct = 2.5
        self.rel_x = 0.02
        self.rel_y = 0.02

        self.load_state()"""
text = text.replace(init_target, init_replacement)

# 3. Sliders UI removal
sliders_target = """        # Sliders for date settings
        date_sliders_layout = QVBoxLayout()
        date_sliders_layout.setSpacing(2)
        
        def create_slider(label_text, min_v, max_v, default_v):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 10px; color: #aaa;")
            sl = QSlider(Qt.Orientation.Horizontal)
            sl.setRange(min_v, max_v)
            sl.setValue(int(default_v))
            sl.setFixedWidth(80)
            date_sliders_layout.addWidget(lbl)
            date_sliders_layout.addWidget(sl)
            return sl
            
        self.slider_font = create_slider("Rozmiar", 5, 100, self.font_size_pct * 10)
        self.slider_mx = create_slider("Poz. X", 0, 500, self.margin_x_pct * 10)
        self.slider_my = create_slider("Poz. Y", 0, 500, self.margin_y_pct * 10)
        
        self.slider_font.valueChanged.connect(self.on_sliders_changed)
        self.slider_mx.valueChanged.connect(self.on_sliders_changed)
        self.slider_my.valueChanged.connect(self.on_sliders_changed)
        
        sliders_widget = QWidget()
        sliders_widget.setLayout(date_sliders_layout)
        
        date_controls_layout = QHBoxLayout()
        date_controls_layout.addWidget(date_widget)
        date_controls_layout.addWidget(sliders_widget)
        
        date_controls_widget = QWidget()
        date_controls_widget.setLayout(date_controls_layout)
        
        info_layout.addWidget(date_controls_widget)"""

sliders_replacement = """        info_layout.addWidget(date_widget)"""
text = text.replace(sliders_target, sliders_replacement)

spacer_target = """        # Spacer on right to balance the grid
        right_spacer = QWidget()
        right_spacer.setFixedSize(180, 80)"""
spacer_replacement = """        # Spacer on right to balance the grid
        right_spacer = QWidget()
        right_spacer.setFixedSize(80, 80)"""
text = text.replace(spacer_target, spacer_replacement)

# 4. lbl_image to ImageLabel
lbl_target = """        # Image display
        self.lbl_image = QLabel("Wybierz foldery, aby rozpocząć.\\n\\nStrzałka w PRAWO -> skopiuj\\nStrzałka w LEWO -> odrzuć\\nGÓRA/DÓŁ -> obróć zdjęcie i zapisz\\nCMD + Z -> cofnij")
        self.lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image.setStyleSheet("font-size: 20px; color: #888888; border: 2px dashed #444444; border-radius: 10px;")
        self.lbl_image.setMinimumSize(400, 300)
        layout.addWidget(self.lbl_image, stretch=1)"""
lbl_replacement = """        # Image display
        self.lbl_image = ImageLabel(self)
        self.lbl_image.setMinimumSize(400, 300)
        layout.addWidget(self.lbl_image, stretch=1)"""
text = text.replace(lbl_target, lbl_replacement)

# 5. state handling
load_target = """                    self.font_size_pct = state.get("font_size_pct", 2.5)
                    self.margin_x_pct = state.get("margin_x_pct", 2.0)
                    self.margin_y_pct = state.get("margin_y_pct", 2.0)"""
load_replacement = """                    self.font_size_pct = state.get("font_size_pct", 2.5)
                    self.rel_x = state.get("rel_x", 0.02)
                    self.rel_y = state.get("rel_y", 0.02)
                    self.current_date_corner = state.get("current_date_corner", None)"""
text = text.replace(load_target, load_replacement)

save_target = """            "font_size_pct": getattr(self, "font_size_pct", 2.5),
            "margin_x_pct": getattr(self, "margin_x_pct", 2.0),
            "margin_y_pct": getattr(self, "margin_y_pct", 2.0)"""
save_replacement = """            "font_size_pct": getattr(self, "font_size_pct", 2.5),
            "rel_x": getattr(self, "rel_x", 0.02),
            "rel_y": getattr(self, "rel_y", 0.02),
            "current_date_corner": getattr(self, "current_date_corner", None)"""
text = text.replace(save_target, save_replacement)

# 6. show_current_image
show_target = """            if image.isNull():
                self.lbl_image.setText("Nie można załadować zdjęcia.\\nFormat może nie być wspierany (np. HEIC).")
                self.lbl_image.setStyleSheet("font-size: 20px; color: #ff5555; border: none;")
            else:
                if self.current_date_corner:
                    date_str = self.get_exif_date(img_path)
                    image = self.draw_date_on_image(image, date_str, self.current_date_corner)
                    
                pixmap = QPixmap.fromImage(image)
                scaled_pixmap = pixmap.scaled(
                    self.lbl_image.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.lbl_image.setPixmap(scaled_pixmap)
                self.lbl_image.setStyleSheet("border: none;")
                
            self.setWindowTitle(f"Selektor Zdjęć - {os.path.basename(img_path)}")
        else:
            self.lbl_image.clear()
            self.lbl_image.setText("Brak kolejnych zdjęć do pokazywania")
            self.lbl_image.setStyleSheet("font-size: 24px; color: #aaffaa; border: 2px dashed #444444; border-radius: 10px;")
            self.setWindowTitle("Selektor Zdjęć")"""

show_replacement = """            if image.isNull():
                self.lbl_image.set_message("Nie można załadować zdjęcia.\\nFormat może nie być wspierany (np. HEIC).")
            else:
                pixmap = QPixmap.fromImage(image)
                date_str = self.get_exif_date(img_path) if self.current_date_corner else ""
                self.lbl_image.set_image(pixmap, date_str)
                
            self.setWindowTitle(f"Selektor Zdjęć - {os.path.basename(img_path)}")
        else:
            self.lbl_image.set_message("Brak kolejnych zdjęć do pokazywania")
            self.setWindowTitle("Selektor Zdjęć")"""
text = text.replace(show_target, show_replacement)

# 7. action_move
action_target = """                image = self.draw_date_on_image(image, date_str, self.current_date_corner)"""
action_replacement = """                image = self.draw_date_on_image(image, date_str)"""
text = text.replace(action_target, action_replacement)

# 8. set_date_position & sliders_changed
set_date_target = """        if not btn.isChecked():
            self.current_date_corner = None
        else:
            self.current_date_corner = self.positions[idx]
            for i, b in enumerate(self.pos_buttons):
                if i != idx:
                    b.setChecked(False)
        self.show_current_image()

    def on_sliders_changed(self):
        self.font_size_pct = self.slider_font.value() / 10.0
        self.margin_x_pct = self.slider_mx.value() / 10.0
        self.margin_y_pct = self.slider_my.value() / 10.0
        self.save_state()
        self.show_current_image()"""

set_date_replacement = """        if not btn.isChecked():
            self.current_date_corner = None
        else:
            self.current_date_corner = self.positions[idx]
            for i, b in enumerate(self.pos_buttons):
                if i != idx:
                    b.setChecked(False)
            self.lbl_image.snap_to_corner(self.current_date_corner)
        self.save_state()
        self.show_current_image()"""
text = text.replace(set_date_target, set_date_replacement)

# 9. draw_date_on_image
draw_target = """    def draw_date_on_image(self, image, date_str, corner):
        if not date_str: return image
        
        painter = QPainter(image)
        base_dim = max(image.width(), image.height())
        font_size = max(10, int(base_dim * (self.font_size_pct / 100.0)))
        font = QFont("Arial", font_size, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor("white"))
        
        margin_x = int(base_dim * (self.margin_x_pct / 100.0))
        margin_y = int(base_dim * (self.margin_y_pct / 100.0))
        
        text_rect = painter.fontMetrics().boundingRect(date_str)
        
        if corner == 'TL':
            x = margin_x
            y = margin_y + text_rect.height()
        elif corner == 'TR':
            x = image.width() - text_rect.width() - margin_x
            y = margin_y + text_rect.height()
        elif corner == 'BL':
            x = margin_x
            y = image.height() - margin_y
        elif corner == 'BR':
            x = image.width() - text_rect.width() - margin_x
            y = image.height() - margin_y
        else:
            x, y = margin_x, margin_y + text_rect.height()
            
        # Draw soft drop shadow for readability
        painter.setPen(QColor(0, 0, 0, 150))
        painter.drawText(x + 2, y + 2, date_str)
        
        painter.setPen(QColor("white"))
        painter.drawText(x, y, date_str)
        
        painter.end()
        return image"""

draw_replacement = """    def draw_date_on_image(self, image, date_str):
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
        return image"""
text = text.replace(draw_target, draw_replacement)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)

