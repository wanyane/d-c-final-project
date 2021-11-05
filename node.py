import json
from flask import Flask, jsonify, request
from flask.wrappers import Response
from flask_cors import CORS
from wallet import Wallet
from blockchain import Blockchain

app = Flask(__name__)
wallet = Wallet()
blockchain = Blockchain(wallet.public_key)
CORS(app)

@app.route("/", methods=["GET"])
def get_UI():
    return "this works"

@app.route("/transaction", methods=["POST"])
def add_transaction():
    values = request.get_json()
    if not values:
        response = {
            "message": "No data found!",
        }
        return jsonify(response), 400
    else:
        required_field = ["is_nature", "recepient", "amount", "product_name", "price"]
        valid = all([field in values for field in required_field])
        if not valid:
            response = {
                "message": "required data is missing"
            }
            return jsonify(response), 400
        else:
            if values["is_nature"] == True:
                sender = wallet.nature_public_key
            else:
                sender = wallet.public_key
            
            signature = wallet.sign_transaction(sender, values["recepient"], values["amount"], values["product_name"], values["price"])
            success = blockchain.add_transaction(values["recepient"], sender, signature, values["amount"], values["product_name"], values["price"])
            if success:
                response = {
                    "message": "successfully creating a transaction",
                    "sender": sender,
                    "recepient": values["recepient"],
                    "signature": signature,
                    "amount": values["amount"],
                    "product_name": values["product_name"],
                    "price": values["price"],
                }
                return jsonify(response), 201
            else:
                response = {
                    "message": "creating a transactin failed",
                    "wallet_set_up": wallet.public_key != None
                }

                return jsonify(response), 500


@app.route("/wallet", methods=["POST"]) #create new key pair
def create_wallet():
    wallet.create_keys()
    if wallet.save_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key)
        response = {
            "public_key": wallet.public_key,
            "private_key": wallet.private_key,
            "product_stock": blockchain.get_product_stock("apple")
        }
        
        return jsonify(response), 201
    else:
        response = {
            "message": "saving keys fail",
        }
        return jsonify(response), 500


@app.route("/wallet", methods=["GET"]) #load key pair
def load_wallet():
    
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key)
        response = {
            "public_key": wallet.public_key,
            "private_key": wallet.private_key,
            "product_stock": blockchain.get_product_stock("apple")
        }
        
        return jsonify(response), 201
    else:
        response = {
            "message": "loading keys fail",
        }
        return jsonify(response), 500    

@app.route("/product_stock", methods=["GET"])
def get_product_stock():
    product_stock = blockchain.get_product_stock("apple")
    print(f"product_stock: {product_stock}")
    if product_stock != None:
        response = {
            "message": "fetching product stock successfully",
            "product_stock": product_stock
        }
        return jsonify(response), 200
    else:
        response = {
            "message": "fetching product stock fail",
            "wallet_set_up": wallet.public_key != None
        }
        return jsonify(response), 500

@app.route("/mine", methods=["POST"])
def mine():
    block = blockchain.mine_block()
    if block:
        dict_block = block.__dict__.copy()
        dict_block["transactions"] = [tx.__dict__ for tx in dict_block["transactions"]]
        response = {
            "message": "Adding a block successfully",
            "block": dict_block,
            "product_stock": blockchain.get_product_stock("apple")
        }
        
        return jsonify(response), 201

    else: # mining fail
        response = {
            "message": "Adding a block fail",
            "wallet_set_up": wallet.public_key != None
        }
        
        return jsonify(response), 500

@app.route("/transactions", methods=["GET"])
def get_transactions():
    transactions = blockchain.get_open_transactions()
    dict_transactons = [tx.__dict__ for tx in transactions]
    
    return jsonify(dict_transactons), 200

@app.route("/chain", methods=["GET"])
def get_chain():
    chain_snapshot = blockchain.chain
    dict_chain = [block.__dict__.copy() for block in chain_snapshot]
    for dict_block in dict_chain:
        dict_block['transactions'] = [tx.__dict__ for tx in dict_block['transactions']]
    return jsonify(dict_chain), 200 # message, status code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
