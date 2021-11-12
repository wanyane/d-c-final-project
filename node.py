from argparse import ArgumentParser
from os import replace
from typing import ChainMap, ValuesView
from flask import Flask, jsonify, request
from flask.wrappers import Response
from flask_cors import CORS
from wallet import Wallet
from blockchain import Blockchain

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def get_UI():
    return "this works"

@app.route("/broadcast-block", methods=["POST"])
def broadcast_block():
    values = request.get_json()
    if not values:
        response = {
            "message": "No data found!",
        }
        return jsonify(response), 400
    
    if "block" not in values:
        response = {
            "message": "required data is missing"
        }
        return jsonify(response), 400
    
    block = values["block"]
    if block["index"] == blockchain.chain[-1].index + 1:
        if blockchain.add_block(block):
            respond = {
                "message": "block added successfully"
            }
            return jsonify(respond), 201
        else:
            respond = {
                "message": "block seems to be invalid"
            }
            return jsonify(respond), 409
    elif block["index"] > blockchain.chain[-1].index:
        response = {
            "message": "block chain seems to be differ from local blockchain"
        }
        blockchain.resolve_conflicts = True
        return jsonify(response), 200
    else:
        response = {
            "message": "block chain seems to be shorter, block not added"
        }
        return jsonify(response), 409



@app.route("/broadcast-transaction", methods=["POST"])
def broadcast_transaction():
    values = request.get_json()
    print(values)
    if not values:
        response = {
            "message": "No data found!",
        }
        return jsonify(response), 400
    else:
        required_field = ["sender", "recipient", "amount", "product_name", "price", "signature"]
        valid = all([field in values for field in required_field])
        if not valid:
            response = {
                "message": "required data is missing"
            }
            return jsonify(response), 400
        else:
            success = blockchain.add_transaction(values["recipient"], values["sender"], values["signature"], values["amount"], values["product_name"], values["price"], is_receiving=True)
            if success:
                response = {
                    "message": "successfully creating a transaction",
                    "sender": values["sender"],
                    "recipient": values["recipient"],
                    "signature": values["signature"],
                    "amount": values["amount"],
                    "product_name": values["product_name"],
                    "price": values["price"],
                }
                return jsonify(response), 201
            else:
                response = {
                    "message": "creating a transactin failed",
                }

                return jsonify(response), 500
 
@app.route("/transaction", methods=["POST"])
def add_transaction():
    values = request.get_json()
    if not values:
        response = {
            "message": "No data found!",
        }
        return jsonify(response), 400
    else:
        required_field = ["is_nature", "recipient", "amount", "product_name", "price"]
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
            
            signature = wallet.sign_transaction(sender, values["recipient"], values["amount"], values["product_name"], values["price"])
            success = blockchain.add_transaction(values["recipient"], sender, signature, values["amount"], values["product_name"], values["price"])
            if success:
                response = {
                    "message": "successfully creating a transaction",
                    "sender": sender,
                    "recipient": values["recipient"],
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
        blockchain = Blockchain(wallet.public_key, node_id)
        response = {
            "public_key": wallet.public_key,
            "private_key": wallet.private_key,
            "product_stock": blockchain.get_product_stock(sender=wallet.public_key ,product_name="apple")
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
        blockchain = Blockchain(wallet.public_key, node_id)
        response = {
            "public_key": wallet.public_key,
            "private_key": wallet.private_key,
            "product_stock": blockchain.get_product_stock(wallet.public_key, "apple")
        }
        
        return jsonify(response), 201
    else:
        response = {
            "message": "loading keys fail",
        }
        return jsonify(response), 500    

@app.route("/product_stock/<sender>&<product_name>", methods=["GET"])
def get_product_stock(sender, product_name):
    product_stock = blockchain.get_product_stock(sender, product_name)
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
    if blockchain.resolve_conflicts == True:
        response = {
            "message": "resolve conflicts first, block not added"
        }
        return jsonify(response), 409
    block = blockchain.mine_block()
    if block:
        dict_block = block.__dict__.copy()
        dict_block["transactions"] = [tx.__dict__ for tx in dict_block["transactions"]]
        response = {
            "message": "Adding a block successfully",
            "block": dict_block,
            "product_stock": blockchain.get_product_stock(wallet.public_key, "apple")
        }
        
        return jsonify(response), 201

    else: # mining fail
        response = {
            "message": "Adding a block fail",
            "wallet_set_up": wallet.public_key != None
        }
        
        return jsonify(response), 500

@app.route("/resolve-conflicts", methods=["POST"])
def resolve_conflicts():
    replace = blockchain.resolve()
    if replace:
        response = {
            "message": "chain replaced"
        }
    else:
        response = {
            "message": "local chain is kept"
        }
    return jsonify(response), 200


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

@app.route("/nodes", methods=["GET"])
def get_nodes():
    nodes = blockchain.get_peer_nodes()
    response = {
        "peer_nodes": nodes
    }
    return jsonify(response), 200

@app.route("/node/<node_url>", methods=["DELETE"])
def delete_node(node_url):
    if node_url == None or node_url == "":
        response = {
            "message": "Invalid input data for node url",
            "node_url": node_url
        }
        return jsonify(response), 500
    else:
        blockchain.remove_peer_node(node_url)
        response = {
            "message": "Deleting node successfully",
            "peer_nodes": blockchain.get_peer_nodes()
        }
        return jsonify(response), 201

@app.route("/node", methods=["POST"])
def add_node():
    values = request.get_json()
    if not values:
        response = {
            "message": "No data found!",
        }
        return jsonify(response), 400
    else:
        if "node" not in values:
            response = {
                "message": "No node data found"
            }
            return jsonify(response), 400
        else:
            blockchain.add_peer_node(values["node"])
            response = {
                "message": "Adding node successfully",
                "peer_nodes": blockchain.get_peer_nodes()
            }
            return jsonify(response), 201
    

        
    



if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=5000)
    args = parser.parse_args()
    node_id = port=args.port
    
    wallet = Wallet(node_id)
    blockchain = Blockchain(wallet.public_key, node_id)
    app.run(host="0.0.0.0", port=node_id)
