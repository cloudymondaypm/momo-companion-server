import time
import asyncio
from collections import deque
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class AudioRateController:
    """
    Audio rate controller - precisely pace 60 ms audio frames
    Avoid accumulated timing errors under high concurrency
    """

    def __init__(self, frame_duration=60, send_delay=0):
        """
        Args:
            frame_duration: Audio frame duration (ms), defaults to 60 ms
            send_delay: Custom send interval (ms).
                        0 = Pace according to frame_duration；
                        >0 = Pace according to send_delay (no main-thread queue delay or prebuffer)
        """
        # Flow-control interval (ms): use send_delay if positive, else frame_duration
        self.interval_ms = send_delay if send_delay > 0 else frame_duration
        self.queue = deque()
        self.play_position = 0  # Virtual playback position (ms)
        self.start_timestamp = None  # Start timestamp (read-only)
        self.pending_send_task = None
        self.logger = logger
        self.queue_empty_event = asyncio.Event()  # Queue-empty event
        self.queue_empty_event.set()  # Initially empty
        self.queue_has_data_event = asyncio.Event()  # Queue-data event
        self._last_queue_empty_time = 0  # Last queue-empty time (seconds)

    def reset(self):
        """Reset controller state"""
        if self.pending_send_task and not self.pending_send_task.done():
            self.pending_send_task.cancel()
            # After cancellation, task cleans up on next event loop tick; no blocking wait needed

        self.queue.clear()
        self.play_position = 0
        self.start_timestamp = None  # Set by first audio packet
        self._last_queue_empty_time = 0  # Reset time
        # Related event handling
        self.queue_empty_event.set()
        self.queue_has_data_event.clear()

    def add_audio(self, opus_packet):
        """Add audio packet to queue"""
        # If queue was empty, adjust timestamp to preserve continuous playback
        # Prevent newly enqueued audio from playing too early while waiting for tools
        # A short gap (less than one frame) is normal streaming and needs no reset
        if len(self.queue) == 0 and self.play_position > 0:
            elapsed_since_empty = (time.monotonic() - self._last_queue_empty_time) * 1000
            # Consider pause/resume only if gap exceeds one frame
            if elapsed_since_empty >= self.interval_ms:
                self.start_timestamp = time.monotonic() - (self.play_position / 1000)
                self.logger.bind(tag=TAG).debug(
                    f"Queue resumed after empty; resetting timestamp at playback position: {self.play_position}ms, gap: {elapsed_since_empty:.0f}ms"
                )

        self.queue.append(("audio", opus_packet))
        # Related event handling
        self.queue_empty_event.clear()
        self.queue_has_data_event.set()

    def add_message(self, message_callback):
        """
        Queue message (send immediately; does not consume playback time)

        Args:
            message_callback: Message sending callback, async def()
        """
        if len(self.queue) == 0 and self.play_position > 0:
            elapsed_since_empty = (time.monotonic() - self._last_queue_empty_time) * 1000
            if elapsed_since_empty >= self.interval_ms:
                self.start_timestamp = time.monotonic() - (self.play_position / 1000)
                self.logger.bind(tag=TAG).debug(
                    f"Queue resumed after empty; resetting timestamp at playback position: {self.play_position}ms, gap: {elapsed_since_empty:.0f}ms"
                )

        self.queue.append(("message", message_callback))
        # Related event handling
        self.queue_empty_event.clear()
        self.queue_has_data_event.set()

    def _get_elapsed_ms(self):
        """Get elapsed time (ms)"""
        if self.start_timestamp is None:
            return 0
        return (time.monotonic() - self.start_timestamp) * 1000

    async def check_queue(self, send_audio_callback):
        """
        Check queue and send audio/messages on schedule

        Args:
            send_audio_callback: Audio sending callback, async def(opus_packet)
        """
        while self.queue:
            item = self.queue[0]
            item_type = item[0]

            if item_type == "message":
                # Message: send immediately without using playback time
                _, message_callback = item
                self.queue.popleft()
                try:
                    await message_callback()
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Failed to send message: {e}")
                    raise

            elif item_type == "audio":
                if self.start_timestamp is None:
                    self.start_timestamp = time.monotonic()

                _, opus_packet = item

                # Wait in a loop until scheduled time
                while True:
                    # Calculate time difference
                    elapsed_ms = self._get_elapsed_ms()
                    output_ms = self.play_position

                    if elapsed_ms < output_ms:
                        # Determine remaining wait time
                        wait_ms = output_ms - elapsed_ms

                        # Check again after wait (interruptible)
                        try:
                            await asyncio.sleep(wait_ms / 1000)
                        except asyncio.CancelledError:
                            self.logger.bind(tag=TAG).debug("Audio sending task cancelled")
                            raise
                        # Recheck time after wait (loop to while True)
                    else:
                        # Exit wait loop when scheduled time arrives
                        break

                # Dequeue and send at scheduled time
                self.queue.popleft()
                self.play_position += self.interval_ms
                try:
                    await send_audio_callback(opus_packet)
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Failed to send audio: {e}")
                    raise

        # Clear event after queue processed
        self.queue_empty_event.set()
        self.queue_has_data_event.clear()
        self._last_queue_empty_time = time.monotonic()  # Record queue-empty time

    def start_sending(self, send_audio_callback):
        """
        Start asynchronous sending task

        Args:
            send_audio_callback: Audio sending callback

        Returns:
            asyncio.Task: Sending task
        """

        async def _send_loop():
            try:
                while True:
                    # Wait on queue-data event instead of CPU polling
                    await self.queue_has_data_event.wait()

                    await self.check_queue(send_audio_callback)
            except asyncio.CancelledError:
                self.logger.bind(tag=TAG).debug("Audio sending loop stopped")
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"Audio sending loop error: {e}")

        self.pending_send_task = asyncio.create_task(_send_loop())
        return self.pending_send_task

    def stop_sending(self):
        """Stop sending task"""
        if self.pending_send_task and not self.pending_send_task.done():
            self.pending_send_task.cancel()
            self.logger.bind(tag=TAG).debug("Audio sending task cancelled")
