#!/usr/bin/env python3

from struct import *
from hashlib import sha256
from Crypto.Signature import pss

class Output:

    def __init__(self, amount, publickey):

        self.amount = amount
        self.publickey = open(publickey, 'rb').read()
        self.len_pubkey = len(self.publickey)

        self._bytes_ = pack('>Q', self.amount) + pack('>I', self.len_pubkey) + self.publickey

class Input:

    def __init__(self, transID, index, signature):

        self.transID = transID
        self.index = index
        self.signature = signature
        self.len_signature = len(self.signature)

        self._bytes_ = self.transID + pack('>I', self.index) + pack('>I', self.len_signature) + self.signature

    
class Tx:

    def newTxn(self, nI, inputs, nO, outputs):

        self.num_inputs = nI
        self.inputs = inputs
        self.num_outputs = nO
        self.outputs = outputs
        TxnToBytes(self)

    def TxnToBytes(self):

        self.input_bytes = inputs[0]._bytes_
        self.output_bytes = outputs[0]._bytes_

        for i in range(1, self.num_inputs):
            self.input_bytes += inputs[i]._bytes_

        for i in range(1, self.num_outputs):
            self.output_bytes += outputs[i]._bytes_

        self._bytes_ = pack('>I', self.num_inputs) + self.input_bytes + pack('>I', self.num_outputs) + self.output_bytes

        self.ID = sha256(self._bytes_).digest()

    def TxnfromBytes(self, txnbytes):
        
        ci = 0
        self.num_inputs = int.from_bytes(bb[ci:ci+4], 'big')
        ci += 4
        inputs = []
        for i in range(num_inputs):
            transID = bb[ci:ci+32]
            ci += 32
            index = int.from_bytes(bb[ci:ci+4], 'big')
            ci += 4
            len_signature = int.from_bytes(bb[ci:ci+4], 'big')
            ci += 4
            signature = bb[ci:ci+len_signature]
            ci += len_signature
            inputs.append(Input(transID, index, signature))
        self.inputs = inputs

        self.num_outputs = int.from_bytes(bb[ci:ci+4], 'big')
        ci += 4
        outputs = []
        for i in range(num_outputs):
            num_coins = int.from_bytes(bb[ci:ci+8], 'big')
            ci += 8
            len_pubkey = int.from_bytes(bb[ci:ci+4], 'big')
            ci += 4
            pubkey = bb[ci:ci+len_pubkey]
            ci += len_pubkey
            outputs.append(Output(num_coins, pubkey))
        self.outputs = outputs

        TxnToBytes(self)

    def ValidateTxn(self,  unused_outputs):

        flag = True
        total_input_coins = 0
        total_output_coins = 0
        temp_used_outputs = {}

        for Input in self.inputs:
            try:
                total_input_coins += unused_outputs[Input.transID][Input.index]["coins"]
            except:
                flag = False
                return flag
        for Output in self.outputs:
            total_output_coins += int.from_bytes(Output.amount, 'big')

        if total_output_coins > total_input_coins:
            flag = False
            return flag

        for Input in self.inputs:
            try:
                verifier = pss.new(unused_outputs[Input.transID][Input.index]["Publickey"])
                data = Input.transID + Input.index.to_bytes(4, 'big') + sha256(self.num_outputs.to_bytes(4, 'big') + self.output_bytes).digest()
                verifier.verify(data, Input.signature)

                temp_used_outputs[Input.transID][Input.index] = unused_outputs[Input.transID].pop[Input.index]
            except:
                for transId in temp_used_outputs:
                    if transID in unused_outputs:
                        unused_outputs.update(temp_used_outputs[transID])
                    else:
                        unused_outputs[transID] = temp_used_outputs[transID]

                flag = False
                return flag
        return flag, unused_outputs

class Coinbase:

    def new(self, output):
        self.output = output
        self._bytes_ = self.output._bytes_

    def fromBytes(self, txnbytes):
        ci = 0
        num_coins = int.from_bytes(txnbytes[ci:ci+8], 'big')
        ci += 8
        len_pubkey = int.from_bytes(txnbytes[ci:ci+4], 'big')
        ci += 4
        pubkey = txnbytes[ci:ci+len_pubkey]
        self.output = Output(num_coins, pubkey)
        self._bytes_ = self.output._bytes_



