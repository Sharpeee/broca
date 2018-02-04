import iso8601

def to_session(server):
    # This is largely bullshit
    return {
        "alt-speed-down": 0,
        "alt-speed-enabled": False,
        "alt-speed-time-begin": 0,
        "alt-speed-time-enabled": False,
        "alt-speed-time-end": 0,
        "alt-speed-time-day": 0,
        "alt-speed-up": 0,
        "blocklist-url": None,
        "blocklist-enabled": False,
        "blocklist-size": 0,
        "cache-size-mb": 0,
        "config-dir": "",
        "download-dir": "",
        "download-queue-size": 0,
        "download-queue-enabled": False,
        "dht-enabled": False,
        "encryption": False,
        "idle-seeding-limit": 0,
        "idle-seeding-limit-enabled": False,
        "incomplete-dir": "",
        "incomplete-dir-enabled": False,
        "lpd-enabled": False,
        "peer-limit-global": 0,
        "peer-limit-per-torrent": 0,
        "pex-enabled": False,
        "peer-port": 0,
        "peer-port-random-on-start": False,
        "port-forwarding-enabled": False,
        "queue-stalled-enabled": False,
        "queue-stalled-minutes": 0,
        "rename-partial-files": False,
        "rpc-version": 2.80,
        "rpc-version-minimum": 2.80,
        "script-torrent-done-filename": "",
        "script-torrent-done-enabled": False,
        "seedRatioLimit": 0,
        "seedRatioLimited": False,
        "seed-queue-size": 0,
        "seed-queue-enabled": False,
        "speed-limit-down": server["throttle_down"] or 0,
        "speed-limit-down-enabled": server["throttle_down"] != None,
        "speed-limit-up": server["throttle_up"] or 0,
        "speed-limit-up-enabled": server["throttle_up"] != None,
        "start-added-torrents": False, # TODO: Make this actually work
        "trash-original-torrent-files": False,
        "units": {
            "speed-units": "MB/s",
            "speed-bytes": 1024,
            "size-units": "MB/s",
            "size-bytes": 1024,
            "memory-units": "MB/s",
            "memory-bytes": 1024,
        },
        "utp-enabled": False,
        "version": "2.93 (synapse)"
    }

def to_timestamp(synapse):
    return iso8601.parse_date(synapse).timestamp()

next_id = 1
id_map = dict()
def get_id(infohash):
    global next_id
    id = id_map.get(infohash)
    if not id:
        id = id_map[infohash] = next_id
        next_id += 1
    return id

def to_torrent(torrent, fields):
    size = torrent["size"] or 0
    throttle_down = torrent["throttle_down"]
    throttle_up = torrent["throttle_up"]
    transferred_down = torrent["transferred_down"]
    transferred_up = torrent["transferred_up"]
    progress = torrent["progress"]
    t = {
        "activityDate": 0,
        "addedDate": 0,
        "bandwidthPriority": 0,
        "comment": "TODO", # TODO Luminarys
        "corruptEver": 0,
        "creator": "TODO", # TODO Luminarys
        "dateCreated": to_timestamp(torrent["created"]),
        "desiredAvailable": 0,
        "doneDate": to_timestamp(torrent["created"]),
        "downloadDir": torrent["path"],
        "downloadedEver": transferred_down,
        "downloadLimit": throttle_down if throttle_down not in [None, -1] else 0,
        "downloadLimited": throttle_down not in [None, -1],
        "error": torrent["error"] is not None,
        "errorString": torrent["error"] or "",
        "eta": 0, # TODO
        "etaIdle": 0,
        "files": [], # TODO
        "fileStats": [], # TODO
        "hashString": torrent["id"],
        "haveUnchecked": 0,
        "haveValid": int(size * progress),
        "honorsSessionLimits": throttle_up is not None and throttle_down is not None,
        "id": get_id(torrent["id"]),
        "isFinished": progress == 1,
        "isPrivate": False, # TODO Luminarys
        "isStalled": False,
        "leftUntilDone": 0,
        "magnetLink": "", # TODO Luminarys
        "manualAnnounceTime": 0,
        "maxConnectedPeers": 0,
        "metadataPercentComplete": progress if torrent["status"] == "magnet" else 1,
        "name": torrent["name"],
        "peer-limit": 0,
        "peers": [], # TODO
        "peersConnected": 0, # TODO
        "peersFrom": { # TODO Luminarys
            "fromCache": 0,
            "fromDht": 0,
            "fromIncoming": 0,
            "fromLpd": 0,
            "fromLtep": 0,
            "fromPex": 0,
            "fromTracker": 0,
        },
        "peersGettingFromUs": 0, # TODO
        "peersSendingToUs": 0, # TODO
        "percentDone": progress,
        "pieces": "",
        "pieceCount": torrent["pieces"] or 0,
        "pieceSize": torrent["piece_size"] or 0,
        "priorities": [],
        "queuePosition": 0,
        "rateDownload": torrent["rate_down"],
        "rateUpload": torrent["rate_up"],
        "recheckProgress": 0,
        "secondsDownloading": 0,
        "secondsSeeding": 0,
        "seedIdleLimit": 0,
        "seedIdleMode": 0,
        "seedRatioLimit": 0,
        "seedRatioMode": 0,
        "sizeWhenDone": size,
        "startDate": to_timestamp(torrent["created"]),
        "status": {
            "paused": 0,
            "pending": 5,
            "leeching": 4,
            "idle": 3,
            "seeding": 6,
            "hashing": 2,
            "magnet": 4,
            "error": 0,
        }[torrent["status"]],
        "trackers": [],
        "trackerStats": [],
        "totalSize": size * progress,
        "torrentFile": "",
        "uploadedEver": transferred_up,
        "uploadLimit": throttle_up if throttle_up not in [None, -1] else 0,
        "uploadLimited": throttle_up not in [None, -1],
        "uploadRatio": transferred_up / transferred_down if transferred_down else 0,
        "wanted": [],
        "webseeds": [],
        "webseedsSendingToUs": 0,
    }
    _t = {}
    for key in fields:
        if key in t:
            _t[key] = t[key]
    return _t
