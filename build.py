#!/usr/bin/env python3

from Crypto.Signature import PKCS1_PSS
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Tx_classes import Input, Output, Tx
from hashlib import  sha256

def BuildTxn(Txn):

    accumulator = 0
    index = 0
    for i,output in enumerate(Txn['unusedOutputs']):
        accumulator += int(output['amount'])
        if accumulator >= Txn['total_amount']:
            index = i+1
            break

    if accumulator > Txn['total_amount']:
        self_output = {}
        self_output['publicKey'] = open(Txn['keys']['pubkey'], 'rb').read()
        self_output['amount'] = accumulator - Txn['total_amount']
        Txn['outputs'].append(self_output)

    outputs = []
    inputs = []
    output_bytes = len(Txn['outputs']).to_bytes(4, 'big')

    print(Txn['outputs'])

    for output in Txn['outputs']:
        classy_output = Output(output['amount'], output['publicKey'])
        outputs.append(classy_output)
        output_bytes += classy_output._bytes_

    for inp in Txn['unusedOutputs'][:index]:
        bytes_to_be_signed = bytes.fromhex(inp['transactionId']) + inp['index'].to_bytes(4, 'big') + sha256(output_bytes).digest()
        i#print(len(bytes_to_be_signed))
        skey = RSA.import_key(open(Txn['keys']['privkey'], 'rb').read())
        h = SHA256.new(bytes_to_be_signed)
        signature = PKCS1_PSS.new(skey).sign(h)

        classy_input = Input(bytes.fromhex(inp['transactionId']), inp['index'], signature)
        inputs.append(classy_input)

    Transaction = Tx()
    Transaction.newTxn(inputs, outputs)

    return Transaction







