import os.path
import logging

import numpy as np

from .transform import ImageTransform

logger = logging.getLogger('microfview.capture')


def get_capture_object(desc, options_dict=None):
    if options_dict is None:
        capture_options = transform_options = {}
    else:
        capture_options = options_dict['capture']
        transform_options = options_dict['transform']

    cap = None

    desc = desc or ''   #remove None
    try:
        use_opencv = capture_options.pop('use_opencv')
    except KeyError:
        use_opencv = True

    if desc.startswith('synth:'):
        from .synth import SynthCapture
        cap = SynthCapture(desc)
    elif os.path.isfile(desc):
        if desc.endswith('.fmf'):
            logging.info('Opening FMF file using motmot')
            from .videofmf import FMFCapture
            cap = FMFCapture(desc, **capture_options)
        else:
            logging.info('Opening video file using OpenCV')
            from .opencv import OpenCVCapture
            cap = OpenCVCapture(desc, is_file=True)
    elif desc.startswith('/dev/video'):
        logging.info('Opening video device %s using OpenCV' % desc)
        from .opencv import OpenCVCapture
        # cv2.VideoCapture() does'nt accept /dev/videoX
        device_num = int(desc[-1])
        cap = OpenCVCapture(device_num, is_file=False, **capture_options)
    elif use_opencv:
        try:
            device_num = int(capture_options['device_num'])
        except KeyError:
            device_num = 0
        logging.info('Opening video device #%d using OpenCV' % device_num)
        from .opencv import OpenCVCapture
        cap = OpenCVCapture(device_num, is_file=False, **capture_options)
    else:
        logging.info('Opening camiface camera')
        from .cameracamiface import CamifaceCapture
        cap = CamifaceCapture(**capture_options)

    if transform_options:
        if all(l in transform_options for l in ImageTransform.LAYERS):
            t = ImageTransform(**transform_options)
            cap.attach_transform(t)
        else:
            logging.warn("transform expects 'foreground' and 'background' keys")

    return cap

class SeekError(Exception):
    pass


class CaptureBase(object):

    fps = np.nan

    frame_count = np.inf
    frame_width = np.nan
    frame_height = np.nan

    is_video_file = None

    noncritical_errors = tuple()

    transform = None

    supports_seeking = False

    @property
    def frame_shape(self):
        return self.frame_width,self.frame_height

    @property
    def duration(self):
        return self.fps * self.frame_count

    def seek_frame(self, n):
        raise NotImplementedError

    def grab_next_frame_blocking(self):
        raise NotImplementedError

    def grab_next_frame(self):
        img = self.grab_next_frame_blocking()
        if self.transform is not None:
            return self.transform.transform(img)
        return img

    def attach_transform(self, t):
        self.transform = t

