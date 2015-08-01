import time
import random

from microfview import *

class MyPlugin(BlockingPlugin):

    def __init__(self, k, vfunc, n):
        super(MyPlugin, self).__init__()
        self._k = k
        self._vfunc = vfunc
        self._n = n
        self._i = 0

    def process_frame(self, frame, frame_number, frame_count, frame_time, current_time, state):
        if self._i > self._n:
            raise PluginFinished
        self._i += 1
        self.logger.debug("%s got %r as state" % (self._k, state))
        return {self._k: self._vfunc()}

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)

    cam = get_capture_object("synth:class=dot:fps=2")
    fview = Microfview(cam)

    chain = PluginChain((
                MyPlugin('even',
                         lambda: random.choice((2,4,6,8)),
                         5),
                MyPlugin('odd',
                         lambda: random.choice((1,3,5,7)),
                         10))
    )
    fview.attach_plugin(chain)
    fview.attach_plugin(DisplayPlugin('chain'))

    fview.start()
    while not fview.finished:
       time.sleep(0.1)
    fview.stop()

