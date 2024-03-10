"""
    Copyright (c) 2016, 2017, 2019 Timothy Savannah All Rights Reserved.

    Licensed under the Lesser GNU Public License Version 3, LGPLv3. You should have recieved a copy of this with the source distribution as
    LICENSE, otherwise it is available at https://github.com/kata198/func_timeout/LICENSE
"""

import os
import ctypes
import threading

__all__ = ("StoppableThread", "JoinThread")


class StoppableThread(threading.Thread):
    """
    StoppableThread - A thread that can be stopped by forcing an exception in the execution context.

      This works both to interrupt code that is in C or in python code, at either the next call to a python function,
       or the next line in python code.

    It is recommended that if you call stop ( @see StoppableThread.stop ) that you use an exception that inherits BaseException, to ensure it likely isn't caught.

     Also, beware unmarked exception handlers in your code. Code like this:

        while True:
            try:
                doSomething()
            except:
                continue

    will never be able to abort, because the exception you raise is immediately caught.

    The exception is raised over and over, with a specifed delay (default 2.0 seconds)
    """

    def _stopThread(self, raise_every: float):
        """
        _stopThread - @see StoppableThread.stop
        """
        if self.is_alive() is False:
            return True

        self._stderr = open(os.devnull, "w")

        # Create "joining" thread which will raise the provided exception
        #  on a repeat, until the thread stops.
        join_thread = JoinThread(self, repeat_every=raise_every)

        # Try to prevent spurrious prints
        join_thread._stderr = self._stderr
        join_thread.start()
        join_thread._stderr = self._stderr
        join_thread.join(0.5)

    def stop(self, raise_every=2.0):
        """
        Stops the thread by raising a given exception.

        @param exception <Exception type> - Exception to throw. Likely, you want to use something

          that inherits from BaseException (so except Exception as e: continue; isn't a problem)

          This should be a class/type, NOT an instance, i.e.  MyExceptionType   not  MyExceptionType()


        @param raiseEvery <float> Default 2.0 - We will keep raising this exception every #raiseEvery seconds,

            until the thread terminates.

            If your code traps a specific exception type, this will allow you #raiseEvery seconds to cleanup before exit.

            If you're calling third-party code you can't control, which catches BaseException, set this to a low number

              to break out of their exception handler.


         @return <None>
        """
        return self._stopThread(raise_every)


class JoinThread(threading.Thread):
    """
    JoinThread - The workhouse that stops the StoppableThread.

        Takes an exception, and upon being started immediately raises that exception in the current context
          of the thread's execution (so next line of python gets it, or next call to a python api function in C code ).

        @see StoppableThread for more details
    """

    def __init__(self, other_thread: threading.Thread, repeat_every: float):
        """
        __init__ - Create a JoinThread (don't forget to call .start() ! )

            @param otherThread <threading.Thread> - A thread

            @param exception <BaseException> - An exception. Should be a BaseException, to prevent "catch Exception as e: continue" type code
              from never being terminated. If such code is unavoidable, you can try setting #repeatEvery to a very low number, like .00001,
              and it will hopefully raise within the context of the catch, and be able to break free.

            @param repeatEvery <float> Default 2.0 - After starting, the given exception is immediately raised. Then, every #repeatEvery seconds,
              it is raised again, until the thread terminates.
        """
        threading.Thread.__init__(self)
        self.other_thread = other_thread
        self.repeat_every = repeat_every
        self.daemon = True

    def run(self):
        """
        run - The thread main. Will attempt to stop and join the attached thread.
        """
        # Try to silence default exception printing.
        self.other_thread._Thread__stderr = self._stderr

        while self.other_thread.is_alive():
            # We loop raising exception incase it's caught hopefully this breaks us far out.
            self._async_raise(self.other_thread.ident)
            self.other_thread.join(self.repeat_every)
        try:
            self._stderr.close()
        except:
            pass

    @staticmethod
    def _async_raise(tid: int):
        """raises the exception, performs cleanup if needed"""
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")
