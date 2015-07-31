import os.path
import logging

logger = logging.getLogger('microfview.capture')

def get_capture_object(desc, **options):
    desc = desc or ''   #remove None
    try:
        use_opencv = options.pop('use_opencv')
    except KeyError:
        use_opencv = True

    if os.path.isfile(desc):
        if desc.endswith('.fmf'):
            logging.info('Opening FMF file using motmot')
            from .videofmf import FMFCapture
            return FMFCapture(desc, **options)
        else:
            logging.info('Opening video file using OpenCV')
            from .opencv import OpenCVCapture
            return OpenCVCapture(desc, is_file=True)

    if desc.startswith('/dev/video'):
        logging.info('Opening video device %s using OpenCV' % desc)
        from .opencv import OpenCVCapture
        # cv2.VideoCapture() does'nt accept /dev/videoX
        device_num = int(desc[-1])
        return OpenCVCapture(device_num, is_file=False, **options)
    elif use_opencv:
        try:
            device_num = int(options['device_num'])
        except KeyError:
            device_num = 0
        logging.info('Opening video device #%d using OpenCV' % device_num)
        from .opencv import OpenCVCapture
        return OpenCVCapture(device_num, is_file=False, **options)
    else:
        logging.info('Opening camiface camera')
        from .cameracamiface import CamifaceCapture
        return CamifaceCapture(**options)
        
class CaptureBase(object):

    fps = None

    frame_count = None
    frame_width = None
    frame_height = None

    is_video_file = None

    noncritical_errors = tuple()

    @property
    def frame_shape(self):
        return self.frame_width,self.frame_height

    def seek_frame(self, n):
        raise NotImplementedError

    def grab_frame_n(self, n):
        raise NotImplementedError

