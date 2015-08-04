"""microfview.main module

Provides Microfview class, which manages the frame capture
and delegates frames to all plugins.

"""
import bisect
import threading
import time
import collections

import cv2

import logging
logger = logging.getLogger('microfview')

from .plugin import PluginFinished

# helper function for frame_capture checks
def _has_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))


class Microfview(threading.Thread):

    def __init__(self, frame_capture, visible=True, debug=True, flipRL=False, flipUD=False):
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
        self.frame_number_current = -1

        self._run = False
        self._callbacks = []
        self._plugins = []

        self._callback_names = {}
        self._profile = None

        self._flip = flipRL or flipUD
        self._slice = (slice(None, None, -1 if flipUD else None),
                       slice(None, None, -1 if flipRL else None))

        self.finished = False

    def attach_profiler(self, callback_func, *callback_args):
        """Attaches a function to be called after every iteration that
        is passed a dictionary showing how long each plugin took to execute"""
        if not hasattr(callback_func, '__call__'):
            raise TypeError("callback_func has to be callable")
        self._profile = (callback_func, callback_args)

    def attach_callback(self, callback_func, every=1):
        """Attaches a callback function, which is called on every Nth frame.

        Args:
          callback_func:  takes three parameters (frame_timestamp, now, buf)
          every:  integer > 0

        returns:
          handle:  can be used to detach callback
        """
        if not hasattr(callback_func, '__call__'):
            raise TypeError("callback_func has to be callable")
        if not isinstance(every, int):
            raise TypeError("every has to be of type int")
        if every < 1:
            raise ValueError("every has to be bigger than 0")
        handle = (every, callback_func)
        if handle in self._callbacks:
            raise ValueError("callback_func, every combination exist.")
        bisect.insort(self._callbacks, handle)

        #get a readable name for the plugin
        cb_name = callback_func.func_name
        if cb_name == "push_frame":
            #the class name is more interesting as this is a plugin
            try:
                #classes can provide identifiers
                cb_name = callback_func.im_self.identifier
                if cb_name is None:
                    raise AttributeError
            except AttributeError:
                #otherwise the class name will do
                cb_name = callback_func.im_class.__name__
        logging.debug("attached callback %s %r" % (cb_name, callback_func))
        self._callback_names[callback_func] = cb_name

        return handle

    def detach_callback(self, handle):
        """Detaches a callback."""
        if handle in self._callbacks:
            self._callbacks.remove(handle)
        else:
            raise ValueError("handle not attached.")

    def attach_plugin(self, plugin):
        """Attaches a plugin."""
        # check if plugin provides the required methods and attributes
        if not (_has_method(plugin, 'start') and
                _has_method(plugin, 'stop') and
                _has_method(plugin, 'push_frame') and
                hasattr(plugin, 'every')):
            raise TypeError("plugin does not have the required methods/attributes.")
        self._plugins.append(plugin)
        handle = self.attach_callback(plugin.push_frame, every=plugin.every)
        logger.info('attaching plugin %s (shows_windows: %s)' % (plugin.identifier, plugin.shows_windows))
        return plugin, handle

    def detach_plugin(self, handle):
        """Detaches a plugin."""
        plugin, cb_handle = handle
        self._plugins.remove(plugin)
        self.detach_callback(cb_handle)

    def run(self):
        """main loop. do not call directly."""
        # start all plugins
        for plugin in self._plugins:
            plugin.set_debug(self._debug)
            plugin.set_visible(self._visible)
            plugin.start(self.frame_capture)

        call_cvwaitkey = any(p.shows_windows for p in self._plugins)
        logger.info('will call waitkey: %s' % call_cvwaitkey)

        self._run = True
        try:

            execution_times = collections.OrderedDict({n:time.time() for n in self._callback_names.values()})
            execution_times['TOTAL'] = time.time()

            state = {'KEY':None, 'ORIGINAL_FRAME':None}
            while self._run:
                now0 = time.time()

                # grab frame
                try:
                    buf = self.frame_capture.grab_next_frame()
                except EOFError as e:
                    logger.info(e.message)
                    self.stop()
                    continue
                except self.frame_capture_noncritical_errors as e:
                    logger.exception("error when retrieving frame")
                    continue

                if buf is None:
                    logger.exception("error when retrieving frame")
                    continue

                state['ORIGINAL_FRAME'] = buf

                frame_timestamp = self.frame_capture.get_last_timestamp()
                frame_number = self.frame_capture.get_last_framenumber()

                # warn if frames were skipped
                skip = frame_number - self.frame_number_current
                if skip != 1:
                    logger.warning('skipped %d frames' % skip)
                self.frame_number_current = frame_number

                self.frame_count += 1

                # flip
                if self._flip:
                    buf = buf[self._slice]

                finished_callback_handles = []
                now = time.time()
                # call all attached callbacks.
                for n, cb in self._callbacks:
                    if self.frame_number_current % n == 0:
                        cn = self._callback_names[cb]
                        try:
                            t0 = time.time()
                            ret = cb(buf, frame_number, self.frame_count, frame_timestamp, now, state)
                            t1 = time.time()

                            # if ret is False, the non-blocking plugin was
                            # still processing the old frame.
                            # if it is None then the plugin didn't return
                            # anything useful
                            # if it is a dictionary then it is state associated with
                            # that frame
                            if ret:
                                #fixme: save to database or csv except 'KEY', "ORIGINAL_FRAME'
                                pass

                            execution_times[cn] = t1 - t0

                        except PluginFinished:
                            logger.info("%s finished" % cn)
                            finished_callback_handles.append((n, cb))

                if self._profile is not None:
                    execution_times['TOTAL'] = time.time() - now0

                for handle in finished_callback_handles:
                    self.detach_callback(handle)
                    cn = self._callback_names[handle[1]]
                    execution_times.pop(cn)

                if not self._callbacks:
                    self.stop()

                with self._lock:
                    if not self._run:
                        logger.info("exiting main loop")
                        break

                if self._profile is not None:
                    #pass on the callback args
                    self._profile[0](execution_times, *self._profile[1])

                if call_cvwaitkey:
                    state['KEY'] = 0xFF & cv2.waitKey(1)


        finally:
            # stop the plugins
            for plugin in self._plugins:
                plugin.stop()

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
