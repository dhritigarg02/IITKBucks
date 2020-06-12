#!/usr/bin/env python3

from flask import Flask, request, jsonify, Response

app = Flask(__name__)

@app.route('/getBlock/<num>')
def return_block(int(num)):
    req_block= open('blockchain/block' + str(num), 'rb').read()
    r = Response(response = req_block, mimetype = 'application/octet-stream')
    r.headers['Content-Type'] = 'application/octet-stream'
    return r

@app.route('/getPendingTransactions')
def txns():
    pendingtxns = get_pending_txns()
    pendingtxnsdict = {"transactions":[]}

    for txn in pendingtxns:
        inputs = [{"transactionID":x.transID, "index":x.index, "signature":x.signature} for x in txn.inputs]
        outputs = [{"amount":y.amount, "recipient":y.publickey} for y in txn.outputs]
        pendingtxnsdict["transactions"].append({"inputs":inputs, "outputs":outputs})

    r = Respose(response = jsonify(pendingtxnsdict), mimetype = 'application/json')
    r.headers['Content-Type'] = 'application/json'
    return r

if __name__ == '__main__':
    app.run(host = '', port = 2020, debug = True)



