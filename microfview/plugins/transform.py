import numpy as np

from ..plugin import BlockingPlugin


class ExtractROIPlugin(BlockingPlugin):

    def __init__(self, roi, copy_data=False, every=1):
        super(ExtractROIPlugin, self).__init__(every=every)
        if np.array(roi).shape != (2, 2):
            raise ValueError('ROI must be ((x0,y0), (x1,y1))')
        # roi is ((x0,y0), (x1,y1))
        self._roi_col, self._roi_row = slice(int(roi[0][0]),int(roi[1][0])), slice(int(roi[0][1]),int(roi[1][1]))
        self._copy_data = copy_data

    def process_frame(self, frame, frame_number, frame_count, frame_time, current_time, state):
        # slice works if image is 1 or 3 channel
        img = frame[self._roi_row, self._roi_col]
        if self._copy_data:
            return img.copy()
        else:
            return img
