"""microfview.plugin module

Provides to classes from which you can derive your own Plugins.

BlockingPlugin:
  Derive from BlockingPlugin and override method process_frame to get
  a Plugin which blocks the Microfview mainloop when running
  process_frame.

NonBlockingPlugin:
  Derive from NonBlockingPlugin and override method process_frame to
  get a Plugin which does not block the Microfview mainloop when running
  process_frame. But it skips a frame if process_frame did not return
  before the next incoming frame.

"""
import threading
import time
import logging
import Queue

import cv2
import numpy as np


class PluginFinished(Exception):
    pass


class _Plugin(object):
    """Base class for

    Attributes:
        every (int): Call this plugin every this many frames
        logger : logging object
        finished (bool) : true if this plugin should quit
        shows_windows (bool) : true if this plugin shows an cv2 window
        uses_color (bool) : true if this plugin uses color information
        human_name (string) : human readable name of this plugin
        uid (string) : code identifying this plugin in the main application hierarchy
    """

    def __init__(self, every=1, logger=None):
        """BlockingPlugin.

        Args:
          every (int): process_frame gets called every Nth frame.

        """
        if logger is None:
            logger = logging.getLogger('microfview')
        self.logger = logger
        self.every = int(every)

        self.finished = False
        self.shows_windows = False
        self.debug = False
        self.visible = True
        self.uses_color = False
        self.human_name = self.__class__.__name__

        self.return_frame = True
        self.return_state = True
        self.threaded = False

        self._t0 = self._t1 = np.nan
        self._uid = "UNKNOWN"

    @property
    def identifier(self):
        return "%s:%s" % (self._uid, self.human_name)

    def set_uid(self, uid):
        self._uid = uid

    def get_uid(self):
        return self._uid

    def get_execution_time(self):
        return self._t1 - self._t0

    def tick(self):
        self._t0 = time.time()

    def tock(self):
        self._t1 = time.time()

    def set_debug(self, d):
        self.debug = d

    def set_visible(self, v):
        self.visible = v

    def debug_window_name(self, name):
        if self._uid == "UNKNOWN":
            self.logger.critical("construct windows in start() as they need uids")
        return "%s:%s" % (self._uid, name)

    def debug_window_create(self, name, size, resizable=True):
        """
        creates a debug window that may be used to show debug images later

        :param name: name of window
        :param size: size of window (if known, or None if not known)
        :param resizable: whether the window should be resizable if possible
        """
        if self.debug:
            name = self.debug_window_name(name)
            if resizable and (size is not None):
                cv2.namedWindow(name, getattr(cv2,'WINDOW_NORMAL',0))
                if (size[0] > 0) and (not np.isnan(size[0])):
                    # some videos don't know their size...
                    cv2.resizeWindow(name, *map(int, size))
            else:
                cv2.namedWindow(name, getattr(cv2, 'WINDOW_AUTOSIZE', 1))
            return name

    def debug_window_show(self, name, img):
        if self.debug and (img is not None):
            name = self.debug_window_name(name)
            cv2.imshow(name, img)

    def debug_window_destroy(self, name):
        if self.debug:
            name = self.debug_window_name(name)
            cv2.destroyWindow(name)

    def start(self, capture_object):
        """compatibility function."""
        pass

    def stop(self):
        """compatibility function."""
        pass

    def process_frame(self, frame, frame_number, frame_count, frame_time, current_time, state):
        """override this function."""
        pass

    def push_frame(self, frame, frame_number, frame_count, frame_time, current_time, state, stores):
        raise NotImplementedError

    def get_schema(self):
        """optionally return a dict describing any data hat is returned for this frame"""
        return {}


class FuncWrapperPlugin(_Plugin):
    def __init__(self, func, name, every=1):
        super(FuncWrapperPlugin, self).__init__(every=every)
        self._func = func
        self.human_name = name

    def __eq__(self, other):
        return isinstance(other, FuncWrapperPlugin) and (self._func == other._func) and (self.every == other.every)

    def push_frame(self, frame, frame_number, frame_count, frame_time, current_time, state, stores):
        return self._func(frame, frame_number, frame_count, frame_time, current_time, state)


