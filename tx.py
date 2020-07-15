#!/usr/bin/env python3

from struct import *
from hashlib import sha256
from Crypto.Signature import PKCS1_PSS
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import random
import requests
from operator import itemgetter
import json

class Output:

    def __init__(self, amount, publickey):

        self.amount = amount
        self.publickey = publickey
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
        self.TxnToBytes()

    def TxnToBytes(self):
        
        if self.num_inputs != 0:
            self.input_bytes = self.inputs[0]._bytes_
            for i in self.inputs[1:]:
                self.input_bytes += i._bytes_
        
        self.output_bytes = self.outputs[0]._bytes_
        for o in self.outputs[1:]:
            self.output_bytes += o._bytes_

        if self.num_inputs != 0:
            self._bytes_ = pack('>I', self.num_inputs) + self.input_bytes + pack('>I', self.num_outputs) + self.output_bytes
        else:
            self._bytes_ = pack('>I', self.num_inputs) + pack('>I', self.num_outputs) + self.output_bytes

        self.ID = sha256(self._bytes_).digest()
        self.size = pack('>I', len(self._bytes_))

    def TxnfromBytes(self, txnbytes):
        
        ci = 0
        bb = txnbytes
        self.num_inputs = int.from_bytes(bb[ci:ci+4], 'big')
        ci += 4
        inputs = []
        for i in range(self.num_inputs):
            transID = bb[ci:ci+32]
            ci += 32
            index = int.from_bytes(bb[ci:ci+4], 'big')
            ci += 4
            len_signature = int.from_bytes(bb[ci:ci+4], 'big')
            #print('Len of signature: ', len_signature)
            ci += 4
            signature = bb[ci:ci+len_signature]
            ci += len_signature
            inputs.append(Input(transID, index, signature))
        self.inputs = inputs

        self.num_outputs = int.from_bytes(bb[ci:ci+4], 'big')
        ci += 4
        outputs = []
        for i in range(self.num_outputs):
            num_coins = int.from_bytes(bb[ci:ci+8], 'big')
            ci += 8
            len_pubkey = int.from_bytes(bb[ci:ci+4], 'big')
            ci += 4
            pubkey = bb[ci:ci+len_pubkey]
            ci += len_pubkey
            outputs.append(Output(num_coins, pubkey))
        self.outputs = outputs

        self.TxnToBytes()

    def TxnfromJson(self, txn):

        inputs = [Input(x["transactionId"], x["index"], x["signature"]) for x in txn["inputs"]]
        outputs = [Output(x["amount"], x["recipient"]) for x in txn["outputs"]]
        self.newTxn(inputs, outputs)

    def toJson(self):

        json = {}
        json['inputs'] = [{'transactionId': x.transID, 'index': x.index, 'signature': x.signature} for x in self.inputs]
        json['outputs'] = [{'amount': x.amount, 'recipient':x.publickey} for x in self.outputs]

        return json

    def VerifyTxn(self, unused_outputs):

        total_input_coins = 0
        total_output_coins = 0
        temp_used_outputs = {}

        try:
            txn_fees = self.getTxnFees(unused_outputs)
            print(txn_fees)
            if not txn_fees >= 0:
                print('!!')
                return False, unused_outputs
        except:
            print('?')
            return False, unused_outputs

        for Input in self.inputs:

            publickey = RSA.import_key(unused_outputs[Input.transID][Input.index]["Publickey"])
            verifier = PKCS1_PSS.new(publickey)
            data = Input.transID + Input.index.to_bytes(4, 'big') + sha256(self.num_outputs.to_bytes(4, 'big') + self.output_bytes).digest()
            print('\n', len(data), '\n')
            print('\n', unused_outputs[Input.transID][Input.index]["Publickey"].hex(), '\n')
            print('\n', data.hex(), '\n')
            print('\n', Input.signature.hex(), '\n')
            h = SHA256.new(data)
            if verifier.verify(h, Input.signature):
                if Input.transID in temp_used_outputs:
                    temp_used_outputs[Input.transID][Input.index] = unused_outputs[Input.transID].pop(Input.index)
                else:
                    temp_used_outputs[Input.transID] = {}
                    temp_used_outputs[Input.transID][Input.index] = unused_outputs[Input.transID].pop(Input.index)
            else:
                print('signature not verified!')
                return False, unused_outputs

        return True, unused_outputs

    def processTxn(self, Blockchain):

        #print(Blockchain.unused_outputs)
        for Input in self.inputs:
            #print(Input.index)
            Blockchain.unused_outputs[Input.transID].pop(Input.index)

        Blockchain.unused_outputs[self.ID] = {}
        for i, output in enumerate(self.outputs):
            Blockchain.unused_outputs[self.ID][i] = {"Publickey":output.publickey, "coins":output.amount}
       
            if output.publickey in Blockchain.unused_outputs_by_key:
                Blockchain.unused_outputs_by_key[output.publickey].append({"transactionID":self.ID, "index":i, "amount":output.amount})
            else:
                Blockchain.unused_outputs_by_key[output.publickey] = [{"transactionID":self.ID, "index":i, "amount":output.amount}]
            
        if self.num_inputs != 0:
            Blockchain.PendingTxns.remove(self)

    def getTxnFees(self, unused_outputs):

        self.total_input_coins = 0
        self.total_output_coins = 0
        for Input in self.inputs:
            self.total_input_coins += unused_outputs[Input.transID][Input.index]["coins"]
        for Output in self.outputs:
            self.total_output_coins += Output.amount

        self.TxnFees = self.total_input_coins - self.total_output_coins 
        return self.TxnFees

class PendingTxns:

    def __init__(self):

        self._list_ = []

    def get(self, my_peers):

        peer = random.choice(my_peers)
        r = requests.get(peer + '/getPendingTransactions')
        self.jsonList = r.json()

        self.JsonToClass()

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


        


            





