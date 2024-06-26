import cv2
import logging
import threading
import time
import argparse

from datetime import datetime, timedelta
from queue import Queue

logging.basicConfig(filename='app.log', level=logging.ERROR, filemode="w")

class Sensor:
    def get(self):
        raise NotImplementedError("Subclasses must implement method get()")

class SensorX(Sensor):
    """Sensor X"""
    def __init__(self, delay: float):
        self.delay = delay
        self.data = 0

    def get(self) -> int:
        time.sleep(self.delay)
        self.data += 1
        return self.data

class SensorManager:
    def __init__(self):
        self.sensors = [
            SensorX(0.01),
            SensorX(0.1),
            SensorX(1)
        ]
        self.q = [
            Queue(),
            Queue(),
            Queue()
            ]
        self.sensor_values = [0] * len(self.sensors)
        self.threads = []
        self.running = True

    def start(self):
        for sensor, qu in zip(self.sensors, self.q):
            thread = threading.Thread(target=self._run_sensor, args=(sensor, qu,))
            self.threads.append(thread)
            thread.start()


    def _run_sensor(self, sensor, qu):
        while self.running:
            qu.put(sensor.get())


    def get_sensor_values(self):
        for sensor, queue in zip(self.sensors, self.q):
            while not queue.empty():
                self.sensor_values[self.sensors.index(sensor)] = queue.get()

        return self.sensor_values

    def stop(self):
        self.running = False
        for thread in self.threads:
            thread.join()

class WindowImage:
    def __init__(self, display_rate, sensor_manager, camera):
        self.display_rate = display_rate
        self.window_name = 'Webcam'
        self.camera = camera
        self.sensor_manager = sensor_manager

    def show(self):
        self.sensor_manager.start()
        self.camera.start()
        start_time = time.time()
        while True:
            sensor_values = self.sensor_manager.get_sensor_values()
            frame = self.camera.get_frame()

            if frame is not None:
                elapsed_time = time.time() - start_time
                elapsed_time_str = str(timedelta(seconds=int(elapsed_time)))
                cv2.putText(frame, f"Camera Uptime: {elapsed_time_str}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                text = ", ".join([f"Sensor {i + 1}: {value}" for i, value in enumerate(sensor_values)])
                cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                try:
                    cv2.imshow(self.window_name, frame)
                    time.sleep(self.display_rate)

                except Exception as e:
                    logging.error(f"Error occurred while displaying frame: {e}")
            time.sleep(0.001)

    def __del__(self):
        try:
            cv2.destroyWindow(self.window_name)
        except Exception as e:
            logging.error(f"Error occurred while destroying window: {e}")


class SensorCam:
    def __init__(self, camera_id, resolution, display_rate):
        self.camera_id = camera_id
        self.resolution = resolution
        self.cap = cv2.VideoCapture(self.camera_id)
        self.q = Queue()
        self.display_rate = display_rate
        width, height = resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.running = True
        self.threads = []

    def start(self):
        thread = threading.Thread(target=self._run_cam, args=(self.q,))
        self.threads.append(thread)
        thread.start()

    def _run_cam(self, q):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                logging.error(f"Failed to read frame from camera: {self.camera_id}")
                raise RuntimeError(f"Failed to read frame from camera: {self.camera_id}")
            else:
                if not q.empty():
                    q.queue.clear()
                    q.put(frame)
                    # time.sleep(self.display_rate)
                else:
                    q.put(frame)
                    # time.sleep(self.display_rate)

    def get_frame(self):
        if not self.q.empty():
            return self.q.get()


    def stop(self):
        self.running = False
        for thread in self.threads:
            thread.join()
        self.cap.release()


def main(camera_id, resolution, display_rate):
    try:
        display_rate = (1 / display_rate)
        sensor_manager = SensorManager()
        camera = SensorCam(camera_id, resolution, display_rate)
        if not camera.cap.isOpened():
            logging.error(f"Failed to open webcam with ID: {camera_id}")
            raise ValueError(f"Failed to open webcam with ID: {camera_id}")
        window = WindowImage(display_rate, sensor_manager, camera)
        window.show()

    except Exception as e:
        logging.exception(f"An error occurred: {e}")
        raise SystemExit("Program terminated due to error")

    finally:
        try:
            sensor_manager.stop()
            camera.stop()
        except UnboundLocalError as e:
            logging.exception(e)

if __name__ == "__main__":  
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--camera_id', type=int, default=0, help='ID of the camera (default: 0)')
    parser.add_argument('--resolution', type=str, default='640x480', help='Desired resolution of the camera (default: 640x480)')
    parser.add_argument('--display_rate', type=int, default=100, help='Rate at which to display images (default: 100 hz)')
    args = parser.parse_args()
    resolution = tuple(map(int, args.resolution.split('x')))
    main(args.camera_id, resolution, args.display_rate)