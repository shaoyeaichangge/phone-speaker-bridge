"""Exercise startup and recovery without opening an audio device or killing processes."""
import asyncio
from pathlib import Path
import socket
import sys
import threading
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class PortTests(unittest.TestCase):
    def test_free_port_is_released_after_check(self):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        server.check_port_available(port)
        with socket.socket() as listener:
            listener.bind(("0.0.0.0", port))

    def test_occupied_port_is_reported_and_listener_survives(self):
        with socket.socket() as listener:
            listener.bind(("0.0.0.0", 0))
            listener.listen()
            port = listener.getsockname()[1]
            with self.assertRaisesRegex(SystemExit, "choose another port"):
                server.check_port_available(port)
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                accepted, _ = listener.accept()
                accepted.close()

    def test_invalid_port_is_rejected(self):
        for port in (0, -1, 65536):
            with self.subTest(port=port), self.assertRaises(SystemExit):
                server.check_port_available(port)

    def test_list_devices_does_not_check_or_start_server(self):
        with patch.object(sys, "argv", ["server.py", "--list-devices"]), \
                patch.object(server, "list_loopback_devices") as listing, \
                patch.object(server, "check_port_available") as port_check, \
                patch.object(server, "tune_windows_scheduling") as tune:
            server.main()
        listing.assert_called_once_with()
        port_check.assert_not_called()
        tune.assert_not_called()


class RecoveryTests(unittest.TestCase):
    def make_capture(self, failures):
        capture = server.LoopbackCapture.__new__(server.LoopbackCapture)
        capture._running = True
        capture._pa = Mock()
        capture._stream = Mock()
        capture._stream.read.side_effect = OSError("temporary device failure")
        capture.device = {"index": 7, "name": "test loopback"}
        capture.rate, capture.channels = 48000, 2
        capture.samples_per_chunk = 960
        capture._sub_lock = threading.Lock()
        receiver = asyncio.Queue(maxsize=1)
        capture._subscribers = {receiver}
        capture._loop = Mock()

        def deliver(callback, queue, chunk):
            callback(queue, chunk)
            capture._running = False

        capture._loop.call_soon_threadsafe.side_effect = deliver
        recovered_stream = Mock()
        recovered_stream.read.return_value = b"recovered audio"
        capture._pa.open.side_effect = [OSError("still unavailable")] * failures + [recovered_stream]
        return capture, receiver, recovered_stream

    def test_capture_reopens_and_delivers_audio(self):
        capture, receiver, recovered = self.make_capture(failures=1)
        broken = capture._stream
        with patch.object(server.time, "sleep"), \
                patch.object(server, "_boost_capture_thread_priority"), \
                patch.object(server, "log"):
            capture._run()
        broken.stop_stream.assert_called_once()
        broken.close.assert_called_once()
        self.assertEqual(capture._pa.open.call_count, 2)
        self.assertIs(capture._stream, recovered)
        self.assertEqual(receiver.get_nowait(), b"recovered audio")

    def test_capture_keeps_retrying_after_first_thirty_failures(self):
        capture, receiver, _ = self.make_capture(failures=30)
        with patch.object(server.time, "sleep"), \
                patch.object(server, "_boost_capture_thread_priority"), \
                patch.object(server, "log"):
            capture._run()
        self.assertEqual(capture._pa.open.call_count, 31)
        self.assertEqual(receiver.get_nowait(), b"recovered audio")


if __name__ == "__main__":
    unittest.main()
