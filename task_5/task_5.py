import cv2
from queue import Queue, Empty
from ultralytics import YOLO
import threading
import time
import argparse

class ParallelModel:
    def __init__(self, num_threads, video):
        try:
            self.num_threads = num_threads
            self.video = cv2.VideoCapture(video)
            if not self.video.isOpened():
                raise Exception("Error in video_path")
        except:
            raise Exception("Init error")

    def process_frames(self, input_q, output_q):
        model = YOLO('yolov8s-pose.pt')
        while True:
            try:
                frame, index = input_q.get(timeout=1)
                result = model(frame, device='cpu')[0].plot()
                output_q.put((result, index))
                input_q.task_done()
            except Empty:
                break
            except Exception as e:
                print(f"Error in process_frames: {e}")
                break

    def read_frames(self, input_q):
        frame_count = 0
        size = None
        while self.video.isOpened():
            ret, frame = self.video.read()
            if not ret:
                break
            if size is None:
                size = frame.shape
            input_q.put((frame, frame_count))
            frame_count += 1
        return frame_count, size

    def get_pose_video(self):
        input_queue = Queue()
        output_queue = Queue()

        frame_count, size = self.read_frames(input_queue)
        threads = []
        for i in range(self.num_threads):
            thread = threading.Thread(target=self.process_frames, args=(input_queue, output_queue, ))
            threads.append(thread)
            print(i)

        for thread in threads:
            thread.start()

        start_time = time.time()
        frames = [None] * frame_count

        try:
            while True:
                frame, index = output_queue.get(timeout=9)
                frames[index] = frame
                print(f'frame {index + 1} of {frame_count}')
        except Empty:
            pass
            print("Queue is empty")
        except Exception as e:
            print(f"Error in main thread: {e}")
            print(f"Error in thread: {e}")

        for thread in threads:
            thread.join()

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter('video_out.mp4', fourcc, 30, (size[1], size[0]))
        for frame in frames:
            video_writer.write(frame)
        video_writer.release()

        return time.time() - start_time

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path_to_video', type=str, default=r'fun_video.avi',
                        help='Path to video (default: ./fun_video.avi)')
    parser.add_argument('--num_threads', type=int, default=7, help='Number of threads (default: 1)')
    args = parser.parse_args()
    result = ParallelModel(args.num_threads, args.path_to_video)
    print("TIME: ", result.get_pose_video())