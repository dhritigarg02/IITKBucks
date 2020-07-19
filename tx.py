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
import copy

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

        self.input_bytes = b''
        self.output_bytes = b''

        for i in self.inputs:
                self.input_bytes += i._bytes_
        
        for o in self.outputs:
            self.output_bytes += o._bytes_

        self._bytes_ = pack('>I', self.num_inputs) + self.input_bytes + pack('>I', self.num_outputs) + self.output_bytes

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

        inputs = [Input(bytes.fromhex(x["transactionId"]), x["index"], bytes.fromhex(x["signature"])) for x in txn["inputs"]]
        outputs = [Output(int(x["amount"]), x["recipient"].encode()) for x in txn["outputs"]]
        self.newTxn(inputs, outputs)

    def toJson(self):

        json = {}
        json['inputs'] = [{'transactionId': x.transID.hex(), 'index': x.index, 'signature': x.signature.hex()} for x in self.inputs]
        json['outputs'] = [{'amount': str(x.amount), 'recipient':x.publickey.decode()} for x in self.outputs]

        return json

    def VerifyTxn(self, u_o):

        unused_outputs = copy.deepcopy(u_o)
        temp_used_outputs = {}

        try:
            txn_fees = self.getTxnFees(unused_outputs)
            #print(txn_fees)
            if not txn_fees >= 0:
                print('\nOutput amount exceeds input amount!')
                return False, unused_outputs
        except:
            print('\nInput not in list of unused outputs!')
            return False, unused_outputs

        for Input in self.inputs:

            publickey = RSA.import_key(unused_outputs[Input.transID][Input.index]["Publickey"])
            verifier = PKCS1_PSS.new(publickey)
            data = Input.transID + Input.index.to_bytes(4, 'big') + sha256(self.num_outputs.to_bytes(4, 'big') + self.output_bytes).digest()
            h = SHA256.new(data)
            if verifier.verify(h, Input.signature):
                if Input.transID in temp_used_outputs:
                    temp_used_outputs[Input.transID][Input.index] = unused_outputs[Input.transID].pop(Input.index)
                else:
                    temp_used_outputs[Input.transID] = {}
                    temp_used_outputs[Input.transID][Input.index] = unused_outputs[Input.transID].pop(Input.index)
            else:
                print('\nInvalid Signature!')
                return False, unused_outputs

        return True, unused_outputs

    def processTxn(self, Blockchain):

        for Input in self.inputs:
            pubkey = Blockchain.unused_outputs[Input.transID][Input.index]['Publickey']
            temp = copy.deepcopy(Blockchain.unused_outputs_by_key[pubkey])
            for i, output in enumerate(temp):
                if output['transactionId'] == Input.transID.hex() and output['index'] == Input.index:
                    del Blockchain.unused_outputs_by_key[pubkey][i]
                    break

            Blockchain.unused_outputs[Input.transID].pop(Input.index)

        Blockchain.unused_outputs[self.ID] = {}
        for i, output in enumerate(self.outputs):
            Blockchain.unused_outputs[self.ID][i] = {"Publickey":output.publickey, "coins":output.amount}
       
            if output.publickey in Blockchain.unused_outputs_by_key:
                Blockchain.unused_outputs_by_key[output.publickey].append({"transactionId":self.ID.hex(), "index":i, "amount":str(output.amount)})
            else:
                Blockchain.unused_outputs_by_key[output.publickey] = [{"transactionId":self.ID.hex(), "index":i, "amount":str(output.amount)}]
            
        if self.num_inputs != 0:
            try:
                Blockchain.PendingTxns.remove(self)
            except:
                pass

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
        self.jsonList = []

    def get(self, my_peers, u_o):

        unused_outputs = copy.deepcopy(u_o)
        peer = random.choice(my_peers)
        r = requests.get(peer + '/getPendingTransactions')
        if r.status_code == 200:
            self.jsonList += r.json()

        index = 0
        while index < len(self.jsonList):
            Txn = Tx()
            Txn.TxnfromJson(self.jsonList[index])
            flag, unused_outputs = Txn.VerifyTxn(unused_outputs)
            if flag:
                self._list_.append(Txn)
                index += 1
                print('\nAdded a transaction to list of pending txns!')
            else:
                del self.jsonList[index]
                print('\n', Txn.inputs[0].transID.hex(), Txn.inputs[0].index)
                print('\nTransaction not Verified!')

    def sort(self, u_o):

        unused_outputs = copy.deepcopy(u_o)
        TxnFeesList = [Txn.getTxnFees(unused_outputs) for Txn in self._list_]
        self.sorted_list = sorted(zip(self._list_, TxnFeesList), key = itemgetter(1), reverse = True)

    def add(self, json, u_o):
        
        unused_outputs = copy.deepcopy(u_o)
        Txn = Tx()
        Txn.TxnfromJson(json)
        flag = Txn.VerifyTxn(unused_outputs)
        if flag:
            self.jsonList.append(json)
            self._list_.append(Txn)
            return True
        else:
            return False

    def remove(self, txn):

        for i, tx in enumerate(self._list_):
            if tx.ID == txn.ID:
                del self._list_[i]
                del self.jsonList[i]
                break


        


            





