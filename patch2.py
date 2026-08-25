import re

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. lbl_similar
lbl_target = """        # Stats label
        self.lbl_stats = QLabel("Dodane: 0 | Odrzucone: 0")
        self.lbl_stats.setStyleSheet("color: #3498db; font-size: 15px; font-weight: bold; margin-bottom: 10px;")
        self.lbl_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        labels_layout.addWidget(self.lbl_stats)
        
        labels_widget = QWidget()"""

lbl_replacement = """        # Stats label
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
        
        labels_widget = QWidget()"""
text = text.replace(lbl_target, lbl_replacement)

# 2. update_stats
stats_target = """    def update_stats(self):
        added = sum(1 for item in self.history if item.get("action") in ["copied", "moved"])
        rejected = sum(1 for item in self.history if item.get("action") == "rejected")
        left = max(0, len(self.image_files) - self.current_image_index)
        self.lbl_stats.setText(f"Do wyboru: {left} | Dodane: {added} | Odrzucone: {rejected}")"""

stats_replacement = """    def update_stats(self):
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
            self.lbl_similar.hide()"""
text = text.replace(stats_target, stats_replacement)

# 3. get_image_datetime & update load_images_from_source
load_target = """        skipped_count = 0
        for f in os.listdir(self.source_folder):
            if f.startswith('.'):
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_exts:
                # If a file with the same name exists in destination, skip it entirely
                if f in dest_files:
                    skipped_count += 1
                    continue

                full_path = os.path.join(self.source_folder, f)
                if full_path not in self.processed_files:
                    self.image_files.append(full_path)
        
        self.image_files.sort()
        self.current_image_index = 0"""

load_replacement = """    def get_image_datetime(self, image_path):
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
        
        self.current_image_index = 0"""
text = text.replace(load_target, load_replacement)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)

