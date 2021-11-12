from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import Crypto.Random
import binascii


class Wallet:
    """Creates, loads and holds private and public keys. Manages transaction signing and verification."""
    
    nature_public_key = "30819f300d06092a864886f70d010101050003818d0030818902818100ca06f2590861776f91faa62bb43a78b45824caffdeba6f0d1c398eb8e312c466da47eba348b372d59eba0e772d15727d91abf6102edbf3436971e33b6c0d9a2443ad7611ac4900f9be9d68577d84d73df3ce23360abcc7a0d90549edabb9f38e6af4da4b7d3d802bf451efea8e9533d9579d978d836ac658b9c9616ce3db1c5f0203010001"
    nature_private_key = "3082025d02010002818100ca06f2590861776f91faa62bb43a78b45824caffdeba6f0d1c398eb8e312c466da47eba348b372d59eba0e772d15727d91abf6102edbf3436971e33b6c0d9a2443ad7611ac4900f9be9d68577d84d73df3ce23360abcc7a0d90549edabb9f38e6af4da4b7d3d802bf451efea8e9533d9579d978d836ac658b9c9616ce3db1c5f02030100010281804453a7214f814f58afa17b13eae79fad36e672b5a9099ac76f55541cd9c79e1f3f11f5f30a828e830b24d8019c80d570fc94912b15fe13bf27e979b5be2cb78593f5a59612f168ce8c3a741caade5f8557ea9d8e6d89b357b3884f91b1faec0cfe2793d123b60de5847df6f4aa7c3e3b6597dd6cd31bbaf8d8adfa7c9b958259024100d14c7aecbe715dce0ea1b2065bd9e477962c213a3f068de14b22b3deb3646229d73049b4380d9ce81038e7233a15972062b32a3dded661ce7913c91568fbc7bb024100f71b194ad446f4e89e20991e26b3f6d5046f469c941f164931a6136e4b96d5cd8fde75abf6179a6a14dde4fa8c4ed15bdb33f6c79a982248b93ba0be3fadb9ad0241008b0f0c71354b2f2f140b9cb39add576d990a32fd77188cb5ce6cfd230effb834e27383d4c8954ad5e8c955d0d2ebbb605a137e126376febee7351d1a2b8975b70240752cd7788162c85dca260115a81aac906492f3b3ea1537b72ba0ea13e22a3b6647b3a0af137a2bd1e3e538e08a4a11c2f216190e9bc34a769bc7a7b8af6f8cdd024100a9115b2fd0667c96a541cd47b3bee36880deb7a0351ec7041420a58aba85497f01f3e197da5b3d52dd3243f6163bbb3e6262098a61d4911fa725dc550211d9ea"
    
    def __init__(self, node_id):
        self.private_key = None
        self.public_key = None
        self.node_id = node_id

    def create_keys(self):
        """Create a new pair of private and public keys."""
        private_key, public_key = self.generate_keys()
        self.private_key = private_key
        self.public_key = public_key

    def save_keys(self):
        """Saves the keys to a file (wallet.txt)."""
        if self.public_key != None and self.private_key != None:
            try:
                with open(f"wallet-{self.node_id}.txt", mode="w") as f:
                    f.write(self.public_key)
                    f.write("\n")
                    f.write(self.private_key)
                return True

            except (IOError, IndexError):
                print("Saving wallet failed...")
                return False

    def load_keys(self):
        """Loads the keys from the wallet.txt file into memory."""
        try:
            with open(f"wallet-{self.node_id}.txt", mode="r") as f:
                keys = f.readlines()
                public_key = keys[0][:-1]
                private_key = keys[1]
                self.public_key = public_key
                self.private_key = private_key
            return True
        except (IOError, IndexError):
            print("Loading wallet failed...")
            return False

    def generate_keys(self):
        """Generate a new pair of private and public key."""
        private_key = RSA.generate(1024, Crypto.Random.new().read)

        public_key = private_key.publickey()
        return (
            binascii.hexlify(private_key.exportKey(format="DER")).decode("ascii"),
            binascii.hexlify(public_key.exportKey(format="DER")).decode("ascii"),
        )

    def sign_transaction(self, sender, recipient, amount, product_name, price):
        """Sign a transaction and return the signature.

        Arguments:
            :sender: The sender of the transaction.
            :recipient: The recipient of the transaction.
            :amount: The amount of the transaction.
        """
        if sender == self.nature_public_key:
            signer = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.nature_private_key)))
        else:    
            signer = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.private_key)))
        
        h = SHA256.new((str(sender) + str(recipient) + str(amount) + str(product_name) + str(price)).encode("utf8"))
        signature = signer.sign(h)
        return binascii.hexlify(signature).decode("ascii")

    @staticmethod
    def verify_transaction(transaction):
        """Verify the signature of a transaction.

        Arguments:
            :transaction: The transaction that should be verified.
        """
        public_key = RSA.importKey(binascii.unhexlify(transaction.sender))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA256.new((str(transaction.sender) + str(transaction.recipient) + str(transaction.amount) + str(transaction.product_name) + str(transaction.price)).encode("utf8"))
        return verifier.verify(h, binascii.unhexlify(transaction.signature))
