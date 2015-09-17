import cv2
import numpy as np

import logging
logger = logging.getLogger('microfview.capture.Transform')


class ImageTransform(object):

    LAYERS = ('background',)

    def __init__(self, **config):
        config = config['background']

        if config.get('mask'):
            self._contour = [np.array(c) for c in config['mask']]
            self._mask = None
        else:
            self._contour = None
        if config.get('roi'):
            roi = config['roi']
            if len(roi) > 1:
                raise ValueError('only one ROI for transform is supported')
            roi = roi[0]
            # roi is ((x0,y0), (x1,y1))
            self._roi = slice(roi[0][0],roi[1][0]), slice(roi[0][1],roi[1][1])
        else:
            self._roi = None

    def transform(self, img):
        if self._contour is not None:
            if self._mask is None:
                # init mask now we know the frame size
                self._mask = np.empty((img.shape[0], img.shape[1]), dtype=np.uint8)
                # start by keeping everything
                self._mask.fill(255)
                for c in self._contour:
                    # subtract the background
                    cv2.drawContours(self._mask, [c], 0, (0, 0, 0), -1) #-1 = CV_FILLED
            return cv2.bitwise_and(img, img, mask=self._mask)
        if self._roi is not None:
            # slice works if image is 1 or 3 channel
            return img[self._roi[1], self._roi[0]]
        return img

