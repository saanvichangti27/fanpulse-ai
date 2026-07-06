import json
import asyncio
import logging
from datetime import datetime, timezone
import os

from ..contracts import RawMessageIn

logger = logging.getLogger(__name__)

class ReplayController:
    def __init__(self):
        self._running_tasks = {}

    async def _replay_loop(self, key: tuple, match_id: str, file_path: str, speed: float,
                           out_queue: asyncio.Queue, loop: bool = False):
        logger.info(f"Starting replay for match {match_id} from {file_path} at {speed}x speed"
                    f"{' (looping)' if loop else ''}.")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            items = data.get("items", [])
            if not items:
                logger.warning("No items in replay file.")
                return

            iteration = 0
            while True:
                # Start time baseline (per pass)
                start_time = asyncio.get_event_loop().time()
                base_offset = items[0].get("t_offset", 0)

                for item in items:
                    target_offset_real = (item["t_offset"] - base_offset) / speed
                    elapsed = asyncio.get_event_loop().time() - start_time
                    wait_time = target_offset_real - elapsed

                    if wait_time > 0:
                        await asyncio.sleep(wait_time)

                    # Check for cancellation
                    if key not in self._running_tasks:
                        logger.info(f"Replay {key} stopped.")
                        return

                    # Inject match_id so markers/messages route to the right match
                    if isinstance(item, dict) and "match_id" not in item:
                        item = {**item, "match_id": match_id}
                    # Looping passes need fresh external_ids or the DB's
                    # (source, external_id) dedupe drops every repeat.
                    if iteration > 0 and isinstance(item, dict) and "external_id" in item:
                        item = {**item, "external_id": f"{item['external_id']}-L{iteration}"}
                    await out_queue.put(item)

                if not loop or key not in self._running_tasks:
                    break
                iteration += 1
                logger.info(f"Replay {key} pass {iteration} complete — looping.")

        except asyncio.CancelledError:
            logger.info(f"Replay task cancelled: {key}")
        except Exception as e:
            logger.error(f"Error during replay: {e}")
        finally:
            self._running_tasks.pop(key, None)

    def start(self, match_id: str, file: str, speed: float, out_queue: asyncio.Queue,
              loop: bool = False):
        # Keyed by (match_id, file) so multiple SOURCES can replay concurrently
        # for the same match (e.g. YouTube capture + simulated Twitter stream).
        key = (match_id, file)
        if key in self._running_tasks:
            logger.warning(f"Replay {key} is already running.")
            return

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        file_path = os.path.join(base_dir, "data", "replay", file)
        if not os.path.exists(file_path):
            logger.error(f"Replay file not found: {file_path}")
            print(f"ERROR: Replay file not found: {file_path}")
            return

        task = asyncio.create_task(self._replay_loop(key, match_id, file_path, speed, out_queue, loop))
        self._running_tasks[key] = task

    def stop(self, match_id: str, file: str | None = None):
        """Stop one replay (match_id + file) or every replay for the match."""
        keys = [k for k in list(self._running_tasks)
                if k[0] == match_id and (file is None or k[1] == file)]
        for k in keys:
            task = self._running_tasks.pop(k, None)
            if task and not task.done():
                task.cancel()
