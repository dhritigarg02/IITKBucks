#!/usr/bin/env python3

from flask import Flask, request, jsonify, Response
from init import init, Worker
from threading import Thread
from queue import Queue
from block import block
import requests

app = Flask(__name__)

main_url = 'https://iitkbucks.pclub.in'
my_url = None
Blockchain = init(main_url, my_url)
queueflag = Queue()
thread = Thread(target = Worker, args = [Blockchain, queueflag])
thread.start()

@app.route('/getBlock/<num>')
def return_block(num):
    req_block = open('blockchain/block' + str(num), 'rb').read()
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
    newblock.from_bytes(blockData)
    flag = Blockchain.addBlock(newblock)

    thread = Thread(target = Worker, args = [Blockchain, queueflag])
    thread.start()

    return 'Added Block to Blockchain successfully!'

@app.route('/addAlias', methods = ['POST'])
def alias():
    alias_data = request.get_json()
    if alias_data['alias'] in Blockchain.alias_map:
        return 'Alias already set!', 400
    else:
        Blockchain.alias_map[alias_data['alias']] = alias_data['publickey']
        for peer in Blockchain.peers:
            r = requests.post(peer + '/addAlias', json = jsonify(alias_data)) 
        return 'Alias set successfully!', 200

@app.route('/getPublicKey', methods = ['POST'])
def return_pubkey():
    data = request.get_json()
    if data['alias'] in Blockchain.alias_map:
        data = {'publicKey': Blockchain.alias_map[data['alias']]}
        return jsonify(data), 200
    else:
        return 'Not found!', 404

@app.route('/getUnusedOutputs', methods = ['POST'])
def UO():
    data = request.get_json()
    if "alias" in data:
        pubkey = Blockchain.alias_map[data["alias"]]
    else:
        pubkey = data["publicKey"]
    if pubkey in Blockchain.unused_outputs_by_key:
        return jsonify({"unusedOutputs":Blockchain.unused_outputs_by_key[pubkey]}), 200
    else:
        return 'No unused outputs found!', 400

@app.route('/newTransaction', methods = ['POST'])
def newTxn():
    data = request.get_json()
    Blockchain.PendingTxns.add(data)
    return 'Added Txn to list of pending Txns'

if __name__ == '__main__':
    app.run(host = '', port = 2020, debug = True)



