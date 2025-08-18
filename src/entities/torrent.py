class Torrent:
    def __init__(self, name: str, status: str, createdAt: int, current_speed: float, eta: int, hash_value: str = ""):
        self.name = name
        self.status = status
        self.createdAt = createdAt
        self.current_speed = current_speed
        self.eta = eta
        self.hash_value = hash_value

    def __str__(self):
        return f"Torrent(name='{self.name}', status='{self.status}', createdAt={self.createdAt}, current_speed={self.current_speed}, eta={self.eta}, hash='{self.hash_value}')"