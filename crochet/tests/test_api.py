"""
Tests for the crochet APIs.
"""

import threading
import time

from twisted.trial.unittest import TestCase
from twisted.internet.defer import succeed, Deferred, fail

from crochet import _Crochet, DeferredResult, TimeoutError


class DeferredResultTests(TestCase):
    """
    Tests for DeferredResult.
    """

    def test_success_result(self):
        """
        result() returns the value the Deferred fired with.
        """
        dr = DeferredResult(succeed(123))
        self.assertEqual(dr.result(), 123)

    def test_later_success_result(self):
        """
        result() returns the value the Deferred fired with, in the case where
        the Deferred is fired after result() is called.
        """
        d = Deferred()
        def fireSoon():
            import time; time.sleep(0.01)
            d.callback(345)
        threading.Thread(target=fireSoon).start()
        dr = DeferredResult(d)
        self.assertEqual(dr.result(), 345)

    def test_success_result_twice(self):
        """
        A second call to result() returns same value as the first call.
        """
        dr = DeferredResult(succeed(123))
        self.assertEqual(dr.result(), 123)
        self.assertEqual(dr.result(), 123)

    def test_failure_result(self):
        """
        result() raises the exception the Deferred fired with.
        """
        dr = DeferredResult(fail(RuntimeError()))
        self.assertRaises(RuntimeError, dr.result)

    def test_later_failure_result(self):
        """
        result() raises the exception the Deferred fired with, in the case
        where the Deferred is fired after result() is called.
        """
        d = Deferred()
        def fireSoon():
            time.sleep(0.01)
            d.errback(RuntimeError())
        threading.Thread(target=fireSoon).start()
        dr = DeferredResult(d)
        self.assertRaises(RuntimeError, dr.result)

    def test_failure_result_twice(self):
        """
        A second call to result() raises same value as the first call.
        """
        dr = DeferredResult(fail(ZeroDivisionError()))
        self.assertRaises(ZeroDivisionError, dr.result)
        self.assertRaises(ZeroDivisionError, dr.result)

    def test_timeout(self):
        """
        If no result is available, result(timeout) will throw a TimeoutError.
        """
        start = time.time()
        dr = DeferredResult(Deferred())
        self.assertRaises(TimeoutError, dr.result, timeout=0.03)
        self.assertTrue(abs(time.time() - start - 0.03) < 0.005)

    def test_timeout_twice(self):
        """
        If no result is available, a second call to result(timeout) will also
        result in a TimeoutError exception.
        """
        dr = DeferredResult(Deferred())
        self.assertRaises(TimeoutError, dr.result, timeout=0.01)
        self.assertRaises(TimeoutError, dr.result, timeout=0.01)

    def test_timeout_then_result(self):
        """
        If a result becomes available after a timeout, a second call to
        result() will return it.
        """
        d = Deferred()
        dr = DeferredResult(d)
        self.assertRaises(TimeoutError, dr.result, timeout=0.01)
        d.callback(u"value")
        self.assertEqual(dr.result(), u"value")
        self.assertEqual(dr.result(), u"value")


class InEventLoopTests(TestCase):
    """
    Tests for the in_event_loop decorator.
    """
