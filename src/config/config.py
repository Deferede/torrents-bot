"""
Configuration Module

This module handles application configuration, including loading from environment variables.
"""

import os
from typing import Optional, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class."""
    
    # qBittorrent settings
    QBITTORRENT_HOST: str = os.getenv('QBITTORRENT_HOST', 'localhost')
    QBITTORRENT_PORT: int = int(os.getenv('QBITTORRENT_PORT', '8080'))
    QBITTORRENT_USERNAME: str = os.getenv('QBITTORRENT_USERNAME', 'admin')
    QBITTORRENT_PASSWORD: str = os.getenv('QBITTORRENT_PASSWORD', 'admin')
    
    # Telegram settings
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    ADMIN_CHAT_ID: str = os.getenv('ADMIN_CHAT_ID', '')
    TRUSTED_USERS_IDS: str = os.getenv('TRUSTED_USERS_IDS', '')
    
    # Application settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    
    @classmethod
    def get_qbittorrent_config(cls) -> dict:
        """Get qBittorrent configuration as a dictionary."""
        return {
            'host': cls.QBITTORRENT_HOST,
            'port': cls.QBITTORRENT_PORT,
            'username': cls.QBITTORRENT_USERNAME,
            'password': cls.QBITTORRENT_PASSWORD
        }
    
    @classmethod
    def get_trusted_users(cls) -> list:
        """Get trusted users IDs as a list."""
        if not cls.TRUSTED_USERS_IDS:
            return []
        return [int(user_id.strip()) for user_id in cls.TRUSTED_USERS_IDS.split(',') if user_id.strip()]

# Create a global config instance
config = Config()

# Example usage:
if __name__ == "__main__":
    print("Configuration loaded:")
    print(f"qBittorrent Host: {config.QBITTORRENT_HOST}")
    print(f"qBittorrent Port: {config.QBITTORRENT_PORT}")
    print(f"qBittorrent Username: {config.QBITTORRENT_USERNAME}")
    print(f"Log Level: {config.LOG_LEVEL}")
    print(f"Debug Mode: {config.DEBUG}")