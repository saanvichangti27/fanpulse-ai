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

    async def _replay_loop(self, match_id: str, file_path: str, speed: float, out_queue: asyncio.Queue):
        logger.info(f"Starting replay for match {match_id} from {file_path} at {speed}x speed.")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            items = data.get("items", [])
            if not items:
                logger.warning("No items in replay file.")
                return

            # Start time baseline
            start_time = asyncio.get_event_loop().time()
            base_offset = items[0].get("t_offset", 0)

            for item in items:
                target_offset_real = (item["t_offset"] - base_offset) / speed
                elapsed = asyncio.get_event_loop().time() - start_time
                wait_time = target_offset_real - elapsed
                
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                
                # Check for cancellation
                if match_id not in self._running_tasks:
                    logger.info(f"Replay for {match_id} stopped.")
                    break
                    
                # Put item in queue (could be message or marker)
                await out_queue.put(item)
                
        except asyncio.CancelledError:
            logger.info(f"Replay task cancelled for {match_id}")
        except Exception as e:
            logger.error(f"Error during replay: {e}")
        finally:
            self.stop(match_id)

    def start(self, match_id: str, file: str, speed: float, out_queue: asyncio.Queue):
        if match_id in self._running_tasks:
            logger.warning(f"Replay for {match_id} is already running.")
            return
            
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        file_path = os.path.join(base_dir, "data", "replay", file)
        if not os.path.exists(file_path):
            logger.error(f"Replay file not found: {file_path}")
            print(f"ERROR: Replay file not found: {file_path}")
            return
            
        task = asyncio.create_task(self._replay_loop(match_id, file_path, speed, out_queue))
        self._running_tasks[match_id] = task

    def stop(self, match_id: str):
        task = self._running_tasks.pop(match_id, None)
        if task and not task.done():
            task.cancel()
