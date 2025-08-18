import requests
from typing import Dict, Any, Optional, List

# Import the Torrent entity
from src.entities.torrent import Torrent


class QBittorrentService:
    """A service class for interacting with qBittorrent's Web API."""
    
    def __init__(self, host: str = "localhost", port: int = 8080, username: str = "admin", password: str = "admin"):
        """
        Initialize the QBittorrentService.
        
        Args:
            host (str): qBittorrent Web API host
            port (int): qBittorrent Web API port
            username (str): qBittorrent username
            password (str): qBittorrent password
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()
        
        # Set the Referer header as required by qBittorrent API
        self.session.headers.update({'Referer': f"{self.base_url}"})

        if not self.login():
            print("Failed to login to qBittorrent")
            raise Exception("Authentication failed")
        
    def login(self) -> bool:
        """
        Login to qBittorrent Web API.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/v2/auth/login",
                data={
                    "username": self.username,
                    "password": self.password
                }
            )
            
            # Check if login was successful (status code 200)
            if response.status_code == 200:
                # The session automatically handles cookies now
                return True
            else:
                print(f"Login failed with status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def get_torrents_info(self) -> Dict[str, Any]:
        """
        Get information about all torrents.
        
        Returns:
            dict: Torrent information
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v2/torrents/info"
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get torrents info, status code: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"Error getting torrents info: {e}")
            return {}
    
    def get_torrents(self) -> List['Torrent']:
        """
        Get all torrents as Torrent entities.
        
        Returns:
            list: List of Torrent entities
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v2/torrents/info"
            )
            
            if response.status_code == 200:
                torrents_data = response.json()
                return [Torrent(
                    name=t['name'],
                    status=t['state'],
                    createdAt=t['added_on'],
                    current_speed=t.get('dlspeed', 0) / 1024,  # Convert to KB/s, with default value
                    eta=t.get('eta', -1),
                    hash_value=t.get('hash', '')
                ) for t in torrents_data]
            else:
                print(f"Failed to get torrents info, status code: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error getting torrents: {e}")
            return []

    def add_torrent(self, torrent_file_path: str) -> bool:
        """
        Add a torrent file to qBittorrent.
        
        Args:
            torrent_file_path (str): Path to the .torrent file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(torrent_file_path, 'rb') as f:
                files = {'file': f}
                response = self.session.post(
                    f"{self.base_url}/api/v2/torrents/add",
                    files=files
                )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error adding torrent: {e}")
            return False

    def add_torrent_from_magnet(self, magnet_link: str, save_path: str = "/DATA") -> bool:
        """
        Add a torrent from magnet link to qBittorrent.
        
        Args:
            magnet_link (str): Magnet link URL
            save_path (str): Path where to save the torrent files
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data = {
                'urls': magnet_link,
                'savepath': save_path
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v2/torrents/add",
                data=data
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error adding magnet torrent: {e}")
            return False

    def get_torrents_status(self) -> Dict[str, Any]:
        """
        Get the status of torrents.
        
        Returns:
            dict: Torrent status information
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v2/torrents/status"
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get torrents status, status code: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"Error getting torrents status: {e}")
            return {}

    def pause_torrent(self, hash_value: str) -> bool:
        """
        Pause a torrent.
        
        Args:
            hash_value (str): Torrent hash value
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/v2/torrents/pause",
                data={'hashes': hash_value}
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error pausing torrent: {e}")
            return False

    def resume_torrent(self, hash_value: str) -> bool:
        """
        Resume a torrent.
        
        Args:
            hash_value (str): Torrent hash value
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/v2/torrents/resume",
                data={'hashes': hash_value}
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error resuming torrent: {e}")
            return False

    def delete_torrent(self, hash_value: str, delete_files: bool = True) -> bool:
        """
        Delete a torrent and optionally its files.
        
        Args:
            hash_value (str): Torrent hash value
            delete_files (bool): Whether to delete downloaded files
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data = {
                'hashes': hash_value,
                'deleteFiles': str(delete_files).lower()
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v2/torrents/delete",
                data=data
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error deleting torrent: {e}")
            return False