#!/usr/bin/env python3

from struct import *

class Output:

    def __init__(self, amount, publickey):

        self.amount = int(amount)
        self.publickey = open(publickey, 'rb').read()
        self.len_pubkey = len(self.publickey)

        self._bytes_ = pack('>Q', self.amount) + pack('>I', self.len_pubkey) + self.publickey

class Input:

    def __init__(self, transID, index, signature):

        self.transID = bytes.fromhex(transID)
        self.index = int(index)
        self.signature = bytes.fromhex(signature)
        self.len_signature = len(self.signature)

        self._bytes_ = self.transID + pack('>I', self.index) + pack('>I', self.len_signature) + self.signature

class Tx:

    def __init__(self, nI, inputs, nO, outputs):

        self.num_inputs = nI
        self.inputs = inputs
        self.num_outputs = nO
        self.outputs = outputs

        self.input_bytes = inputs[0]._bytes_
        self.output_bytes = outputs[0]._bytes_

        for i in range(1, self.num_inputs):
            self.input_bytes += inputs[i]._bytes_

        for i in range(1, self.num_outputs):
            self.output_bytes += outputs[i]._bytes_

        self._bytes_ = pack('>I', self.num_inputs) + self.input_bytes + pack('>I', self.num_outputs) + self.output_bytes




