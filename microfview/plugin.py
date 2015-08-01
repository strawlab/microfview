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


class PluginFinished(Exception):
    pass


class _Plugin(object):

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

    def start(self, capture_object):
        """compatibility function."""
        pass

    def stop(self):
        """compatibility function."""
        pass

    def process_frame(self, frame, frame_number, frame_count, frame_time, current_time, state):
        """override this function."""
        pass

    def push_frame(self, frame, frame_number, frame_count, frame_time, current_time, state):
        raise NotImplementedError


class PluginChain(_Plugin):

    def __init__(self, plugins, every=1, logger=None):
        super(PluginChain, self).__init__(every, logger)
        if not isinstance(plugins, tuple):
            raise ValueError('plugins must be a tuple')
        self._plugins = list(plugins)

    def start(self, capture_object):
        map(lambda x: x.start(capture_object), self._plugins)

    def stop(self):
        """compatibility function."""
        map(lambda x: x.stop(), self._plugins)

    def push_frame(self, frame, frame_number, frame_count, frame_time, current_time, state):
        """override this function."""
        finished = []
        ret = state or dict()

        if not self._plugins:
            raise PluginFinished

        for p in self._plugins:
            try:
                _ret = p.process_frame(frame, frame_number, frame_count, frame_time, current_time, ret)
                if _ret:
                    ret.update(_ret)
            except PluginFinished:
                finished.append(p)

        map(lambda x: self._plugins.remove(x), finished)

        return ret


class BlockingPlugin(_Plugin):

    def push_frame(self, *callargs):
        """compatibility function."""
        return self.process_frame(*callargs)


class NonBlockingPlugin(_Plugin, threading.Thread):

    def __init__(self, every=1, max_start_delay_sec=0.001, logger=None):
        """NonBlockingPlugin.

        Starts a worker thread that listens for incoming frames.

        Args:
          every (int): process_frame gets called every Nth frame.
          max_start_delay_sec (float): spins the workerthread on this
            timescale. Defaults to 0.001 sec.

        """
        _Plugin.__init__(self, every, logger)
        threading.Thread.__init__(self)
        self.daemon = True
        self._frame_available = False
        self._lock = threading.Lock()
        self._idle_wait = float(max_start_delay_sec)
        self._callargs = (None, None, None, None, None, None)
        self._ret = None

    def start(self, capture_object):
        threading.Thread.start(self)

    def stop(self):
        """stop the worker thread."""
        with self._lock:
            self._run = False

    def push_frame(self, *callargs):
        """push a frame to the worker queue.

        Returns True if the queue is empty. False if the worker thread is still
        processing a frame.

        """
        with self._lock:
            frame_available = self._frame_available
        if frame_available:
            return False
        else:
            self._callargs = callargs
            with self._lock:
                self._frame_available = True
            return self._ret

    def run(self):
        """worker mainloop."""
        self.logger.info("starting worker")
        self._run = True
        while not self.finished:
            with self._lock:
                frame_available = self._frame_available
                # also need to copy the args here
                if not self._run:
                    self.logger.info("exiting worker")
                    break
            if not frame_available:
                time.sleep(self._idle_wait)
                continue
            try:
                self._ret = self.process_frame(*self._callargs)
            except PluginFinished:
                self.finished = True
            except:
                self.logger.exception("error in process_frame")
            with self._lock:
                self._frame_available = False

