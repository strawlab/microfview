import random
import time

from microfview import Microfview, NonBlockingPlugin, BlockingPlugin, PluginChain, PluginFinished, get_capture_object


class TestNonBlocking(NonBlockingPlugin):

    def process_frame(self, frame, frame_number, frame_count, frame_time, current_time, state):
        time.sleep(0.2)
        self.logger.debug("processed %d" % frame_count)
        return {'block':frame_count}

class MyPlugin(BlockingPlugin):

    def __init__(self, k, vfunc, n):
        super(MyPlugin, self).__init__(logger=logging.getLogger('example.%s' % k))
        self._k = k
        self._vfunc = vfunc
        self._n = n
        self._i = 0

    @property
    def identifier(self):
        return self.__class__.__name__ + ':' + self._k

    def process_frame(self, frame, frame_number, frame_count, frame_time, current_time, state):
        time.sleep(0.1)
        if self._i > self._n:
            raise PluginFinished
        self._i += 1
        self.logger.debug("%s got %r as state" % (self._k, state.keys()))
        return {self._k: self._vfunc()}

    def stop(self):
        self.logger.debug("finished")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)

    fview = Microfview.new_from_commandline(cap_fallback=get_capture_object("synth:class=dot:fps=2:nframes=10"))

    chain = PluginChain(
                MyPlugin('even',
                         lambda: random.choice((2,4,6,8)),
                         5),
                MyPlugin('odd',
                         lambda: random.choice((1,3,5,7)),
                         10)
    )
    fview.attach_plugin(chain)
    fview.attach_plugin(TestNonBlocking())
    fview.main()


