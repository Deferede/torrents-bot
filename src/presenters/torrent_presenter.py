import json
from typing import Dict, Any
from src.entities.torrent import Torrent

class TorrentPresenter:
    @staticmethod
    def present(torrent: Torrent) -> Dict[str, Any]:
        """Present a Torrent entity as a dictionary (JSON-like)"""
        return {
            "name": torrent.name,
            "status": torrent.status,
            "created_at": torrent.createdAt,
            "current_speed": torrent.current_speed,
            "eta": torrent.eta
        }
    
    @staticmethod
    def present_list(torrents: list[Torrent]) -> list[Dict[str, Any]]:
        """Present a list of Torrent entities as a list of dictionaries"""
        return [TorrentPresenter.present(torrent) for torrent in torrents]
    
    @staticmethod
    def to_json(torrent: Torrent) -> str:
        """Convert a Torrent entity to JSON string"""
        return json.dumps(TorrentPresenter.present(torrent), indent=2)
    
    @staticmethod
    def to_json_list(torrents: list[Torrent]) -> str:
        """Convert a list of Torrent entities to JSON string"""
        return json.dumps(TorrentPresenter.present_list(torrents), indent=2)