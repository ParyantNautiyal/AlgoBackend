class KiteModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def create_table():
        return """
        CREATE TABLE IF NOT EXISTS kite_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(255),
            price FLOAT,
            timestamp DATETIME
        )
        """ 