"""microfview.camera module

Provides CameraCapture class for cam_iface cameras.
"""
import motmot.cam_iface.cam_iface_ctypes as cam_iface

import logging
logger = logging.getLogger('microfview')


class CameraCapture(cam_iface.Camera):

    def __init__(self, device_num=0, mode_num=None,
                 num_buffers=30, trigger_mode=None, roi=None):
        """class for interfacing cam_iface cameras.

        Args:
          device_num (int, optional): cam_iface device number. Defaults to 0.
          mode_num (int, optional): camera mode number.
          num_buffers (int, optional): image buffer length for camera.
            Defaults to 30.
          trigger_mode (int, optional): trigger mode number.
          roi ((int, int), optional): region of interest. Defaults to full
            image.

        """
        logger.info('initializing camera %d', device_num)

        # print all available camera modes on init.
        num_modes = cam_iface.get_num_modes(device_num)
        for this_mode_num in range(num_modes):
            mode_str = cam_iface.get_mode_string(device_num, this_mode_num)
            logger.info('video mode %d: %s', this_mode_num, mode_str)
            if mode_num is None:
                if 'DC1394_VIDEO_MODE_FORMAT7_0' in mode_str and 'MONO8' in mode_str:
                    mode_num = this_mode_num
        logger.info('using video mode %d', mode_num if mode_num is not None else 0)

        # initialize cam_iface.Camera instance.
        cam_iface.Camera.__init__(self, device_num, num_buffers, mode_num)

        # print all available trigger modes.
        n_trigger_modes = self.get_num_trigger_modes()
        for i in range(n_trigger_modes):
            logger.info('trigger mode %d: %s', i, self.get_trigger_mode_string(i))
        if trigger_mode is not None:
            self.set_trigger_mode_number(trigger_mode)
        logger.info('using trigger mode %d', self.get_trigger_mode_number())

        # start the camera and set roi if requested.
        self.start_camera()
        if roi is not None:
            self.set_frame_roi(*roi)
            actual_roi = self.get_frame_roi()
            if roi != actual_roi:
                raise ValueError("could not set ROI. Actual ROI is %s." % (actual_roi,))

        # set errors which can be ignored by the microfview mainloop
        self.noncritical_errors = (cam_iface.FrameDataMissing,
                                   cam_iface.FrameSystemCallInterruption)
