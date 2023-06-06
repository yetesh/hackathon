import threading
import queue
import time
import sys
import TranscriberModels

from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QLabel, QPushButton, QSlider
from PyQt5.QtCore import Qt, QTimer
from AudioTranscriber import AudioTranscriber
from GPTResponder import GPTResponder
import AudioRecorder

def write_in_textbox(textbox, text):
    textbox.setPlainText(text)

def update_transcript_UI(transcriber, textbox):
    transcript_string = transcriber.get_transcript()
    textbox.setPlainText(transcript_string)
    QTimer.singleShot(300, lambda: update_transcript_UI(transcriber, textbox))

def update_response_UI(responder, textbox, update_interval_slider_label, update_interval_slider, freeze_state):
    if not freeze_state[0]:
        response = responder.response
        textbox.setPlainText(response)
        update_interval = int(update_interval_slider.value())
        responder.update_response_interval(update_interval)
        update_interval_slider_label.setText(f"Update interval: {update_interval} seconds")

    QTimer.singleShot(300, lambda: update_response_UI(responder, textbox, update_interval_slider_label, update_interval_slider, freeze_state))

def clear_context(transcriber, audio_queue):
    transcriber.clear_transcript_data()
    with audio_queue.mutex:
        audio_queue.queue.clear()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.audio_queue = queue.Queue()

        user_audio_recorder = AudioRecorder.DefaultMicRecorder()
        user_audio_recorder.record_into_queue(self.audio_queue)

        time.sleep(2)

        speaker_audio_recorder = AudioRecorder.DefaultSpeakerRecorder()
        speaker_audio_recorder.record_into_queue(self.audio_queue)

        model = TranscriberModels.get_model('--api' in sys.argv)

        self.transcriber = AudioTranscriber(user_audio_recorder.source, speaker_audio_recorder.source, model)
        transcribe = threading.Thread(target=self.transcriber.transcribe_audio_queue, args=(self.audio_queue,))
        transcribe.daemon = True
        transcribe.start()

        self.responder = GPTResponder()
        respond = threading.Thread(target=self.responder.respond_to_transcriber, args=(self.transcriber,))
        respond.daemon = True
        respond.start()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Ecoute")
        self.setGeometry(100, 100, 1000, 600)

        font_size = 20

        self.transcript_textbox = QTextEdit(self)
        self.transcript_textbox.setFontPointSize(font_size)
        self.transcript_textbox.setStyleSheet("color: #FFFCF2; background-color: #252422")
        self.transcript_textbox.setReadOnly(True)
        self.transcript_textbox.setLineWrapMode(QTextEdit.WidgetWidth)
        self.transcript_textbox.setGeometry(10, 20, 470, 520)

        self.response_textbox = QTextEdit(self)
        self.response_textbox.setFontPointSize(font_size)
        self.response_textbox.setStyleSheet("color: #639cdc; background-color: #252422")
        self.response_textbox.setReadOnly(True)
        self.response_textbox.setLineWrapMode(QTextEdit.WidgetWidth)
        self.response_textbox.setGeometry(520, 20, 470, 520)

        self.clear_transcript_button = QPushButton("Clear Transcript", self)
        self.clear_transcript_button.setGeometry(10, 560, 120, 30)
        self.clear_transcript_button.clicked.connect(lambda: clear_context(self.transcriber, self.audio_queue))

        self.freeze_button = QPushButton("Freeze", self)
        self.freeze_button.setGeometry(880, 560, 100, 30)
        self.freeze_button.clicked.connect(self.freeze_unfreeze)

        self.update_interval_slider_label = QLabel(f"Update interval: 2 seconds", self)
        self.update_interval_slider_label.setGeometry(520, 560, 200, 30)
        self.update_interval_slider_label.setStyleSheet("color: #FFFCF2")

        self.update_interval_slider = QSlider(Qt.Horizontal, self)
        self.update_interval_slider.setRange(1, 10)
        self.update_interval_slider.setValue(2)
        self.update_interval_slider.setGeometry(720, 560, 270, 30)
        self.update_interval_slider.valueChanged.connect(self.update_interval_changed)

        self.freeze_state = [False]

        self.update_transcript_UI(self.transcriber, self.transcript_textbox)
        self.update_response_UI(self.responder, self.response_textbox, self.update_interval_slider_label, self.update_interval_slider, self.freeze_state)

    def freeze_unfreeze(self):
        self.freeze_state[0] = not self.freeze_state[0]
        self.freeze_button.setText("Unfreeze" if self.freeze_state[0] else "Freeze")

    def update_interval_changed(self):
        update_interval = self.update_interval_slider.value()
        self.responder.update_response_interval(update_interval)
        self.update_interval_slider_label.setText(f"Update interval: {update_interval} seconds")

    def update_transcript_UI(self, transcriber, textbox):
        transcript_string = transcriber.get_transcript()
        textbox.setPlainText(transcript_string)
        QTimer.singleShot(300, lambda: self.update_transcript_UI(transcriber, textbox))

    def update_response_UI(self, responder, textbox, update_interval_slider_label, update_interval_slider, freeze_state):
        if not freeze_state[0]:
            response = responder.response
            textbox.setPlainText(response)
            update_interval = int(update_interval_slider.value())
            responder.update_response_interval(update_interval)
            update_interval_slider_label.setText(f"Update interval: {update_interval} seconds")

        QTimer.singleShot(300, lambda: self.update_response_UI(responder, textbox, update_interval_slider_label, update_interval_slider, freeze_state))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
