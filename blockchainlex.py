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

class blockchainlex(object):
    difficulty_target = "0000"

    def hash_block(self, block):
        block_encode = json.dumps(block, short_key=True).encode()
        hash_block = hashlib.sha256(block_encode).hexdigest()
        return hash_block
    
    def __init__(self):
        self.chain = []
        self.current_transaction = []
        genesis_block = self.hash_block("genesis_block")

        self.append_block(
            hash_of_previous_block = genesis_block,
            nonce = self.proof_of_work(0, genesis_block, [])
        )

    def append_block(self, hash_of_previous_block, nonce):
        block = {
            "index": len(self.chain),
            "timestamp": time(),
            "hash_of_previous_block": hash_of_previous_block,
            "nonce": nonce,
            "current_transaction" : self.current_transaction,
        }

        self.current_transaction = []

        self.chain.append(block)

        return block
    
    def proof_of_work(self, index, previous_block, transaction, nonce):
        nonce = 0

        while self.valid_proove(index, previous_block, transaction, nonce) is False:
            nonce += 1
        return nonce

    def valid_proove(self, index, previous_block, transaction, nonce):
        nonce_encode = f"{index}{previous_block}{transaction}{nonce}".encode()
        hash_nonce = hashlib.sha256(nonce_encode).hexdigest()
        return hash_nonce[:len(self.difficulty_target)] == self.difficulty_target

    def add_transaction(self, sender, recipient, amount):
        self.current_transaction.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index'] + 1
    
    @property
    def last_block(self):
        return self.chain[-1]