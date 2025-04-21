import json
import base64
from immudb import ImmudbClient

class ImmuDBReader:
    """Helper class to read transactions from ImmuDB"""
    
    def __init__(self, url, db_name):
        """
        Initialize the ImmuDBReader with connection parameters
        
        Args:
            url (str): URL of the ImmuDB server (e.g., "localhost:3322")
            db_name (str): Name of the database to connect to
        """
        self.url = url
        self.db_name = db_name
        self.client = None
    
    def connect(self):
        """Establish connection to the ImmuDB server"""
        try:
            # Parse URL to extract host and port
            if "://" in self.url:
                self.url = self.url.split("://")[1]
            
            if ":" in self.url:
                host, port = self.url.split(":")
                port = int(port)
            else:
                host = self.url
                port = 3322  # Default ImmuDB port
            
            # Connect to ImmuDB
            self.client = ImmudbClient(f"{host}:{port}")
            self.client.login(username="immudb", password="immudb")
            self.client.useDatabase(self.db_name)
            return self
        except Exception as e:
            print(f"Error connecting to ImmuDB: {e}")
            raise
    def get_all_transactions(self):
        """Retrieve all key-value pairs from the database"""
        if not self.client:
            self.connect()

        result = {}
        try:
            entries = self.client.scan(key=b'', prefix=b'', limit=0, desc=False)
            for entry in entries:
                # normalize to (key_bytes, value_bytes)
                if isinstance(entry, tuple) and len(entry) == 2:
                    key_bytes, value_bytes = entry
                elif hasattr(entry, 'key') and hasattr(entry, 'value'):
                    key_bytes, value_bytes = entry.key, entry.value
                elif isinstance(entry, bytes):
                    key_bytes = entry
                    resp = self.client.get(key_bytes)
                    # extract payload
                    if hasattr(resp, 'value'):
                        value_bytes = resp.value
                    elif hasattr(resp, 'payload'):
                        value_bytes = resp.payload
                    else:
                        value_bytes = b''
                else:
                    continue

                key_str = key_bytes.decode('utf-8', errors='replace')
                try:
                    value_str = value_bytes.decode('utf-8', errors='replace')
                except:
                    # fallback to b64
                    value_str = base64.b64encode(value_bytes).decode('utf-8')
                result[key_str] = value_str

        except Exception as e:
            print(f"Error scanning db: {e}")

        return result

    def get_by_prefix(self, prefix):
        """Retrieve key-value pairs with keys starting with the given prefix"""
        if not self.client:
            self.connect()

        result = {}
        pfx = prefix.encode('utf-8')
        try:
            entries = self.client.scan(key=b'', prefix=pfx, limit=0, desc=False)
            for entry in entries:
                # same normalization as above
                if isinstance(entry, tuple) and len(entry) == 2:
                    key_bytes, value_bytes = entry
                elif hasattr(entry, 'key') and hasattr(entry, 'value'):
                    key_bytes, value_bytes = entry.key, entry.value
                elif isinstance(entry, bytes):
                    key_bytes = entry
                    resp = self.client.get(key_bytes)
                    value_bytes = getattr(resp, 'value', getattr(resp, 'payload', b''))
                else:
                    continue

                key_str = key_bytes.decode('utf-8', errors='replace')
                if not key_str.startswith(prefix):
                    continue

                try:
                    value_str = value_bytes.decode('utf-8', errors='replace')
                except:
                    value_str = base64.b64encode(value_bytes).decode('utf-8')
                result[key_str] = value_str

        except Exception as e:
            print(f"Error scanning prefix '{prefix}': {e}")

        return result

    def get_by_suffix(self, suffix):
        """Retrieve key-value pairs with keys ending with the given suffix"""
        if not self.client:
            self.connect()

        result = {}
        sfx = suffix.encode('utf-8')
        try:
            entries = self.client.scan(key=b'', prefix=b'', limit=0, desc=False)
            for entry in entries:
                if isinstance(entry, tuple) and len(entry) == 2:
                    key_bytes, value_bytes = entry
                elif hasattr(entry, 'key') and hasattr(entry, 'value'):
                    key_bytes, value_bytes = entry.key, entry.value
                elif isinstance(entry, bytes):
                    key_bytes = entry
                    resp = self.client.get(key_bytes)
                    value_bytes = getattr(resp, 'value', getattr(resp, 'payload', b''))
                else:
                    continue

                if not key_bytes.endswith(sfx):
                    continue

                key_str = key_bytes.decode('utf-8', errors='replace')
                try:
                    value_str = value_bytes.decode('utf-8', errors='replace')
                except:
                    value_str = base64.b64encode(value_bytes).decode('utf-8')
                result[key_str] = value_str

        except Exception as e:
            print(f"Error scanning suffix '{suffix}': {e}")

        return result
    
    def get_merkle_root(self):
        """Get the Merkle root of the database"""
        if not self.client:
            self.connect()
        
        try:
            state = self.client.currentState()
            return {
                "txId": state.txId,
                "merkleRoot": state.txHash.hex()
            }
        except Exception as e:
            print(f"Error getting Merkle root: {e}")
            return {"txId": None, "merkleRoot": None}

