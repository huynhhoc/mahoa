import hashlib
import json
from time import time
import requests
class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()
        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)
    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain
        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """
        block = {
        	'index': len(self.chain) + 1,
        	'timestamp': time(),
        	'transactions': self.current_transactions,
        	'proof': proof,
        	'previous_hash': previous_hash or self.hash(self.chain[-1]),
    	}
    	# Reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block
    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block
        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
        	'sender': sender,
        	'recipient': recipient,
        	'amount': amount,
    	})
        return self.last_block['index'] + 1
    
    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        """
        Returns the last Block in the chain
        """
        return self.chain[-1]
    
    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:
        - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
        - p is the previous proof, and p' is the new proof

        :param last_proof: <int> The previous proof of work
        :return: <int> The new proof of work
        """
        # Get the value of the last proof from the previous block
        last_proof = last_block['proof']
        
        # Calculate the hash of the previous block to use in finding a new proof
        last_hash = self.hash(last_block)

        # Initialize the proof to 0
        proof = 0

        # Loop until a proof satisfying the condition is found
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        # Return the newly found proof
        return proof


    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Validates the Proof

        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :param last_hash: <str> Hash of the Previous Block
        :return: <bool> True if correct, False if not.
        """
        # Combine the previous proof, current proof, and hash of the previous block
        # Encode the combined string to bytes for hashing
        guess = f'{last_proof}{proof}{last_hash}'.encode()

        # Hash the combined string using the SHA-256 algorithm
        guess_hash = hashlib.sha256(guess).hexdigest()

        # Check if the hash has at least 4 leading zeros, which is a common criterion for Proof
        # of Work in many blockchain implementations.
        # The number of leading zeros determines the difficulty of the Proof of Work. 
        return guess_hash[:4] == "0000"

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1
        
        return True

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: <bool> True if our chain was replaced, False if not
        """
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new,valid chain longerthan ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

