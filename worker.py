#!/usr/bin/env python3

from block import block, Blockchain
import time
from Tx_classes import Tx, Output, PendingTxns
import copy


def Worker(Blockchain, queueflag):

    print('\nSTARTED WORKER THREAD!')

    PUBLICKEY = open('my_pk.pem', 'rb').read()

    while True:
        while not len(Blockchain.PendingTxns._list_) > 0:
            time.sleep(5)
            print('\nWaiting......')
            #Blockchain.PendingTxns.get(Blockchain.peers, Blockchain.unused_outputs)

        #Blockchain.PendingTxns.sort(Blockchain.unused_outputs)
        accumulator = bytes()
        BlockFees = 0
        num_txns = 1

        unused_outputs = copy.deepcopy(Blockchain.unused_outputs)
        flag = True
        for i, txn in enumerate(Blockchain.PendingTxns._list_):
            flag, unused_outputs = txn.VerifyTxn(unused_outputs)
            if flag:
                accumulator += (txn.size + txn._bytes_)
                if not len(accumulator) < 10 ** 6 - 520:
                    accumulator -= (txn.size + txn._bytes_)
                    break
                else:
                    BlockFees += txn.getTxnFees(Blockchain.unused_outputs)
                    num_txns += 1

        coinbase_output = Output(BlockFees + Blockchain.block_reward, PUBLICKEY)
        coinbase = Tx()
        coinbase.newTxn([], [coinbase_output])
        body = num_txns.to_bytes(4, 'big') + coinbase.size + coinbase._bytes_ + accumulator

        my_block = block()
        my_block.new(Blockchain, body)

        flag = my_block.mine(queueflag)
        if flag:
            Blockchain.addBlock(my_block)
        else:
            return False
