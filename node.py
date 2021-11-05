from uuid import uuid4

from blockchain import Blockchain
from utility.verification import Verification
from wallet import Wallet


class Node:
    """The node which runs the local blockchain instance.

    Attributes:
        :id: The id of the node.
        :blockchain: The blockchain which is run by this node.
    """

    def __init__(self):
        # self.id = str(uuid4())
        self.wallet = Wallet()
        self.wallet.create_keys()
        self.blockchain = Blockchain(self.wallet.public_key)

    def get_transaction_value(self):
        """Returns the input of the user (a new transaction amount) as a float."""
        # Get the user input, transform it from a string to a float and store it in user_input
        is_nature = input("Enter 'y' if produced by nature: ")
        
        if is_nature == "y":
            tx_sender = Wallet.nature_public_key
        else:
            tx_sender = self.wallet.public_key
        
        tx_recipient = input("Enter the recipient of the transaction: ")
        tx_amount = float(input("Your transaction amount please: "))
        # [Winston]
        tx_product_name = "apple"
        tx_price = 0
        return tx_sender, tx_recipient, tx_amount, tx_product_name, tx_price

    def get_user_choice(self):
        """Prompts the user for its choice and return it."""
        user_input = input("Your choice: ")
        return user_input

    def print_blockchain_elements(self):
        """Output all blocks of the blockchain."""
        # Output the blockchain list to the console
        # for block in self.blockchain.chain:
        #     print("Outputting Block")
        #     print(block)
        # else:
        #     print("-" * 20)
        for b in self.blockchain.chain:
            print(b)

    def listen_for_input(self):
        """Starts the node and waits for user input."""
        waiting_for_input = True

        # A while loop for the user input interface
        # It's a loop that exits once waiting_for_input becomes False or when break is called
        while waiting_for_input:
            print("Please choose")
            print("1: Add a new transaction value")
            print("2: Mine a new block")
            print("3: Output the blockchain blocks")
            print("4: Check transaction validity")
            print("5: Create wallet")
            print("6: Load wallet")
            print("7: Save keys")
            print("q: Quit")
            user_choice = self.get_user_choice()
            if user_choice == "1":
                tx_data = self.get_transaction_value()
                sender, recipient, amount, product_name, price = tx_data
                # Add the transaction amount to the blockchain
                signature = self.wallet.sign_transaction(
                    sender, recipient, amount, product_name, price
                )
                if self.blockchain.add_transaction(recipient, sender, signature, amount, product_name, price):
                    print("Added transaction!")
                else:
                    print("Transaction failed!")
                
            elif user_choice == "2":
                print("user_choice == 2 start")
                if not self.blockchain.mine_block():
                    print("Mining failed. Got no wallet?")
                print("user_choice == 2 end")
            elif user_choice == "3":
                self.print_blockchain_elements()
                print(f"open transactions:\n{self.blockchain.get_open_transactions()}")
            elif user_choice == "4":
                if Verification.verify_transactions(self.blockchain.get_open_transactions(), self.blockchain.get_product_stock):
                    print("All transactions are valid")
                else:
                    print("There are invalid transactions")
            elif user_choice == "5":
                self.wallet.create_keys()
                self.blockchain = Blockchain(self.wallet.public_key)
            elif user_choice == "6":
                self.wallet.load_keys()
                self.blockchain = Blockchain(self.wallet.public_key)
            elif user_choice == "7":
                self.wallet.save_keys()
            elif user_choice == "q":
                # This will lead to the loop to exist because it's running condition becomes False
                waiting_for_input = False
            elif user_choice == "s":
                pass
            else:
                print("Input was invalid, please pick a value from the list!")
            if not Verification.verify_chain(self.blockchain.chain):
                
                self.print_blockchain_elements()
                print("[Invalid blockchain!]")
                # Break out of the loop
                break
            # print(
            #     "Balance of *{}: {:6.2f}".format(
            #         self.wallet.public_key[:32], self.blockchain.get_product_stock(product_name="apple")
            #     )
            # )
            # print(self.blockchain.get_open_transactions())
        else:
            print("User left!")

        print("Done!")


if __name__ == "__main__":
    node = Node()
    node.listen_for_input()
