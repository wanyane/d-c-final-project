import requests
from wallet import Wallet

class CtrlNode():
    public_key_port_map = {Wallet.nature_public_key: "nature"}
    port_public_key_map = {"nature": Wallet.nature_public_key}
    def __init__(self, port):
        self.port = port
        self.url = f"http://localhost:{self.port}"
        self.public_key = None
        self.private_key = None

    def load_wallet(self):
        respond = requests.get(f"{self.url}/wallet")
        
        public_key = respond.json()["public_key"]
        self.public_key_port_map[public_key] = self.port
        self.port_public_key_map[str(self.port)] = public_key


    def add_peer(self, peer_port):
        respond = requests.post(f"{self.url}/node", json={
                            "node": f"localhost:{peer_port}"
                        })
    

    def send_transaction(self, is_nature, recipient_port, amount, product_name, price):
        respond = requests.post(f"{self.url}/transaction", json={
                            "is_nature": is_nature ,
                            "recipient": self.port_public_key_map[str(recipient_port)],
                            "amount": amount,
                            "product_name": product_name,
                            "price": price
                        })
        print(respond.json()["message"])

    def mine(self):
        respond = requests.post(f"{self.url}/mine")
        print(respond.json())

    def view_open_transactions(self):
        respond = requests.get(f"{self.url}/transactions")
        transactions = respond.json()
        print(f"open transactions of ({self.port})")
        for i, t in enumerate(transactions):
            print(f"#{i}: ({self.public_key_port_map[t['sender']]}) sends {t['amount']} of {t['product_name']} to ({self.public_key_port_map[t['recipient']]})")

    def view_chain(self):
        respond = requests.get(f"{self.url}/chain")
        blocks = respond.json()
        blocks = blocks[1:] # get rid of the first block
        print(f"chain of ({self.port})")
        for b in blocks:
            print(f"block_idx: {b['index']}")
            print(f"block_proof: {b['proof']}")
            print("transactions:")
            for t in b["transactions"]:
                print(f"\t({self.public_key_port_map[t['sender']]}) sends {t['amount']} of {t['product_name']} to ({self.public_key_port_map[t['recipient']]})")




node5000 = CtrlNode(5000)
node5001 = CtrlNode(5001)

if __name__ == "__main__":
    node5000.load_wallet()
    node5001.load_wallet()
    
    node5000.add_peer(5001)
    node5001.add_peer(5000)

    # view chain
    # node5000.view_chain()
    # node5000.send_transaction(False, 5001, 10, "apple", 0)
    node5000.view_open_transactions()
    node5001.view_open_transactions()
    node5000.mine()
    node5000.view_open_transactions()
    node5001.view_open_transactions()
