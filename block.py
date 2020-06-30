#!/usr/bin/env python3

import hashlib
import time
from hashlib import sha256

class block:

    def new(self, index, parent_hash, target, body):

        self.index = index
        self.parent_hash = parent_hash
        self.target = target
        self.body = body
        self.body_hash = sha256(self.body).digest()
        parsebody(self)

    def from_bytes(self, blockbytes):
        
        curr_index = 0
        with blockbytes as bb, curr_index as ci:
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
            parsebody(self)
            self.hash = sha256(bb[0:116]).digest()

    def parsebody(self):
        
        ci = 0
        with self.body as bb:
            self.num_txns = int.from_bytes(bb[ci:ci+4], 'big')
            ci += 4
            txns = []
            for i in range(num_txns):
                size_txn = int.from_bytes(bb[ci:ci+4], 'big')
                ci += 4
                if i == 0:
                    Transaction = Coinbase()
                    Transaction.fromBytes(bb[ci:ci+size_txn])
                else:
                    Transaction = Tx()
                    Transaction.TxnfromBytes(bb[ci:ci+size_txn])
                ci += size_txn

                txns.append(Transaction)
            self.transactions = txns

    def mine(self, max_nonce):

        max_nonce = 100000000000
        self.header = index.to_bytes(4, 'big') + self.parent_hash + self.body_hash + self.target.to_bytes(32, 'big')

        h = sha256()
        h.update(self.header)
        start_time = time.time()
        for nonce in range(max_nonce):

            h_copy = h.copy()
            timestamp = time.time_ns()
            h_copy.update(timestamp.to_bytes(8, 'big') + nonce.to_bytes(8, 'big'))

            if int.from_bytes(h_copy.digest(), 'big') < self.target:

                #time_taken = time.time() - start_time
                self.header = self.header + timestamp.to_bytes(8, 'big') + nonce.to_bytes(8, 'big')
                self.hash = h_copy.hexdigest()
                self.timestamp = timestamp
                self.nonce = nonce
                #print('Time taken to find nonce: ',int(time_taken/60),'m',int(time_taken%60), 's')
                break

    def Verify(self, unused_outputs):

        def get_prev_hash(index):
            if index == -1:
                return bytes.fromhex('0'*64)
            block = open('blockchain/block' + str(index), 'rb').read()
            return sha256(block[0:116]).digest()

        if not bytearray(self.parent_hash) == bytearray(get_prev_hash(self.index-1)):
            return False
        if not int.from_bytes(self.hash, 'big') < self.target :
            return False
        if not bytearray(sha256(self.body).digest()) == bytearray(self.body_hash):
            return False

        for i, txn in enumerate(self.transactions):
            if i == 0:
                pass
            else:
                flag, unused_outputs = txn.ValidateTxn(unused_outputs)
                if flag == False:
                    return flag
        return True, unused_outputs

    def process(self, unused_outputs):

        for i, output in enumerate(txn.outputs):
            unused_outputs[txn.ID][i] = {"Publickey":self.publickey, "coins":self.amount}

        return unused_outputs



















