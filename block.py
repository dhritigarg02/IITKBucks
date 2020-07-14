#!/usr/bin/env python3

import hashlib
import time
from hashlib import sha256
from tx import Output, Input, Tx, PendingTxns
import requests

class block:

    def new(self, index, target, body):

        self.index = index
        fh = open('blockchain/block' + str(index-1) , 'rb')
        self.parent_hash = sha256(fh.read(116)).digest()
        self.target = target
        self.body = body
        self.body_hash = sha256(self.body).digest()
        self.parsebody()

    def from_bytes(self, bb):
        # bb stands for blockbytes, ci for curret_index
        ci = 0
        self.index = int.from_bytes(bb[ci:ci+4], 'big')
        ci += 4
        self.parent_hash = bb[ci:ci+32]
        ci += 32
        self.body_hash = bb[ci:ci+32]
        ci += 32
        self.target = bb[ci:ci+32]
        ci += 32
        self.timestamp = int.from_bytes(bb[ci:ci+8], 'big')
        ci += 8
        self.nonce = int.from_bytes(bb[ci:ci+8], 'big')
        ci += 8
        self.body = bb[ci:]
        self.parsebody()
        self.hash = sha256(bb[0:116]).digest()
        self.header = bb[0:116]

    def parsebody(self):
        
        ci = 0
        bb = self.body
        self.num_txns = int.from_bytes(bb[ci:ci+4], 'big')
        ci += 4
        txns = []
        for i in range(self.num_txns):
            size_txn = int.from_bytes(bb[ci:ci+4], 'big')
            ci += 4
            Transaction = Tx()
            Transaction.TxnfromBytes(bb[ci:ci+size_txn])
            ci += size_txn

            txns.append(Transaction)
        self.transactions = txns

    def mine(self, queueflag):

        max_nonce = 10000000000000
        self.header = index.to_bytes(4, 'big') + self.parent_hash + self.body_hash + self.target.to_bytes(32, 'big')

        h = sha256()
        h.update(self.header)
        start_time = time.time()
        for nonce in range(max_nonce):

            h_copy = h.copy()
            if nonce % 100 == 0:
                try:
                    queueflag.get_nowait()
                    return False
                except:
                    pass
            timestamp = time.time_ns()
            h_copy.update(timestamp.to_bytes(8, 'big') + nonce.to_bytes(8, 'big'))

            if int.from_bytes(h_copy.digest(), 'big') < self.target:

                time_taken = time.time() - start_time
                self.header = self.header + timestamp.to_bytes(8, 'big') + nonce.to_bytes(8, 'big')
                self.hash = h_copy.hexdigest()
                self.timestamp = timestamp
                self.nonce = nonce
                print('Time taken to find nonce: ',int(time_taken/60),'m',int(time_taken%60), 's')
                return True
        

    def Verify(self, Blockchain):

        def get_prev_hash(index):
            if index == -1:
                return bytes.fromhex('0'*64)
            hash = Blockchain.chain[index].hash
            return hash

        if not bytearray(self.parent_hash) == bytearray(get_prev_hash(self.index-1)):
            print('wrong hash!')
            return False
        if not int.from_bytes(self.hash, 'big') < int.from_bytes(self.target, 'big') :
            print('target not reached!')
            return False
        if not bytearray(sha256(self.body).digest()) == bytearray(self.body_hash):
            print('body hash wrong')
            return False
        
        unused_outputs = Blockchain.unused_outputs
        for i, txn in enumerate(self.transactions):
            if i == 0:
                self.Total_fees = self.getTotalBlockFees(unused_outputs)
                #print(Blockchain.block_reward, self.Total_fees)
                #print(txn.outputs[0].amount)
                if not txn.outputs[0].amount == Blockchain.block_reward + self.Total_fees:
                    return False
            else:
                flag, unused_outputs = txn.VerifyTxn(unused_outputs)
                if not flag:
                    return False
    
        return True

    def process(self, Blockchain):
        
        for txn in self.transactions:
            txn.processTxn(Blockchain)
        fh = open('blockchain/block' + str(Blockchain.current_index), 'wb')
        fh.write(self.header + self.body)
        fh.close()

    def getTotalBlockFees(self, unused_outputs):

        Total_fees = 0
        for txn in self.transactions[1:]:
            txnFees = txn.getTxnFees(unused_outputs)
            Total_fees += txnFees

        return Total_fees

class Blockchain:

    def __init__(self, my_peers):

        self.chain = []
        self.current_index = 0
        self.unused_outputs = {}
        self.PendingTxns = PendingTxns()
        self.peers = my_peers
        self.target = int.from_bytes(bytes.fromhex('0'*5+'f'+'0'*58), 'big')
        self.alias_map = {}
        self.unused_outputs_by_key = {}
        self.block_reward = None

    def addBlock(self, block):

        flag = block.Verify(self)
        #print(flag)

        if flag:
            block.process(self)
            self.chain.append(block)

            fh = open('blockchain/block' + str(self.current_index), 'wb')
            fh.write(block.header + block.body)
            fh.close()
            #print(self.current_index)
            self.current_index += 1
            for peer in self.peers:
                r = requests.post(peer + '/newBlock', 
                        data = block.header + block.body, 
                        headers = {'Content-Type' : 'application/octet-stream'})

            return True
        else:
            return False

























