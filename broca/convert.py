from urllib.parse import urlparse
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
        "rpc-version": 15,
        "rpc-version-minimum": 14,
        "script-torrent-done-filename": "",
        "script-torrent-done-enabled": False,
        "seedRatioLimit": 0,
        "seedRatioLimited": False,
        "seed-queue-size": 0,
        "seed-queue-enabled": False,
        "speed-limit-down": int(server["throttle_down"] or 0),
        "speed-limit-down-enabled": server["throttle_down"] != None,
        "speed-limit-up": int(server["throttle_up"] or 0),
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
        "version": f"2.93 (Synapse {server['id']})"
    }

def to_timestamp(synapse):
    return int(iso8601.parse_date(synapse).timestamp())

next_id = 1
transmission_ids = dict()
synapse_ids = dict()
def get_transmission_id(infohash):
    global next_id
    id = transmission_ids.get(infohash)
    if not id:
        id = transmission_ids[infohash] = next_id
        synapse_ids[id] = infohash
        next_id += 1
    return id

def get_synapse_id(id):
    return synapse_ids.get(id)

def to_file(f):
    return {
        "bytesCompleted": int(f["size"] * f["progress"]),
        "length": f["size"],
        "name": f["path"],
    }

def to_priority(p):
    return { 1: -1, 2: -1, 3: 0, 4: 1, 5: 1 }[p]

def from_priority(p):
    return { -1: 1, 0: 3, 1: 5 }[p]

def to_filestat(f):
    return {
        "bytesCompleted": int(f["size"] * f["progress"]),
        "wanted": True,
        "priority": to_priority(f["priority"]),
    }

def to_peer(p):
    return {
        "address": p["ip"],
        "clientName": p["client_id"],
        "clientIsChoked": False,
        "clientIsInterested": False,
        "flagStr": "", # TODO: wtf is this
        "isDownloadingFrom": p["rate_down"] != 0,
        "isEncrypted": False,
        "isIncoming": False,
        "isUploadingTo": p["rate_up"] != 0,
        "isUTP": False,
        "peerIsChoked": False,
        "peerIsInterested": False,
        "port": 12345,
        "progress": p["availability"],
        "rateToClient": p["rate_down"],
        "rateToPeer": p["rate_up"]
    }

def to_tracker(t):
    return {
        "announce": t["url"],
        "id": get_transmission_id(t["id"]),
        "scrape": "",
        "tier": 1,
    }

def to_trackerstat(t):
    announce = urlparse(t["url"])
    return {
        "announce": t["url"],
        "announceState": 0,
        "downloadCount": 0,
        "hasAnnounced": True,
        "hasScraped": True,
        "host": announce.netloc,
        "id": get_transmission_id(t["id"]),
        "isBackup": False,
        "lastAnnouncePeerCount": 0,
        "lastAnnounceResult": "",
        "lastAnnounceStartTime": to_timestamp(t["last_report"]),
        "lastAnnounceSucceeded": t["error"] is None,
        "lastAnnounceTime": to_timestamp(t["last_report"]),
        "lastAnnounceTimedOut": t["error"] is None,
        "lastScrapeResult": "",
        "lastScrapeStartTime": 0,
        "lastScrapeSucceeded": True,
        "lastScrapeTime": 0,
        "lastScrapeTimedOut": False,
        "leecherCount": 0, # TODO Luminarys
        "nextAnnounceTime": 0,
        "nextScrapeTime": 0,
        "scrape": "",
        "scrapeState": 0,
        "seederCount": 0, # TODO Luminarys
        "tier": 1,
    }

def to_torrent(torrent, fields=None, files=[], peers=[], trackers=[]):
    size = torrent.get("size") or 0
    throttle_down = torrent.get("throttle_down")
    throttle_up = torrent.get("throttle_up")
    transferred_down = torrent.get("transferred_down") or 0
    transferred_up = torrent.get("transferred_up") or 0
    progress = torrent.get("progress") or 0
    # We want these consistently sorted
    files = sorted(files, key=lambda f: f.get("path"))
    peers = sorted(peers, key=lambda p: p.get("id"))
    trackers = sorted(trackers, key=lambda t: t.get("url"))
    t = {
        "activityDate": to_timestamp(torrent["modified"]),
        "addedDate": to_timestamp(torrent["created"]),
        "announceUrl": trackers[0]["url"] if trackers else "",
        "bandwidthPriority": to_priority(torrent["priority"]),
        "comment": "broca TODO: fill out comment", # TODO Luminarys
        "corruptEver": 0,
        "creator": "TODO", # TODO Luminarys
        "dateCreated": to_timestamp(torrent["created"]),
        "desiredAvailable": 0,
        "doneDate": to_timestamp(torrent["created"]),
        "downloadDir": torrent["path"],
        "downloadedEver": transferred_down,
        "downloadLimit": throttle_down if throttle_down not in [None, -1] else 0,
        "downloadLimited": throttle_down not in [None, -1],
        "error": 0,
        "errorString": torrent["error"] or "",
        "eta": int((size * (1 - progress)) * torrent["rate_up"]),
        "etaIdle": int((size * (1 - progress)) * torrent["rate_up"]),
        "files": [to_file(f) for f in files],
        "fileStats": [to_filestat(f) for f in files],
        "hashString": torrent["id"],
        "haveUnchecked": 0,
        "haveValid": int(size * progress),
        "honorsSessionLimits": throttle_up is not None and throttle_down is not None,
        "id": get_transmission_id(torrent["id"]),
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
        "peers": [to_peer(p) for p in peers],
        "peersConnected": len(peers),
        "peersFrom": { # TODO Luminarys
            "fromCache": 0,
            "fromDht": 0,
            "fromIncoming": 0,
            "fromLpd": 0,
            "fromLtep": 0,
            "fromPex": 0,
            "fromTracker": 0,
        },
        "peersGettingFromUs": sum(1 for p in peers if p["rate_up"] != 0),
        "peersSendingToUs": sum(1 for p in peers if p["rate_down"] != 0),
        "percentDone": progress,
        "pieces": "",
        "pieceCount": torrent["pieces"] or 0,
        "pieceSize": torrent["piece_size"] or 0,
        "priorities": [to_priority(f["priority"]) for f in files],
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
            "idle": 0,
            "seeding": 6,
            "hashing": 2,
            "magnet": 4,
            "error": 0,
        }[torrent["status"]],
        "trackers": [to_tracker(t) for t in trackers],
        "trackerStats": [to_trackerstat(t) for t in trackers],
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
    if fields is None:
        return t
    _t = {}
    for key in fields:
        if key in t:
            _t[key] = t[key]
        else:
            print(f"Warning: client requested unknown key {key}")
    return _t

def from_torrent(torrent):
    sytorrent = dict()
    if "bandwidthPriority" in torrent:
        sytorrent["priority"] = from_priority(torrent.get("bandwidthPriority"))
    if not torrent.get("honorSessionLimits"):
        dl_limit = torrent.get("downloadLimit") or -1
        sytorrent["throttle_down"] = dl_limit
        ul_limit = torrent.get("uploadLimit") or -1
        sytorrent["throttle_up"] = ul_limit
    else:
        sytorrent["throttle_up"] = None
        sytorrent["throttle_down"] = None
    # TODO: File priority
    return sytorrent
