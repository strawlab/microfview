import time
import cv2

from microfview import Microfview, PluginChain, DisplayPlugin, BlockingPlugin, get_capture_object


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

class Slow(BlockingPlugin):
    def process_frame(self, *args):
        time.sleep(0.05)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)

    fview = Microfview.new_from_commandline(cap_fallback=get_capture_object("synth:class=dot:bg=graffiti.png"))

    blue = PluginChain(ChannelSeparator(0),
                       DisplayPlugin('blue', show_original_frame=False),
                       Slow())
    fview.attach_parallel_plugin(blue)
    green = PluginChain(ChannelSeparator(1),
                        DisplayPlugin('green', show_original_frame=False))
    fview.attach_parallel_plugin(green)
    red = PluginChain(ChannelSeparator(2),
                      DisplayPlugin('red', show_original_frame=False),
                      Slow())
    fview.attach_parallel_plugin(red)

    fview.main()


