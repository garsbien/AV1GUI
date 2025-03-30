import sys
import os
import subprocess
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog,
    QLineEdit, QProgressBar, QTextEdit
)
from PyQt6.QtCore import QThread, pyqtSignal

class EncoderThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, input_file, output_file, quality, resolution):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.quality = quality
        self.resolution = resolution
        self.process = None
        self.temp_yuv = self.input_file.rsplit('.', 1)[0] + ".yuv"
        self.fps = None
        self.bit_depth = 8  # Par défaut, mais on forcera 10 bits pour la sortie

    def run(self):
        try:
            # ✅ Extraction des infos vidéo avec ffprobe
            ffprobe_cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,pix_fmt,r_frame_rate",
                "-of", "json", self.input_file
            ]
            result = subprocess.run(ffprobe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

            info = json.loads(result.stdout)
            stream = info["streams"][0]
            source_width, source_height = int(stream["width"]), int(stream["height"])
            self.fps = eval(stream["r_frame_rate"])  # Convertir "30/1" en 30.0

            # ✅ Détection du bit depth de la vidéo source
            if "10le" in stream["pix_fmt"]:
                self.bit_depth = 10

            print(f"📊 Vidéo source : {source_width}x{source_height}, {self.fps} FPS, {self.bit_depth} bits")

            # ✅ Vérification de la résolution demandée
            if self.resolution[0] > source_width * 2 or self.resolution[1] > source_height * 2:
                raise ValueError(f"⚠️ Upscaling excessif ! (Source: {source_width}x{source_height}, Demandé: {self.resolution[0]}x{self.resolution[1]})")

            # ✅ Ajustement si nécessaire
            if self.resolution[0] > source_width and self.resolution[1] > source_height:
                self.resolution = (source_width, source_height)
                print(f"✅ Résolution ajustée : {self.resolution[0]}x{self.resolution[1]}")

            # ✅ Conversion en YUV (en 10 bits, peu importe la source)
            pix_fmt = "yuv420p10le"  # Forcé en 10 bits pour la sortie
            ffmpeg_cmd = [
                "ffmpeg", "-i", self.input_file,
                "-pix_fmt", pix_fmt,
                "-s", f"{self.resolution[0]}x{self.resolution[1]}",
                "-r", str(self.fps),
                "-f", "rawvideo", self.temp_yuv
            ]
            subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

            # ✅ Trouver le chemin du fichier SvtAv1EncApp.exe dans le même dossier que l'exécutable principal
            exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))  # Obtenir le répertoire de l'EXE
            svt_exe_path = os.path.join(exe_dir, "SvtAv1EncApp.exe")  # Créer le chemin vers SvtAv1EncApp.exe

            # Vérifier si le fichier SvtAv1EncApp.exe existe
            if not os.path.exists(svt_exe_path):
                raise FileNotFoundError(f"Le fichier SvtAv1EncApp.exe n'a pas été trouvé dans le répertoire : {exe_dir}")

            # ✅ Encodage SVT-AV1
            svt_cmd = [
                svt_exe_path,
                "-i", self.temp_yuv, "-b", self.output_file,
                "--preset", "3", "--crf", str(self.quality),
                "--film-grain", "0", "--film-grain-denoise", "1",
                "--enable-tpl-la", "1", "--lp", "0",
                "--enable-restoration", "1", "--scd", "1",
                "--keyint", "240", "--input-depth", str(10),  # Forcé en 10 bits pour la sortie
                "--passes", "1", "--width", str(self.resolution[0]),
                "--height", str(self.resolution[1]), "--fps", str(int(self.fps))
            ]

            print("🚀 Lancement de l'encodage SVT-AV1...")
            self.process = subprocess.Popen(svt_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            for line in self.process.stdout:
                print(line.strip())
                if "frame" in line:
                    parts = line.split()
                    try:
                        frame_number = int(parts[parts.index("frame") + 1])
                        self.progress.emit(min(100, frame_number // 10))
                    except (ValueError, IndexError):
                        pass

            self.process.wait()
            self.finished.emit(self.output_file)

            # ✅ Suppression du fichier temporaire
            if os.path.exists(self.temp_yuv):
                os.remove(self.temp_yuv)

        except Exception as e:
            print(f"❌ Erreur : {e}")
            self.finished.emit(f"Erreur: {str(e)}")

    def stop(self):
        if self.process:
            self.process.terminate()

class AV1EncoderGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Encodeur AV1 - SVT-AV1 GUI")
        self.setGeometry(200, 200, 500, 350)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel("Sélectionner une vidéo :")
        layout.addWidget(self.label)

        self.file_button = QPushButton("Ouvrir un fichier")
        self.file_button.clicked.connect(self.select_file)
        layout.addWidget(self.file_button)

        self.file_label = QLabel("Aucun fichier sélectionné")
        layout.addWidget(self.file_label)

        self.quality_label = QLabel("Qualité (1-63) :")
        layout.addWidget(self.quality_label)

        self.quality_input = QLineEdit("23")
        layout.addWidget(self.quality_input)

        self.resolution_label = QLabel("Résolution (ex: 1920x1080) :")
        layout.addWidget(self.resolution_label)

        self.resolution_input = QLineEdit("1920x1080")
        layout.addWidget(self.resolution_input)

        self.start_button = QPushButton("Lancer l'encodage")
        self.start_button.clicked.connect(self.start_encoding)
        layout.addWidget(self.start_button)

        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_encoding)
        layout.addWidget(self.cancel_button)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner une vidéo", "", "Vidéos (*.mp4 *.mkv *.avi *.mov)")
        if file_path:
            self.input_file = file_path
            self.file_label.setText(f"Fichier : {os.path.basename(file_path)}")

    def start_encoding(self):
        if not hasattr(self, 'input_file'):
            self.log_output.append("⚠️ Veuillez sélectionner un fichier vidéo.")
            return

        quality = self.quality_input.text()
        output_file = self.input_file.rsplit('.', 1)[0] + "_av1.ivf"

        resolution_str = self.resolution_input.text()
        try:
            resolution = tuple(map(int, resolution_str.lower().split("x")))
            if len(resolution) != 2:
                raise ValueError
        except ValueError:
            self.log_output.append("⚠️ Résolution invalide. Format attendu : largeurxhauteur (ex: 1920x1080)")
            return

        self.encoder_thread = EncoderThread(self.input_file, output_file, quality, resolution)
        self.encoder_thread.progress.connect(self.progress_bar.setValue)
        self.encoder_thread.finished.connect(self.encoding_done)
        self.encoder_thread.start()

        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.log_output.append("🚀 Encodage en cours...")

    def cancel_encoding(self):
        if hasattr(self, 'encoder_thread') and self.encoder_thread.isRunning():
            self.encoder_thread.stop()
            self.log_output.append("❌ Encodage annulé.")
            self.progress_bar.setValue(0)
            self.start_button.setEnabled(True)
            self.cancel_button.setEnabled(False)

    def encoding_done(self, output_file):
        self.log_output.append(f"✅ Encodage terminé : {output_file}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AV1EncoderGUI()
    window.show()
    sys.exit(app.exec())
