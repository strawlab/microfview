"""microfview.main module

Provides Microfview class, which manages the frame capture
and delegates frames to all plugins.

"""
import bisect
import threading
import time
import collections

import cv2
import numpy as np

import logging
logger = logging.getLogger('microfview')

from .plugin import PluginFinished, FuncWrapperPlugin
from .plugins.display import DisplayPlugin

# helper function for frame_capture checks
def _has_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))


class Microfview(threading.Thread):

    def __init__(self, frame_capture, visible=True, debug=True, single_frame_step=False, stop_frame=0):
        """Microfview main class.

        Args:
          frame_capture (microfview capture): A capture class for aquiring frames.
            See microfview.camera or microfview.video.

        """
        threading.Thread.__init__(self)
        self.daemon = True
        self._lock = threading.Lock()

        # These three methods must be provided by a frame capture
        if not (_has_method(frame_capture, 'grab_next_frame_blocking') and
                _has_method(frame_capture, 'get_last_timestamp') and
                _has_method(frame_capture, 'get_last_framenumber')):
            raise TypeError("frame_capture_device does not provide required methods.")

        self._visible = visible
        self._debug = debug

        self.frame_capture = frame_capture
        self.frame_capture_noncritical_errors = frame_capture.noncritical_errors

        self.frame_count = 0
        self.frame_number_current = 0

        self._stop_frame = stop_frame

        self._run = False

        self._plugins = []

        self._profile_timestore = None
        self._profile = None
        self._framestores = []

        self._display_plugins = []

        self._waitkey_delay = 0 if single_frame_step else 1

        self.finished = False

    @classmethod
    def new_from_commandline_args(cls, args, cap_fallback=None, add_display_plugin=True):
        from .capture import get_capture_object
        from .util import parse_config_file, print_mean_fps
        conf = parse_config_file(args.config)
        cap_fallback = get_capture_object(args.capture, cap_fallback=cap_fallback, options_dict=conf)
        obj = cls(cap_fallback, visible=not args.hide, debug=args.debug, single_frame_step=args.step, stop_frame=args.stop_frame)
        if args.print_fps:
            obj.attach_profiler(print_mean_fps)
        if add_display_plugin and (not args.hide):
            obj.attach_display_plugin()
        return obj

    @classmethod
    def new_from_commandline(cls, cap_fallback=None, add_display_plugin=True):
        from .util import get_argument_parser
        parser = get_argument_parser()
        return Microfview.new_from_commandline_args(parser.parse_args(), cap_fallback=cap_fallback, add_display_plugin=add_display_plugin)

    def attach_display_plugin(self, plugin=None):
        """Attaches a display plugin to be called after every other plugin has
        been called.

        If no plugin is given, the default DisplayPlugin is used.
        """
        if plugin is None:
            plugin = DisplayPlugin('microfview', show_original_frame=True, every=1)
        self._display_plugins.append(plugin)

    def attach_profiler(self, callback_func):
        """Attaches a function to be called after every iteration that
        is passed a dictionary showing how long each plugin took to execute"""
        if not hasattr(callback_func, '__call__'):
            raise TypeError("callback_func has to be callable")
        self._profile_timestore = collections.defaultdict(lambda: collections.deque(maxlen=10))
        self._profile = callback_func

    def attach_framestore(self, obj):
        """Attaches a FrameStore instance that will be called after every
        frame to save any relevant data for that frame"""
        self._framestores.append(obj)

    def attach_callback(self, callback_func, every=1):
        """Attaches a callback function, which is called on every Nth frame.

        Args:
          callback_func:  takes 5 parameters (buf, frame_number, frame_count, frame_timestamp, now_timestamp, state)
          every:  integer > 0

        returns:
          plugin_object:  can be used to detach callback
        """
        if not hasattr(callback_func, '__call__'):
            raise TypeError("callback_func has to be callable")
        if not isinstance(every, int):
            raise TypeError("every has to be of type int")
        if every < 1:
            raise ValueError("every has to be bigger than 0")

        plug = FuncWrapperPlugin(callback_func, callback_func.func_name, every)
        if plug in self._plugins:
            raise ValueError("callback_func + every combination already exists")
        self.attach_plugin(plug)
        return plug

    def attach_plugin(self, plugin):
        """Attaches a plugin."""
        # check if plugin provides the required methods and attributes
        if not (_has_method(plugin, 'start') and
                _has_method(plugin, 'stop') and
                _has_method(plugin, 'push_frame') and
                hasattr(plugin, 'every')):
            raise TypeError("plugin %r does not have the required methods/attributes." % plugin)
        self._plugins.append(plugin)
        logger.info('attaching plugin %s (shows_windows: %s)' % (plugin.human_name, plugin.shows_windows))

    def attach_parallel_plugin(self, plugin, threaded=False):
        plugin.return_frame = False
        plugin.return_state = False
        plugin.threaded = threaded
        self.attach_plugin(plugin)

    def detach_plugin(self, plugin):
        """Detaches a plugin."""
        plugin.stop()
        self._plugins.remove(plugin)

    def run(self):
        """main loop. do not call directly."""
        # display plugins are just normal plugins. Adding them here ensures they are
        # called last
        map(self.attach_plugin, self._display_plugins)

        # start all plugins
        schema = {}
        for i,plugin in enumerate(self._plugins):
            plugin.set_uid(str(i))

            plugin.set_debug(self._debug)
            plugin.set_visible(self._visible)
            plugin.start(self.frame_capture)

            schema[plugin.identifier] = plugin.get_schema()

        # initialize all frame stores
        for s in self._framestores:
            s.open(schema)

        call_cvwaitkey = any(p.shows_windows for p in self._plugins)
        logger.info('will call waitkey: %s' % call_cvwaitkey)

        all_grey_plugins = not any(p.uses_color for p in self._plugins)
        logger.info('plugins all use grey images: %s' % all_grey_plugins)

        self._run = True
        try:

            execution_times = collections.OrderedDict({'Acquire':time.time()})
            for p in self._plugins:
                execution_times[p.identifier] = time.time()
            execution_times['TOTAL'] = time.time()

            capture_is_color = None

            while self._run:
                now0 = time.time()

                # grab frame
                try:
                    frame = self.frame_capture.grab_next_frame()
                    execution_times['Acquire'] = time.time() - now0
                except EOFError as e:
                    logger.info(e.message)
                    self.stop()
                    continue
                except self.frame_capture_noncritical_errors as e:
                    logger.exception("error when retrieving frame")
                    continue

                if frame is None:
                    logger.exception("error when retrieving frame")
                    continue

                if capture_is_color is None:
                    #protect against empty last dimensions
                    capture_is_color = (frame.shape[-1] == 3) & (frame.ndim == 3)

                if capture_is_color and all_grey_plugins:
                    buf = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                else:
                    buf = frame

                state = {}
                state['FRAME_ORIGINAL'] = frame
                state['FRAME_METADATA'] = self.frame_capture.get_last_metadata()
                state['KEY'] = None

                frame_timestamp = self.frame_capture.get_last_timestamp()
                frame_number = self.frame_capture.get_last_framenumber()

                # warn if frames were skipped
                skip = frame_number - self.frame_number_current
                if skip != 1:
                    logger.warning('skipped %d frames' % skip)
                self.frame_number_current = frame_number

                self.frame_count += 1

                finished_plugins = []
                now = time.time()
                for plugin in self._plugins:
                    if self.frame_number_current % plugin.every == 0:
                        cn = plugin.identifier
                        try:
                            plugin.tick()
                            ret = plugin.push_frame(buf, frame_number, self.frame_count, frame_timestamp, now, state, self._framestores)
                            plugin.tock()

                            dbg_s = [cn]

                            # if ret is False, the non-blocking plugin was
                            # still processing the old frame.
                            # if it is None then the plugin didn't return
                            # anything useful
                            # if is a 2-tuple then it is a frame and a dict
                            if ret is not None:
                                ret_state = {}
                                if ret is False:
                                    dbg_s.append('BUSY')
                                elif isinstance(ret, tuple):
                                    buf, ret_state = ret
                                    dbg_s.append('returned img %r and state' % (buf.shape,))
                                elif isinstance(ret, dict):
                                    ret_state = ret
                                    dbg_s.append('returned state')
                                elif isinstance(ret, np.ndarray):
                                    buf = ret
                                    dbg_s.append('returned image %r' % (buf.shape,))

                                state.update(ret_state)
                                dbg_s.append('current state\n\t%s' % state.keys())

                            else:
                                dbg_s.append('returned None')

                            # print ' '.join(dbg_s)

                            execution_times[cn] = plugin.get_execution_time()

                        except PluginFinished:
                            logger.info("%s finished" % cn)
                            finished_plugins.append(plugin)

                if self._profile is not None:
                    execution_times['TOTAL'] = time.time() - now0

                for plugin in finished_plugins:
                    self.detach_plugin(plugin)
                    cn = plugin.identifier
                    execution_times.pop(cn)

                if self._profile is not None:
                    for et in execution_times:
                        self._profile_timestore[et].append(execution_times[et])
                    self._profile(execution_times, self._profile_timestore)

                if not self._plugins:
                    self.stop()

                if self._stop_frame and (self.frame_count > self._stop_frame):
                    self.stop()

                with self._lock:
                    if not self._run:
                        logger.info("exiting main loop")
                        break

                if call_cvwaitkey:
                    state['KEY'] = 0xFF & cv2.waitKey(self._waitkey_delay)
                elif self._waitkey_delay == 0:
                    raw_input('Press key to continue')



        finally:
            # stop the plugins
            for plugin in self._plugins:
                plugin.stop()
            for s in self._framestores:
                s.close()

        self.finished = True

    def stop(self):
        """stop the mainloop."""
        with self._lock:
            self._run = False

    def main(self):
        try:
            self.start()
            while not self.finished:
               time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
