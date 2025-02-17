import cv2
import time
import ctypes
import logging
import multiprocessing
import numpy as np

from sixsens.process.audio_player import AudioPlayer
from sixsens.process.matrix import Matrix
from sixsens.process.yolo import Yolo

from sixsens.reaction.audio_reaction import AudioReaction
from sixsens.reaction.matrix_reaction import MatrixReaction

from sixsens.audio.status import VisionObstructed


def run():
    audio_player = AudioPlayer()
    matrix = Matrix()

    audio_reaction = AudioReaction()
    matrix_reaction = MatrixReaction()

    cap = cv2.VideoCapture(0)

    i = 0

    shared_buffer = None
    buffer = None
    yolo = None

    matrix_call = False
    auto_speech = False
    auto_speech_debounce = i

    past_time = time.time()
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        if i == 0:
            shared_buffer = multiprocessing.Array(
                ctypes.c_uint8, int(np.multiply.reduce(frame.shape))
            )
            buffer = np.frombuffer(shared_buffer.get_obj(), np.uint8)
            yolo = Yolo(shared_buffer, frame.shape)

        buffer[:] = frame.flatten()

        if i % 2 == 0:
            yolo.call(frame.shape)

        if auto_speech:
            frame[0:15, 0:15] = [0, 0, 255]
        if matrix_call:
            frame[0:15, 15:30] = [0, 255, 0]

        rendered = False
        if latest := yolo.latest(frame):
            latest.ims[0] = frame
            rendered_frame = latest.render()[0]
            rendered = True

            audio_reaction.process_predictions(latest)
            matrix_reaction.process_predictions(latest)

        # cv2.namedWindow("6SENS", cv2.WINDOW_NORMAL)
        # cv2.moveWindow("6SENS", 1920, 0)
        # cv2.setWindowProperty(
        #     "6SENS", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
        # )
        cv2.imshow("6SENS", rendered_frame if rendered else frame)

        movements = matrix_reaction.build_reaction()
        if np.add.reduce(movements):
            matrix.call(movements)
            matrix_call = True
        else:
            matrix_call = False

        def trigger_speech():
            logging.info(
                f"Speech triggered {'automatically' if auto_speech else ''}"
            )

            speeches = audio_reaction.build_reaction()

            for speech in speeches:
                speech.play(audio_player)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("s"):
            trigger_speech()
        elif key == ord("a") and (i - auto_speech_debounce) > 5:
            auto_speech_debounce = i
            auto_speech = not auto_speech
            logging.info(f"Auto speech: {auto_speech}")
        elif key == ord("r"):
            logging.info(f"Matrix reset")
            matrix.call(np.zeros(48, dtype=np.uint8))

        if auto_speech and i % 75 == 0 and audio_player.input_queue.empty():
            trigger_speech()

        i += 1

        if i % 100 == 0:
            logging.debug(f"Loop time {(time.time() - past_time)/100}")
            past_time = time.time()

    cap.release()
    cv2.destroyAllWindows()

    audio_player.stop()
    matrix.stop()
    yolo.stop()
