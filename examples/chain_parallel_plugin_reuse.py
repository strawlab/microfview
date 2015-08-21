import time
import random
import os.path

import cv2

from microfview import *

class ChannelSeparator(BlockingPlugin):

    def __init__(self, channel, vmin=100, vmax=255):
        super(ChannelSeparator, self).__init__(logger=logging.getLogger('example.%s' % channel))
        self._channel = channel
        self._vmin = vmin
        self._vmax = vmax

        self.uses_color = True

    @property
    def identifier(self):
        return "%s:%s" % (self.__class__.__name__,self._channel)

    def process_frame(self, frame, frame_number, frame_count, frame_time, current_time, state):
        return cv2.inRange(frame[:,:,self._channel], self._vmin, self._vmax)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)

    bg = os.path.join(os.path.dirname(__file__),'..','data','graffiti.png')

    cam = get_capture_object("synth:class=dot:bg=%s" % bg)
    fview = Microfview(cam)

    blue = PluginChain(ChannelSeparator(0),
                       DisplayPlugin('blue', show_original_frame=False))
    fview.attach_plugin(blue)
    green = PluginChain(ChannelSeparator(1),
                        DisplayPlugin('green', show_original_frame=False))
    fview.attach_plugin(green)
    red = PluginChain(ChannelSeparator(2),
                      DisplayPlugin('red', show_original_frame=False))
    fview.attach_plugin(red)
    fview.attach_plugin(DisplayPlugin('original-image'))
    fview.main()


