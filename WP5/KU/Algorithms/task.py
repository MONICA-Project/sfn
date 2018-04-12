"""
  A dummy task
"""
from time import sleep
import sys
import mmap
import numpy as np
import cv2
from WP5.KU.Algorithms.crowd_density_local.get_crowd import GetCrowd


def work(width, height, buffer, seq_id):
    sys.stderr.write("buf: %d == %d\n" % (len(buffer), width*height*3/2) )
    vec = np.frombuffer(buffer, dtype=np.uint8)
    mat = np.reshape(vec, (height + int(height/2), width))
    rgb = cv2.cvtColor(mat, cv2.COLOR_YUV2BGR_NV12, 3)

    # roi WOULD NEED TO BE PULLED FROM THE CAMERA CONFIG DATA
    roi = [200, 200, 400, 400]
    # PROCESS THE FRAME HERE?
    j_mess, density_map = analyser.process_frame(rgb, 'SOME_VCA_DEFINED_CAMERA_STREAM_ID', roi)

    cv2.imshow('bw', rgb)
    cv2.waitKey(5)
    # Simulate doing something with the image (5 fps = 0.2s processing)
    sleep(0.5)
    sys.stdout.buffer.write(b'{"seq":%d,"width":%d,"height":%d}\n' % (seq_id, width, height))


if __name__ == '__main__':
    i = 0
    fd = open('/tmp/vca_mmap_python.bin', 'rb')
    data = mmap.mmap(fd.fileno(), 0, access=mmap.ACCESS_READ)
    # init here.
    analyser = GetCrowd('SOME_VCA_DEFINED_MODULE_ID')
    for line in sys.stdin.buffer:
        work(int(sys.argv[1]), int(sys.argv[2]), data, i, k)
        i += 1
