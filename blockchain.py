import hashlib, json, time

class Block:
    def __init__(self, index, data, prev_hash):
        self.index = index
        self.timestamp = time.time()
        self.data = data
        self.prev_hash = prev_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        content = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "prev_hash": self.prev_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(content).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = [self.genesis()]

    def genesis(self):
        return Block(0, "Genesis Block", "0")

    def add_vote(self, vote):
        self.chain.append(
            Block(len(self.chain), vote, self.chain[-1].hash)
        )

    def count_votes(self):
        result = {}
        for block in self.chain[1:]:
            c = block.data["candidate"]
            result[c] = result.get(c, 0) + 1
        return result
