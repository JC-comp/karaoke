import json
import time

from redis import Redis
from ...datatype import QueueItem

DEFAULT_ROOM_STATE = {
    'is_fullscreen': True,
    'is_playing': True,
    'is_vocal_on': False,
    'volume': 100,
    'version': 0
}

BOOL_KEYS = ['is_fullscreen', 'is_playing', 'is_vocal_on']
INT_KEYS = ['volume', 'version']

class RoomManager:
    def __init__(self, redis: Redis):
        self.redis = redis

    def _get_key(self, room_id: str, suffix: str) -> str:
        return f"room:{room_id}:{suffix}"

    def get_room(self, room_id: str) -> dict:
        """
        Atomically fetches both state and playlist.
        """
        lua = """
        local state_key = KEYS[1]
        local queue_key = KEYS[2]
        local song_key  = KEYS[3]

        -- 1. Get all metadata (state)
        local state_raw = redis.call('HGETALL', state_key)
        
        -- 2. Get all song IDs from the queue
        local song_ids = redis.call('ZRANGE', queue_key, 0, -1)
        
        -- 3. Get all song metadata for those IDs
        local songs_raw = {}
        if #song_ids > 0 then
            songs_raw = redis.call('HMGET', song_key, unpack(song_ids))
        end

        return {state_raw, song_ids, songs_raw}
        """
        keys = [
            self._get_key(room_id, "state"),
            self._get_key(room_id, "queue"),
            self._get_key(room_id, "song")
        ]
        
        raw_state, song_ids, raw_songs = self.redis.eval(lua, 3, *keys) # type: ignore
        
        # --- Post-processing logic in Python ---
        
        # Convert Lua list [key1, val1, key2, val2] to Python dict
        state_dict = {}
        for i in range(0, len(raw_state), 2):
            k = raw_state[i]
            v = raw_state[i+1]
            state_dict[k] = v
            
        # Apply defaults and type casting (using your existing logic)
        states = {**DEFAULT_ROOM_STATE, **state_dict}
        for key in BOOL_KEYS:
            if key in states:
                states[key] = str(states[key]) in ("1", "True", "true")
        for int_key in INT_KEYS:
            if int_key in states:
                states[int_key] = int(states[int_key])

        # Parse songs
        playlist = [
            {
                'id': song_id,
                'item': json.loads(s) if s else None 
            }
            for song_id, s in zip(song_ids, raw_songs)
        ]
        
        room = {**states, "room_name": room_id, "playlist": playlist}
        
        return {
            "version": int(states.get('version', 0)),
            "target": "sync",
            "item": room
        }
        
    def add_song_to_queue(self, room_id: str, item: QueueItem) -> dict:
        serialized = json.dumps(item.serialize())

        pipe = self.redis.pipeline()
        pipe.multi()
        pipe.hset(self._get_key(room_id, "song"), item.item_id, serialized)
        pipe.zadd(self._get_key(room_id, "queue"), {item.item_id: time.time()})
        pipe.hincrby(self._get_key(room_id, "state"), "version", 1)
        results = pipe.execute()
        
        return {
            "version": int(results[-1]),
            "target": "playlist",
            "action": "added",
            "item": json.loads(serialized)
        }

    def remove_song(self, room_id: str, item_id: str) -> dict:
        """
        Remove a song from the playlist.
        """
        pipe = self.redis.pipeline()
        pipe.multi()
        pipe.zrem(self._get_key(room_id, "queue"), item_id)
        pipe.hdel(self._get_key(room_id, "song"), item_id)
        pipe.hincrby(self._get_key(room_id, "state"), "version", 1)
        results = pipe.execute()
        return {
            "version": int(results[-1]),
            "target": "playlist",
            "action": "removed",
            "item_id": item_id
        }

    def move_item_to_top(self, room_id: str, item_id: str) -> dict:
        """
        Move an item to the top of the playlist.
        """
        lua = """
        local q_key, state_key = KEYS[1], KEYS[2]
        local first_item = redis.call('ZRANGE', q_key, 0, 0, 'WITHSCORES')
        local new_score
        if #first_item > 0 then
            new_score = tonumber(first_item[2]) - 1
        else
            -- Queue was empty, use provided timestamp
            new_score = tonumber(ARGV[2])
        end
        redis.call('ZADD', q_key, new_score, ARGV[1])
        local new_v = redis.call('HINCRBY', state_key, 'version', 1)
        return new_v
        """
        keys = [
            self._get_key(room_id, "queue"),
            self._get_key(room_id, "state")
        ]
        res = self.redis.eval(lua, 2, *keys, item_id, time.time())
        return {
            "version": int(res), # type: ignore
            "target": "playlist",
            "action": "moved_to_top", 
            "item_id": item_id
        }

    def move_to_item(self, room_id: str, item_id: str) -> dict:
        """Removes all items before item_id and returns the removed set."""
        lua = """
        local q_key, song_key, state_key = KEYS[1], KEYS[2], KEYS[3]
        local rank = redis.call('ZRANK', q_key, ARGV[1])
        if rank and tonumber(rank) > 0 then
            local to_remove = redis.call('ZRANGE', q_key, 0, rank - 1)
            redis.call('ZREMRANGEBYRANK', q_key, 0, rank - 1)
            if #to_remove > 0 then
                redis.call('HDEL', song_key, unpack(to_remove))
            end
            return redis.call('HINCRBY', state_key, 'version', 1)
        end
        return redis.call('HGET', state_key, 'version')
        """
        keys = [
            self._get_key(room_id, "queue"), 
            self._get_key(room_id, "song"), 
            self._get_key(room_id, "state")
        ]
        res = self.redis.eval(lua, 3, *keys, item_id)
        return {
            "version": int(res), #type: ignore
            "target": "playlist",
            "action": "cleared_to",
            "item_id": item_id
        }

    def set_metadata(self, room_id: str, vals: dict):
        """Validates input, updates Redis, and returns a versioned diff."""
        validated = {}
        diff = {}
        for key, value in vals.items():
            if key not in DEFAULT_ROOM_STATE or key == 'version':
                continue
            
            if key in BOOL_KEYS:
                if not isinstance(value, bool): raise ValueError(f"{key} must be bool")
                validated[key] = 1 if value else 0
                diff[key] = value
            elif key == 'volume':
                vol = int(value)
                if not (0 <= vol <= 100): raise ValueError("Volume must be 0-100")
                validated[key] = vol
                diff[key] = vol
            else:
                validated[key] = value
                diff[key] = value

        if not validated:
            current_v = int(self.redis.hget(self._get_key(room_id, "state"), "version") or 0) # type: ignore
            return {
                "version": current_v,
                "target": "metadata",
                "changes": {}
            }

        pipe = self.redis.pipeline()
        pipe.multi()
        pipe.hset(self._get_key(room_id, "state"), mapping=validated)
        pipe.hincrby(self._get_key(room_id, "state"), "version", 1)
        results = pipe.execute()

        return {
            "version": results[-1], 
            "target": "metadata",
            "changes": diff
        }
