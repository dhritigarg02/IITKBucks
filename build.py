#!/usr/bin/env python3

from Crypto.Signature import PKCS1_PSS
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Tx import Input, Output, Tx

def BuildTxn(Txn):

    accumulator = 0
    index = 0
    for i,output in enumerate(Txn['unused_outputs']):
        accumulator += output['amount']
        if accumulator >= Txn['total_amount']:
            index = i+1
            break

    if accumulator >= Txn['total_amount']:
        self_output = {}
        self_output['publicKey'] = Txn['keys']['pubkey']
        self_output['amount'] = accumulator - Txn['total_amount']
        Txn['outputs'].append(self_output)

    outputs = []
    inputs = []
    output_bytes = len(Txn['outputs']).to_bytes(4, 'big')

    for output in Txn['outputs']:
        classy_output = Output(output['amount'], output['publicKey'])
        outputs.append(classy_output)
        output_bytes += classy_output._bytes_

    for inp in Txn['unused_outputs'][:index]:
        bytes_to_be_signed = inp['transactionId'] + inp['index'].to_bytes(4, 'big') + output_bytes
        skey = RSA.import_key(Txn['keys']['privkey'])
        h = SHA256.new(bytes_to_be_signed)
        signature = PKCS1_PSS.new(skey).sign(h)

        classy_input = Input(inp['transactionId'], inp['index'], signature)
        inputs.append(classy_input)

    Transaction = Tx()
    Transaction.newTxn(inputs, outputs)

    return Transaction







