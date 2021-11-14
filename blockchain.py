from functools import reduce
import hashlib as hl
from os import replace
import requests
import json
import pickle
from requests import exceptions

from werkzeug.datastructures import FileStorage

# Import two functions from our hash_util.py file. Omit the ".py" in the import
from utility.hash_util import hash_block
from utility.verification import Verification
from block import Block
from transaction import Transaction
from wallet import Wallet

class Blockchain:
    """The Blockchain class manages the chain of blocks as well as open transactions and the node on which it's running.
    
    Attributes:
        :chain: The list of blocks
        :open_transactions (private): The list of open transactions
        :wallet_public_key: The connected node (which runs the blockchain).
    """
    def __init__(self, wallet_public_key, node_id):
        """The constructor of the Blockchain class."""
        # Our starting block for the blockchain
        genesis_block = Block(0, '', [], 100, 0)
        # Initializing our (empty) blockchain list
        self.chain = [genesis_block]
        # Unhandled transactions
        self.__open_transactions = []
        self.wallet_public_key = wallet_public_key
        self.node_id = node_id
        self.__peer_nodes = set()
        self.resolve_conflicts = False
        
        self.load_data()
    # This turns the chain attribute into a property with a getter (the method below) and a setter (@chain.setter)
    @property
    def chain(self):
        return self.__chain[:]

    # The setter for the chain property
    @chain.setter 
    def chain(self, val):
        self.__chain = val


    def get_open_transactions(self):
        """Returns a copy of the open transactions list."""
        return self.__open_transactions[:]

    def load_data(self):
        """Initialize blockchain + open transactions data from a file."""
        try:
            with open(f"blockchain-{self.node_id}.txt", mode='r') as f:
                # file_content = pickle.loads(f.read())
                file_content = f.readlines()
                # blockchain = file_content['chain']
                # open_transactions = file_content['ot']
                blockchain = json.loads(file_content[0][:-1])
                # We need to convert  the loaded data because Transactions should use OrderedDict
                updated_blockchain = []
                for block in blockchain:
                    converted_tx = [Transaction(tx['sender'], tx['recipient'], tx['signature'], tx['amount'], tx['product_name'], tx['price']) for tx in block['transactions']]
                    updated_block = Block(
                        block['index'], block['previous_hash'], converted_tx, block['proof'], block['timestamp'])
                    updated_blockchain.append(updated_block)
                self.chain = updated_blockchain
                open_transactions = json.loads(file_content[1][:-1])
                # We need to convert  the loaded data because Transactions should use OrderedDict
                updated_transactions = []
                for tx in open_transactions:
                    updated_transaction = Transaction(tx['sender'], tx['recipient'], tx['signature'], tx['amount'], tx['product_name'], tx['price'])
                    updated_transactions.append(updated_transaction)
                self.__open_transactions = updated_transactions
                peer_node = json.loads(file_content[2])
                self.__peer_nodes = set(peer_node)
        except (IOError, IndexError):
            pass
        finally:
            print('Cleanup!')

    def save_data(self):
        """Save blockchain + open transactions snapshot to a file."""
        try:
            with open(f"blockchain-{self.node_id}.txt", mode='w') as f:
                saveable_chain = [block.__dict__ for block in [Block(block_el.index, block_el.previous_hash, [
                    tx.__dict__ for tx in block_el.transactions], block_el.proof, block_el.timestamp) for block_el in self.__chain]]
                f.write(json.dumps(saveable_chain))
                f.write('\n')
                saveable_tx = [tx.__dict__ for tx in self.__open_transactions]
                f.write(json.dumps(saveable_tx))
                f.write("\n")
                f.write(json.dumps(list(self.__peer_nodes)))
        except IOError:
            print('Saving failed!')

    def proof_of_work(self):
        """Generate a proof of work for the open transactions, the hash of the previous block and a random number (which is guessed until it fits)."""
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0
        # Try different PoW numbers and return the first valid one
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def get_product_stock(self, sender, product_name):
        """Calculate and return the balance for a participant.
        """
        # [Winston]
        if sender == None:
            return None
        else:
            participant = sender # might not be owner of this node / might be send by other node

        if participant == self.wallet_public_key:
            print(f"participant is local wallet owner")
        else:
            print(f"participant is other node")

    
        # Fetch a list of all sent coin amounts for the given person (empty lists are returned if the person was NOT the sender)
        # This fetches sent amounts of transactions that were already included in blocks of the blockchain
        tx_sender = [[tx.amount for tx in block.transactions if tx.sender == participant and tx.product_name == product_name] for block in self.__chain]
        # Fetch a list of all sent coin amounts for the given person (empty lists are returned if the person was NOT the sender)
        # This fetches sent amounts of open transactions (to avoid double spending)
        open_tx_sender = [tx.amount
                        for tx in self.__open_transactions if tx.sender == participant and tx.product_name == product_name]
        tx_sender.append(open_tx_sender)
        # print(tx_sender)
        amount_sent = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
                            if len(tx_amt) > 0 else tx_sum + 0, tx_sender, 0)
        # This fetches received coin amounts of transactions that were already included in blocks of the blockchain
        # We ignore open transactions here because you shouldn't be able to spend coins before the transaction was confirmed + included in a block
        tx_recipient = [[tx.amount for tx in block.transactions if tx.recipient == participant and tx.product_name == product_name] for block in self.__chain]
        amount_received = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
                                if len(tx_amt) > 0 else tx_sum + 0, tx_recipient, 0)
        # Return the total balance
        return amount_received - amount_sent

    def get_last_blockchain_value(self):
        """ Returns the last value of the current blockchain. """
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]

    # This function accepts two arguments.
    # One required one (transaction_amount) and one optional one (last_transaction)
    # The optional one is optional because it has a default value => [1]

    # [Winston]def add_transaction(self, recipient, sender, signature, amount=1.0, product_name, price):
    def add_transaction(self, recipient, sender, signature, amount, product_name, price, is_receiving=False):
        """ Append a new value as well as the last blockchain value to the blockchain.

        Arguments:
            :sender: The sender of the coins.
            :recipient: The recipient of the coins.
            :amount: The amount of coins sent with the transaction (default = 1.0)
        """

        if self.wallet_public_key == None:
            return False
        transaction = Transaction(sender, recipient, signature, amount, product_name, price)
        if Verification.verify_transaction(transaction, self.get_product_stock):
            self.__open_transactions.append(transaction)
            self.save_data()
            # brocast to all peer nodes
            if is_receiving == False:
                for node in self.__peer_nodes:
                    url = f"http://{node}/broadcast-transaction"
                    try:
                        respond = requests.post(url, json={
                            "sender": sender,
                            "recipient": recipient,
                            "signature": signature,
                            "amount": amount,
                            "product_name": product_name,
                            "price": price
                        })
                        if respond.status_code == 400 or respond.status_code == 500:
                            print("transaction declined, need resolving")
                            return False
                    except requests.exceptions.ConnectionError:
                        continue
            return True

        print("[Error] blockchain.py -> add_transaction return false")
        return False

    def mine_block(self):
        """Create a new block and add open transactions to it."""
        # Fetch the currently last block of the blockchain
        if self.wallet_public_key == None:
            return None 
        last_block = self.__chain[-1]
        # Hash the last block (=> to be able to compare it to the stored hash value)
        hashed_block = hash_block(last_block)
        proof = self.proof_of_work()
        # Miners should be rewarded, so let's create a reward transaction
        # [Winston] 
        # reward_transaction = Transaction('MINING', self.wallet_public_key, '', MINING_REWARD, "apple", 0)
        # Copy transaction instead of manipulating the original open_transactions list
        # This ensures that if for some reason the mining should fail, we don't have the reward transaction stored in the open transactions
        copied_transactions = self.__open_transactions[:]
        for tx in copied_transactions:
            if not Wallet.verify_transaction(tx):
                return None
        # [Winston] 
        # copied_transactions.append(reward_transaction)
        block = Block(len(self.__chain), hashed_block, copied_transactions, proof)
        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()
        # send the mined block to peer nodes
        for node in self.__peer_nodes:
            url = f"http://{node}/broadcast-block"
            converted_block = block.__dict__.copy()
            converted_block["transactions"] = [tx.__dict__ for tx in converted_block["transactions"]]
            try:
                respond = requests.post(url, json={"block": converted_block})
                if respond.status_code == 400 or respond.status_code == 500:
                    print("block declined, need resolving")
                if respond.status_code == 409: # our local blockchain is invalid
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue
        return block

    def add_block(self, block):
        transactions = [Transaction(tx["sender"], tx["recipient"], tx["signature"],tx["amount"],tx["product_name"],tx["price"]) for tx in block["transactions"]]
        proof_is_valid = Verification.valid_proof(transactions, block["previous_hash"], block["proof"])
        hash_match = hash_block(self.chain[-1]) == block["previous_hash"]
        if not proof_is_valid or not hash_match:
            return False
        
        converted_block = Block(block["index"], block["previous_hash"], transactions, block["proof"], block["timestamp"])
        self.__chain.append(converted_block)
        
        # [Winston] Remove duplicate transactions
        stored_transactions = self.__open_transactions[:]
        for tx in block["transactions"]:
            for stored_transaction in stored_transactions:
                if stored_transaction.sender == tx["sender"] and \
                   stored_transaction.recipient == tx["recipient"] and \
                   stored_transaction.amount == tx["amount"] and \
                   stored_transaction.product_name == tx["product_name"] and \
                   stored_transaction.price == tx["price"]: #same transaction (should also compare timestamp)
                    try:
                        self.__open_transactions.remove(stored_transaction)
                    except ValueError:
                        print("transaction already removed")

        self.save_data()
        return True
    
    def resolve(self):
        winner_chain = self.chain
        replace = False
        for node in self.__peer_nodes:
            url = f"http://{node}/chain"
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [Block(b["index"], b["previous_hash"], [Transaction(tx["sender"], tx["recipient"], tx["signature"], tx["amount"], tx["product_name"], tx["price"]) for tx in b["transactions"]], b["proof"], b["timestamp"]) for b in node_chain]
                node_chain_len = len(node_chain)
                local_chain_len = len(winner_chain)
                if node_chain_len > local_chain_len and Verification.verify_chain(node_chain):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue
        
        self.resolve_conflicts = False    
        self.chain = winner_chain 
        if replace == True:
            self.__open_transactions = []
        
        self.save_data()
        return replace

    
    def add_peer_node(self, node):
        self.__peer_nodes.add(node)
        self.save_data()

    def remove_peer_node(self, node):
        self.__peer_nodes.discard(node)
        self.save_data()

    def get_peer_nodes(self):
        return list(self.__peer_nodes)[:]
