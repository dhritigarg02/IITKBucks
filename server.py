#!/usr/bin/env python3

from flask import Flask, request, jsonify, Response

app = Flask(__name__)

my_peers = []

@app.route('/getBlock/<num>')
def return_block(num):
    req_block= open('blockchain/block' + str(num), 'rb').read()
    r = Response(response = req_block, mimetype = 'application/octet-stream')
    r.headers['Content-Type'] = 'application/octet-stream'
    return r

@app.route('/getPendingTransactions')
def txns():
    pendingtxns = pendingtxns._list_
    pendingtxnsdict = {"transactions":[]}

    for txn in pendingtxns:
        inputs = [{"transactionID":x.transID, "index":x.index, "signature":x.signature} for x in txn.inputs]
        outputs = [{"amount":y.amount, "recipient":y.publickey} for y in txn.outputs]
        pendingtxnsdict["transactions"].append({"inputs":inputs, "outputs":outputs})

    r = Respose(response = jsonify(pendingtxnsdict), mimetype = 'application/json')
    r.headers['Content-Type'] = 'application/json'
    return r

@app.route('/newPeer', methods = ['POST'])
def _newpeer_():
    url = request.get_json()
    if len(my_peers) < 5:
        if url['url'] not in my_peers:
            my_peers.append(url['url'])
            return 'Added ' + url['url'] + ' successfully!'
        else:
            return 'Peer already added!'
    else:
        return 'Peer limit reached, cannot add more peers', 500

@app.route('/getPeers')
def getPeers():
    return jsonify({"peers":my_peers})

@app.route('/newBlock', methods = ['POST'])
def newBlock():
    blockData = request.get_data()
    blockchain.add_block(blockData)
    return 'Added Block to Blockchain successfully!'

@app.route('/newTransaction', methods = ['POST'])
def newTxn():
    data = request.get_json()
    pendingTxns.add(data)
    return 'Added Txn to list of pending Txns'

if __name__ == '__main__':
    app.run(host = '', port = 2020, debug = True)