# Helper functions for easy usage

def read_transactions(url, db_name, prefix=None, suffix=None):
    """
    Read transactions from ImmuDB based on optional filters
    
    Args:
        url (str): URL of the ImmuDB server
        db_name (str): Name of the database
        prefix (str, optional): Filter keys starting with this prefix
        suffix (str, optional): Filter keys ending with this suffix
        
    Returns:
        dict: Dictionary of key-value pairs matching the criteria
    """
    reader = ImmuDBReader(url, db_name).connect()
    
    if prefix:
        return reader.get_by_prefix(prefix)
    elif suffix:
        return reader.get_by_suffix(suffix)
    else:
        return reader.get_all_transactions()

def get_merkle_root(url, db_name):
    """
    Get the Merkle root of the database
    
    Args:
        url (str): URL of the ImmuDB server
        db_name (str): Name of the database
        
    Returns:
        dict: Dictionary with txId and merkleRoot
    """
    reader = ImmuDBReader(url, db_name).connect()
    return reader.get_merkle_root()

def get_transactions_as_json(url, db_name, prefix=None, suffix=None):
    """
    Get transactions and return as JSON string
    
    Args:
        url (str): URL of the ImmuDB server
        db_name (str): Name of the database
        prefix (str, optional): Filter keys starting with this prefix
        suffix (str, optional): Filter keys ending with this suffix
        
    Returns:
        str: JSON string representation of matching key-value pairs
    """
    data = read_transactions(url, db_name, prefix, suffix)
    return json.dumps(data)

def get_merkle_root_as_json(url, db_name):
    """
    Get the Merkle root as JSON string
    
    Args:
        url (str): URL of the ImmuDB server
        db_name (str): Name of the database
        
    Returns:
        str: JSON string with txId and merkleRoot
    """
    data = get_merkle_root(url, db_name)
    return json.dumps(data)


if __name__ == "__main__":
    # Connect and get all transactions
    URL = "localhost:3322"
    DB_NAME = "defaultdb"
    reader = ImmuDBReader(URL, DB_NAME).connect()
    all_txs = reader.get_all_transactions()
    print(all_txs)

    all_txs = read_transactions(URL, DB_NAME)
    print(all_txs)

    # Search by prefix
    user_txs = read_transactions(URL, DB_NAME, prefix="block:")
    print(user_txs)

    # Search by suffix
    log_txs = read_transactions(URL, DB_NAME, suffix="9")
    print(log_txs)

    # Get Merkle root for verification
    root = get_merkle_root(URL, DB_NAME)
    print(f"Transaction ID: {root['txId']}")
    print(f"Merkle Root: {root['merkleRoot']}")