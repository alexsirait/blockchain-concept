import sys
import hashlib
import json

from time import time
from uuid import uuid4

from flask import Flask
from flask.globals import request
from flask.json import jsonify

import requests
from urllib.parse import urlparse

class Blockchain(object):
    difficulty_target = "0000";

    def hash_block(self, block):
        block_encode = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(block_encode).hexdigest()

    def __init__(self):
        self.nodes = set()
        self.chain = []
        self.current_transaction = []
        genesis_hash = self.hash_block("genesis_block")

        self.append_block(
            hash_of_previous_block = genesis_hash,
            nonce = self.proof_of_work(0, genesis_hash, [])
        )
    
    def add_node(self, address):
        parse_url = urlparse(address)
        self.nodes.add(parse_url.netloc)
        print(parse_url.netloc)

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            if block['hash_of_previous_block'] != self.hash_block(last_block):
                return False
            
            if not self.valid_proof(
                current_index,
                block['hash_of_previous_block'],
                block['transaction'],
                block['nonce'],
            ):
                return False
            last_block = block
            current_index += 1

        return True
    
    def update_blockchain(self):
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            res = requests.get(f'http://{node}/blockchain')

            if res.status_code == 200:
                length = res.json()['length']
                chain = res.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

                if new_chain:
                    self.chain = new_chain
                    return True
                
        return False
    
    
    def proof_of_work(self, index, hash_of_previous_block, transaction):
        nonce = 0
        while self.valid_proof(index, hash_of_previous_block, transaction, nonce) is False:
            nonce += 1
        return nonce
    
    def valid_proof(self, index, hash_of_previous_block, transaction, nonce):
        content = f'{index}{hash_of_previous_block}{transaction}{nonce}'.encode()

        content_hash = hashlib.sha256(content).hexdigest()

        return content_hash[:len(self.difficulty_target)] == self.difficulty_target

    def append_block(self, nonce, hash_of_previous_block):
        block = {
            'index': len(self.chain),
            'timestamp': time(),
            'transaction': self.current_transaction,
            'nonce': nonce,
            'hash_of_previous_block': hash_of_previous_block
        }

        self.current_transaction = []

        self.chain.append(block)
        return block
    
    def add_transaction(self, sender, recipient, amount):
        self.current_transaction.append({
            'amount': amount,
            'recipient': recipient,
            'sender': sender,
        })

        return self.last_block['index'] + 1
    
    @property
    def last_block(self):
        return self.chain[-1]

# app
app = Flask(__name__)
node_identifier = str(uuid4()).replace('-','')
blockchain = Blockchain()

@app.route('/blockchain', methods=['GET'])
def full_chain():
    res = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(res), 200

@app.route('/mine', methods=['GET'])
def mine_block():
    blockchain.add_transaction("0", node_identifier, 1)
    last_block_hash = blockchain.hash_block(blockchain.last_block)
    index = len(blockchain.chain)
    nonce = blockchain.proof_of_work(index, last_block_hash, blockchain.current_transaction)
    block = blockchain.append_block(nonce, last_block_hash)
    res = {
        'timestamp': time(),
        'transaction': block['transaction'],
        'nonce': block['nonce'],
        'hash_of_previous_block': block['hash_of_previous_block'],
        'message': 'yeayy.. mined !!!'
    }

    return jsonify(res), 200

@app.route('/transaction/new', methods=['POST'])
def new_transactions():
    value = request.get_json()
    check_value = ["sender", "recipient", "amount"]
    if not all(k in value for k in check_value):
        return "Opps, not valid :|", 400
    
    blockchain.add_transaction(value['sender'], value['recipient'], value['amount'])
    res = {
        'message': f'Transaction add block {len(blockchain.chain)}',
    }
    return jsonify(res), 201

@app.route('/nodes/add_nodes', methods=['POST'])
def add_nodes():
    value = request.get_json()
    nodes = value.get('nodes')

    if nodes is None:
        return "Error, :|", 400
    
    for node in nodes:
        blockchain.add_node(node)

    res = {
        'message': 'Node added :)',
        'nodes': list(blockchain.nodes)
    }

    return jsonify(res), 200

@app.route('/nodes/sync', methods=['GET'])
def sync():
    updated = blockchain.update_blockchain()
    if updated:
        res = {
            'message': 'Blockchain updated with new block :)',
            'blockchain': blockchain.chain
        }
    else:
        res = {
            'message': 'Blockchain updated :)',
            'blockchain': blockchain.chain
        }
    return jsonify(res), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(sys.argv[1]))



    

    
