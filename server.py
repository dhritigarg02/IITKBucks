#!/usr/bin/env python3

from flask import Flask, request, jsonify, Response
from init import init, Worker, post_new_block
from threading import Thread
from queue import Queue
from block import block

app = Flask(__name__)

main_url = None
my_url = None
Blockchain = init(main_url, my_url)
queueflag = Queue()
thread = Thread(target = Worker, args = [Blockchain, queueflag])
thread.start()

@app.route('/getBlock/<num>')
def return_block(num):
    req_block= open('blockchain/block' + str(num), 'rb').read()
    r = Response(response = req_block, mimetype = 'application/octet-stream')
    return r

@app.route('/getPendingTransactions')
def txns():
    pendingtxns = Blockchain.PendingTxns.jsonList
    r = Respose(response = jsonify(pendingtxns), mimetype = 'application/json')
    return r

@app.route('/newPeer', methods = ['POST'])
def _newpeer_():
    if len(Blockchain.my_peers) < 5:
        url = request.get_json()
        if url['url'] not in Blockchain.my_peers:
            Blockchain.my_peers.append(url['url'])
            return 'Added ' + url['url'] + ' successfully!'
        else:
            return 'Peer already added!', 500
    else:
        return 'Peer limit reached, cannot add more peers', 500

@app.route('/getPeers')
def getPeers():
    return jsonify({"peers":Blockchain.my_peers})

@app.route('/newBlock', methods = ['POST'])
def newBlock():
    blockData = request.get_data()
    queueflag.put(True)
    thread.join()
    newblock = block()
    newblock.from_bytes(blockData.content)
    flag = Blockchain.addBlock(newblock)
    post_new_block(newblock)

    thread = Thread(target = Worker, args = [Blockchain, queueflag])
    thread.start()

    return 'Added Block to Blockchain successfully!'

@app.route('/newTransaction', methods = ['POST'])
def newTxn():
    data = request.get_json()
    Blockchain.PendingTxns.add(data)
    return 'Added Txn to list of pending Txns'

if __name__ == '__main__':
    app.run(host = '', port = 2020, debug = True)



