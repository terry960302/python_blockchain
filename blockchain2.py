import hashlib
import json
from time import time
from uuid import uuid4

from flask import jsonify, Flask, request

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # genesis block 생성
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # 거래 내역 초기화
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):

        self.current_transactions.append({
          'sender': sender,
          'recipient' : recipient,
          'amount' : amount,
        })

        return self.last_block['index'] + 1


    @property
    def last_block(self):
        return self.chain[-1]


    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: <dict> Block
        :return : <str>
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof):
        """
        POW 알고리즘 설명:
        - 앞에서 0의 개수가 4개가 나오는 hash(pp')을 만족시키는 p'을 찾는다.
        - p 는 이전 블록의 proof, p' 는 새로운 블록의 proof

        :param last_proof : <int>
        :return : <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Proof 검증 방법 : hash(last_proof, proof)의 값의 앞의 4자리가 0인가?

        :param last_proof : <int> 이전 블록의 proof 값
        :param proof : <int> 현재 블록의 proof 값
        :return : <bool> 옳다면 true 값 그렇지 않으면 false 값 반환
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()

@app.route('/')
def hello_world():
    return '<h1>이렇게 /하나인 거 만들어줘야 오류없음</h1><input type="textbox"/>'

@app.route('/mine', methods=['GET'])
def mine():
    # 다음 블록의 proof 값을 얻어내기 위해 POW 알고리즘을 수행한다.
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # proof 값을 찾으면(채굴에 성공하면) 보상을 준다.
    # sender의 주소를 0으로 한다. (원래 거래는 송신자, 수신자가 있어야 하는데 챌굴에 대한 보상으로 얻은 코인은 sender 가 없다.)
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    #
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transactions():
    values = request.get_json()

    # 요청된 필드가 POST 된 데이터인지 확인하는
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # 새로운 거래 생성
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(debug=True)
