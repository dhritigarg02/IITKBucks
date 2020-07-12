#!/usr/bin/env python3

from struct import *
from hashlib import sha256
from Crypto.Signature import pss
import random
import requests
from operator import itemgetter

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

    def newTxn(self, inputs, outputs):

        self.num_inputs = len(inputs)
        self.inputs = inputs
        self.num_outputs = len(outputs)
        self.outputs = outputs
        TxnToBytes(self)

    def TxnToBytes(self):

        self.input_bytes = self.inputs[0]._bytes_
        self.output_bytes = self.outputs[0]._bytes_

        for i in self.inputs[1:]:
            self.input_bytes += i._bytes_

        for o in self.outputs[1:]:
            self.output_bytes += o._bytes_

        self._bytes_ = pack('>I', self.num_inputs) + self.input_bytes + pack('>I', self.num_outputs) + self.output_bytes

        self.ID = sha256(self._bytes_).digest()
        self.size = pack('>I', len(self._bytes_))

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

    def TxnfromJson(self, json):

        inputs = [Input(x["transactionID"], x["index"], x["signature"]) for x in txn["inputs"]]
        outputs = [Output(x["amount"], x["publickey"]) for x in txn["outputs"]]
        newTxn(self, inputs, outputs)

    def VerifyTxn(self, unused_outputs):

        total_input_coins = 0
        total_output_coins = 0
        temp_used_outputs = {}

        def revert(unused_outputs, temp_used_outputs):
            for transId in temp_used_outputs:
                if transID in unused_outputs:
                    unused_outputs[transID].update(temp_used_outputs[transID])
                else:
                    unused_outputs[transID] = temp_used_outputs[transID]

            return unused_outputs

        for Input in self.inputs:
            try:
                total_input_coins += unused_outputs[Input.transID][Input.index]["coins"]
            except:
                return False, unused_outputs
        for Output in self.outputs:
            total_output_coins += Output.amount

        if total_output_coins > total_input_coins:
            return False, unused_outputs

        for Input in self.inputs:
            try:
                verifier = pss.new(unused_outputs[Input.transID][Input.index]["Publickey"])
                data = Input.transID + Input.index.to_bytes(4, 'big') + sha256(self.num_outputs.to_bytes(4, 'big') + self.output_bytes).digest()
                verifier.verify(data, Input.signature)

                temp_used_outputs[Input.transID][Input.index] = unused_outputs[Input.transID].pop[Input.index]
            except:
                unused_outputs = revert(unused_outputs, temp_used_outputs)
                return False, unused_outputs

        return True, unused_outputs

    def processTxn(self, Blockchain):

        for Input in self.inputs:
            Blockchain.unused_outputs[Input.transID].pop[Input.Index]
        for i, output in enumerate(self.outputs):
            Blockchain.unused_outputs[self.ID][i] = {"Publickey":output.publickey, "coins":output.amount}
       
            if output.publickey in Blockchain.unused_outputs_by_key:
                Blockchain.unused_outputs_by_key[output.publickey].append({"transactionID":self.ID, "index":i, "amount":output.amount})
            else:
                Blockchain.unused_outputs_by_key[output.publickey] = [{"transactionID":self.ID, "index":i, "amount":output.amount}]
            
        Blockchain.PendingTxns.remove(self)

    def getTxnFees(self, unused_outputs):

        self.total_input_coins = 0
        self.total_output_coins = 0
        for Input in self.inputs:
            self.total_input_coins += unused_outputs[Input.transID][Input.index]["coins"]
        for Output in self.outputs:
            total_output_coins += Output.amount

        self.TxnFees = self.total_input_coins - total_output_coins 
        return self.TxnFees

class Coinbase:

    block_reward = 50
    my_publickey = None

    def new(self, BlockFees):
        self.output = Output(self.block_reward + BlockFees, self.my_publickey)
        self._bytes_ = self.output._bytes_
        self.size = len(self._bytes_).to_bytes(4, 'big')

    def fromBytes(self, txnbytes):
        ci = 0
        num_coins = int.from_bytes(txnbytes[ci:ci+8], 'big')
        ci += 8
        len_pubkey = int.from_bytes(txnbytes[ci:ci+4], 'big')
        ci += 4
        pubkey = txnbytes[ci:ci+len_pubkey]
        self.output = Output(num_coins, pubkey)
        self._bytes_ = self.output._bytes_
        self.ID = sha256(self._bytes_).digest()

    def processTxn(self, Blockchain):

            Blockchain.unused_outputs[self.ID][i] = {"Publickey":self.output.publickey, "coins":self.output.amount}

class PendingTxns:

    def get(self, my_peers):

        peer = random.choice(my_peers)
        r = requests.get(peer + '/getPendingTransactions')
        self.jsonList = r.json

        JsonToClass(self)

    def JsonToClass(self):

        self._list_ = []
        for txn in self.jsonList:
            Txn = Tx()
            Txn.TxnfromJson(txn)
            self._list_.append(Txn)

    def sort(self):
        
        TxnFeesList = [Txn.getTxnFees for Txn in self._list_]
        self.sorted_list = sorted(zip(self._list_, TxnFeesList), key = itemgetter(1), reverse = True)

        #return self.sorted_list

    def add(self, json):

        self.jsonList.append(json)
        Txn = Tx()
        Txn.TxnfromJson(json)
        self._list_.append(Txn)

    def remove(self, txn):

        for i, tx in enumerate(self._list_):
            if tx.ID == txn.ID:
                del self._list_[i]
                del self.jsonList[i]
                break


        


            