class PluginChain(_Plugin, threading.Thread):

    def __init__(self, *plugins, **kwargs):
        _Plugin.__init__(self, every=kwargs.get('every', 1), logger=kwargs.get('logger', None))
        threading.Thread.__init__(self)
        self.daemon = True

        if not isinstance(plugins, tuple):
            raise ValueError('plugins must be a tuple')

        self.human_name = "%s(%s)" % (self.__class__.__name__, kwargs.get('name', ''))
        self.shows_windows = any(p.shows_windows for p in plugins)
        self.uses_color = any(p.uses_color for p in plugins)
        self.return_frame = kwargs.get('return_frame', False)
        self.return_state = kwargs.get('return_state', True)

        self._plugins = list(plugins)
        self._arg_queue = Queue.Queue(maxsize=1)
        self._res_queue = Queue.Queue(maxsize=1)
        self._res_queue.put(False)
        self._et = np.nan

        if ('return_last_frame' in kwargs) or ('return_last_state' in kwargs):
            raise ValueError("UPDATE YOUR CODE")

    def set_uid(self, v):
        self._uid = v
        for i, plugin in enumerate(self._plugins):
            plugin.set_uid("%s.%s" % (self._uid, i))

    def get_schema(self):
        schema = {}
        for p in self._plugins:
            schema.update(p.get_schema())
        return schema

    def set_debug(self, d):
        map(lambda x: x.set_debug(d), self._plugins)

    def set_visible(self, v):
        map(lambda x: x.set_visible(v), self._plugins)

    def start(self, capture_object):
        map(lambda x: x.start(capture_object), self._plugins)
        if self.threaded:
            threading.Thread.start(self)
            logging.debug('plugin %s started thread' % self.identifier)

    def stop(self):
        """compatibility function."""
        map(lambda x: x.stop(), self._plugins)
        if self.threaded:
            self._arg_queue.put(None)
            self.join()

    def get_execution_time(self):
        if self.threaded:
            return self._et
        else:
            return self._t1 - self._t0

    def run(self):
        while True:
            args = self._arg_queue.get()
            # thread was quit
            if args is None:
                break
            else:
                try:
                    t0 = time.time()
                    self._res_queue.put(self._call_plugins(*args))
                    self._et = time.time() - t0
                except Exception as e:
                    self.logger.warn(e.message, exc_info=True)
                    self._res_queue.put(e)
                    break

    def _call_plugins(self, frame, frame_number, frame_count, frame_time, current_time, state):
        for p in self._plugins:
            ret = p.process_frame(frame, frame_number, frame_count, frame_time, current_time, state)
            # if ret is False, the non-blocking plugin was
            # still processing the old frame.
            # if it is None then the plugin didn't return
            # anything useful
            # if is a 2-tuple then it is a frame and a dict
            if ret is not None:
                ret_state = {}
                if ret is False:
                    self.logger.warn("non-blocking plugins in chain not supported")
                elif isinstance(ret, tuple):
                    frame, ret_state = ret
                elif isinstance(ret, dict):
                    ret_state = ret
                elif isinstance(ret, np.ndarray):
                    frame = ret
                state.update(ret_state)
        return frame, state

    def push_frame(self, frame, frame_number, frame_count, frame_time, current_time, state, stores):
        if self.threaded:
            ret = self._res_queue.get()
            # re-raise exceptions (such as PluginFinished) back to the main thread
            if isinstance(ret, Exception):
                raise ret
            # fixme: copy state and frame??
            self._arg_queue.put((frame, frame_number, frame_count, frame_time, current_time, state))
        else:
            ret = self._call_plugins(frame, frame_number, frame_count, frame_time, current_time, state)

        ret_state = {}
        if isinstance(ret, tuple):
            frame, ret_state = ret
        elif isinstance(ret, dict):
            ret_state = ret
        elif isinstance(ret, np.ndarray):
            frame = ret
        if ret_state:
            for s in stores:
                s.store(self.identifier, frame, frame_number, frame_count, frame_time, current_time, ret_state)

        if self.return_frame and self.return_state:
            return frame, ret_state
        elif self.return_frame:
            return frame
        elif self.return_state:
            return ret_state
        else:
            return None


class BlockingPlugin(_Plugin):

    def push_frame(self, frame, frame_number, frame_count, frame_time, current_time, state, stores):
        ret = self.process_frame(frame, frame_number, frame_count, frame_time, current_time, state)
        if ret is not None:
            ret_state = {}
            if isinstance(ret, tuple):
                frame, ret_state = ret
            elif isinstance(ret, dict):
                ret_state = ret
            elif isinstance(ret, np.ndarray):
                frame = ret
            if ret_state:
                for s in stores:
                    s.store(self.identifier, frame, frame_number, frame_count, frame_time, current_time, ret_state)
            return frame, ret_state
        return None


class NonBlockingPlugin(_Plugin, threading.Thread):

    def __init__(self, every=1, logger=None):
        """NonBlockingPlugin.

        Starts a worker thread that listens for incoming frames. If a new
        frame arrives and the plugin is still processing the old frame, the
        new plugin is dropped.

        Args:
          every (int): process_frame gets called every Nth frame.
        """
        _Plugin.__init__(self, every, logger)
        threading.Thread.__init__(self)
        self.daemon = True
        self._arg_queue = Queue.Queue(maxsize=1)
        self._res_queue = Queue.Queue(maxsize=1)
        self._et = np.nan

        self.threaded = True

    # we manage our own t0 and t1 based on the real time of execution
    def tick(self): pass
    def tock(self): pass
    def get_execution_time(self):
        return self._et

    def start(self, capture_object):
        threading.Thread.start(self)
        logging.debug('plugin %s started thread' % self.identifier)

    def stop(self):
        """stop the worker thread."""
        # block to make sure the thread finishes
        self._arg_queue.put(None)
#        self.join()
    
    def push_frame(self, frame, frame_number, frame_count, frame_time, current_time, state, stores):
        """push a frame to the worker queue.

        Returns False if the worker thread is still processing the last frame.
        """
        try:
            self._arg_queue.put_nowait((frame, frame_number, frame_count, frame_time, current_time, state))
        except Queue.Full:
            # drop new frames if we are busy
            pass
        try:
            ret_state = {}
            ret = self._res_queue.get_nowait()
            if isinstance(ret, tuple):
                frame, ret_state = ret
            elif isinstance(ret, dict):
                ret_state = ret
            elif isinstance(ret, np.ndarray):
                frame = ret
            if ret_state:
                for s in stores:
                    s.store(self.identifier, frame, frame_number, frame_count, frame_time, current_time, ret_state)
            return frame, ret_state
        except Queue.Empty:
            # we are still busy
            return False
            

    def run(self):
        while True:
            args = self._arg_queue.get()
            #thread was quit
            if args is None:
                break
            else:
                t0 = time.time()
                self._res_queue.put(self.process_frame(*args))
                self._et = time.time() - t0

