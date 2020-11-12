#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import cv2
import socket
import io
import math
import sys
import os
import pandas as pd


from PIL import Image

dirname = os.path.dirname(os.path.abspath(__file__)) + '/resources/'

verbose = False
camera_mode = False

UDP_IP = '127.0.0.1'
UDP_PORT = 5005
MAX_PACKET = 9216 # This value depends on your environment.

screen_size = (414,896) # default


# Utility
def launch_logo():
    with open(dirname + 'sprash.txt','r') as file:
        logo = file.read()
        print(logo.replace('█', '\033[94m' + '█' + '\033[0m'))


def verbose_print(text):
    if verbose:
        print(text)

def organize_color(image_array): # While OpenCV uses BGR, Pillow uses RGB so we have to convert the color pattern.
    return cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)

def image_to_bytes(image: Image):
  imgByteArr = io.BytesIO()
  image.save(imgByteArr, format='PNG')
  imgByteArr = imgByteArr.getvalue()
  return imgByteArr

def crop_image(image: Image):
    center_x = int(image.width / 2)
    center_y = int(image.height / 2)

    screen_width = screen_size[0]
    screen_height = screen_size[1]

    left_upper = (center_x - int(screen_width / 2), center_y - int(screen_height / 2))
    right_lower = (center_x + int(screen_width / 2), center_y + int(screen_height / 2))

    return image.crop(left_upper + right_lower)

# Main Cycle

def load_argument():
    global screen_size

    def verbose_on():
        global verbose

        verbose = True
        print(' ~ verbose mode ~ ')

    def camera_on():
        global camera_mode

        camera_mode = True
        print(' ~ camera mode ~ ')

    def print_help():
        with open(dirname + 'command_help.txt','r') as file:
            print(file.read())
        exit()

    arguments = sys.argv
    patterns = {'verbose' : verbose_on , 'camera' : camera_on , 'help' : print_help }

    for argument in arguments:
        for target_argument, function in patterns.items():
            for format in ['-' , '--']:

                target = format + target_argument
                if argument == format + target_argument or argument == format + target_argument[0]:
                    function()

    #For Changing Screen Size.
    print('Checking the screen size of iOS Simulator...')
    display_sizes = pd.read_csv(dirname + 'displays.csv')
    for row in display_sizes.itertuples():

        device_name = row.device
        target_argument = [device_name, 'iphone' + device_name]

        for argument in map(lambda arg: arg.lower(), arguments):
            if argument in target_argument:
                screen_size = (row.width, row.height)
                print('Screen Size: ' + str(screen_size[0]) + 'x' + str(screen_size[1]))
                return

    print('Screen Size: ' + str(screen_size[0]) + 'x' + str(screen_size[1]))


def capture():

    cap = cv2.VideoCapture(0)

    while(True):
        ret, frame = cap.read()

        if camera_mode:
            cv2.imshow('frame',frame)

        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

        image = Image.fromarray(organize_color(frame))
        image = crop_image(image)
        raw_data = image_to_bytes(image)
        verbose_print('\nCaptured: ImageSize → ' + str(len(raw_data)))


        sock.sendto(b'.', (UDP_IP, UDP_PORT)) #画像データの始まりを示す識別子
        for i in range(math.ceil(len(raw_data) / MAX_PACKET)):
            sock.sendto(raw_data[i*MAX_PACKET:(i+1)*MAX_PACKET],(UDP_IP, UDP_PORT)) # https://stackoverflow.com/questions/22819214/udp-message-too-long

        verbose_print('Success! Packets are sent.')

        if not verbose:
            print('Success.')

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def get_max_packet():
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:

        for i in range(9216, 100000):
            try:
                sock.sendto(b"a" * i, (UDP_IP, UDP_PORT))
            except:
                return i - 1



def main():
    launch_logo()
    load_argument()

    print('\nIf you need some help, use command \'-h\'. \n\nChecking your environment...')

    MAX_PACKET = get_max_packet()
    print('The maximum length of data that can be sent over UDP is ' + str(MAX_PACKET) + ' bytes. \n\nRunning...')

    capture()



if __name__ == '__main__':
    main()
