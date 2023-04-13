from detector import Model
from drone import Drone
import time
import cv2 as cv
import argparse
from threading import Thread
import subprocess
import os

parser = argparse.ArgumentParser(
    prog='ProgramName',
    description='What the program does',
    epilog='Text at the bottom of help')

parser.add_argument('-e', '--edges', type=float, default=0.25)
parser.add_argument('-o', '--outdoor', type=int, default=1)
parser.add_argument('-f', '--fly', type=int, default=1)
parser.add_argument('--headless', type=int, default=0)
parser.add_argument('--closed', type=int, default=0)
parser.add_argument('--lrenabled', type=int, default=1)

args = parser.parse_args()

IMG_SIZE = (1280, 720)
finished = False
landed = False

if __name__ == '__main__':
    model = Model()
    drone = Drone(fly=args.fly)
    drone.fly_to_start(outdoor=args.outdoor)
    avg_iteration_time = 0
    iteration = 0
    conditions = {'close_to_left_edge': lambda x, y: x <= args.edges and x != -1,
                'close_to_right_edge': lambda x, y: x >= (1 - args.edges) and x != -1,
                'close_to_middle':
                    lambda x, y: args.edges < x < (1 - args.edges) and args.edges * 0.5 < y < (1 - args.edges) and x != -1,
                'close_to_top': lambda x, y: y <= 0.5 * args.edges and x != -1,
                'close_to_bottom': lambda x, y: y >= (1 - args.edges) and x != -1,
                'empty': lambda x, y: x == -1
                }
    conditions_prev = {'close_to_left_edge': 0,
                     'close_to_right_edge': 0,
                     'close_to_middle': 0,
                     'close_to_top': 0,
                     'close_to_bottom': 0,
                     'empty': 0
                     }
    conditions_curr = {'close_to_left_edge': 0,
                     'close_to_right_edge': 0,
                     'close_to_middle': 0,
                     'close_to_top': 0,
                     'close_to_bottom': 0,
                     'empty': 0
                     }
    rotate_left_condition=False
    rotate_right_condition=False

    def navigate(drone, left_right_enabled):
        global finished
        global rotate_left_condition
        global rotate_right_condition
        while not finished:
            if conditions_prev['close_to_middle'] and conditions_curr['close_to_middle']:
                drone.tello.move_forward(30)
            elif rotate_left_condition:
                drone.tello.rotate_counter_clockwise(40)
                rotate_left_condition=False
            elif rotate_right_condition:
                drone.tello.rotate_clockwise(40)
                rotate_right_condition=False
            elif conditions_prev['close_to_left_edge'] and conditions_curr['close_to_left_edge'] and left_right_enabled:
                drone.tello.move_left(30)
            elif conditions_prev['close_to_right_edge'] and conditions_curr['close_to_right_edge'] and left_right_enabled:
                drone.tello.move_right(30)
            elif conditions_prev['close_to_top'] and conditions_curr['close_to_top']:
                drone.tello.move_up(30)
            elif conditions_prev['close_to_bottom'] and conditions_curr['close_to_bottom']:
                drone.tello.move_down(30)
            elif conditions_prev['empty'] and conditions_curr['empty']:
                drone.tello.move_forward(200)
                finished=True
            elif not left_right_enabled:
                drone.tello.move_forward(30)
            time.sleep(2)

    if args.fly:
        navigation = Thread(target=navigate, args=(drone,args.lrenabled))
        navigation.start()

    subprocess.run(['rm', '-r', 'sequence'])
    subprocess.run(['mkdir', 'sequence'])
    f = open('input.txt', 'w')

    while not finished:
        iteration += 1
        start = time.time()
        frame = drone.frame
        xywh = model.detect(frame)
        if xywh is None:
            image = frame
            cv.putText(img=image, text='No Window', org=(100, 100), fontFace=cv.FONT_HERSHEY_TRIPLEX, fontScale=2,
                       color=(0, 255, 0), thickness=2)
            xywh = (-1, -1, -1, -1)
        else:
            top_left = (int((xywh[0] - xywh[2] / 2) * frame.shape[0]), int((xywh[1] - xywh[3] / 2) * frame.shape[1]))
            top_right = (int((xywh[0] + xywh[2] / 2) * frame.shape[0]), int((xywh[1] + xywh[3] / 2) * frame.shape[1]))
            image = cv.rectangle(frame, top_left, top_right, (0, 255, 0), 3)
        for key in conditions.keys():
            conditions_prev[key] = conditions_curr[key]
            conditions_curr[key] = conditions[key](xywh[0], xywh[1])
        rotate_left_condition = conditions_curr['empty'] and conditions_prev['close_to_left_edge']
        rotate_right_condition = conditions_curr['empty'] and conditions_prev['close_to_right_edge']

        cv.imwrite(f'sequence/image{iteration}.png', image)
        if not args.headless:
            cv.imshow("Display window", image)
            key = cv.waitKey(1)
            if key == 27:
                finished = True
        end = time.time()
        avg_iteration_time = (avg_iteration_time * (iteration - 1) + end - start) / iteration
        f.write(f'file sequence/image{iteration}.png\nduration {end-start}\n')
        f.flush()
        os.fsync(f.fileno())


    def camera_thread():
        global iteration
        while not landed:
            iteration += 1
            start = time.time()
            frame = drone.frame
            cv.imwrite(f'sequence/image{iteration}.png', frame)
            end = time.time()
            f.write(f'file sequence/image{iteration}.png\nduration {end-start}\n')
            f.flush()
            os.fsync(f.fileno())

    camera_t = Thread(target=camera_thread)
    camera_t.start()
    if args.fly:
        navigation.join()
        drone.fly_to_finish(args.outdoor, args.closed)
    landed = True
    camera_t.join()

    if not args.headless:
        cv.destroyAllWindows()
    f.close()
    os.system('ffmpeg -f concat -i input.txt -vsync vfr -pix_fmt yuv420p output.mp4')
    # subprocess.run(['ffmpeg', '-f concat', '-i input.txt', '-vsync vfr', '-pix_fmt yuv720p', 'output.mp4'])

    print(f'Avarage processing time per frame: {avg_iteration_time}')
