#!/usr/bin/env python3

import requests
import random
from validation import ValidateTxn
from tx import Output, Input, Tx
from hashlib import sha256

def findPeers(genesis_url, my_url):
    my_peers = []
    potential_peers = []

    r = requests.post(genesis_url + '/newPeer', json = {"url":my_url})
    if r.status_code == 200:
        my_peers.append(genesis_url)
    r = requests.get(genesis_url + '/getPeers')
    potential_peers += r.json["peers"]

    while len(my_peers) < 5 and len(potential_peers) > 0:
        peer = potential_peers[0]
        r = requests.post(peer + '/newPeer', json = {"url":my_url})
        if r.status_code == 200:
            my_peers.append(peer)
        r = requests.get(peer + '/getPeers')
        for peer in r.json["peers"]:
            if peer not in potential_peers:
                potential_peers.append(peer)
        potential_peers.remove(peer)

    return my_peers

def getBlockchain(my_peers):

    block_num = 0
    r = requests.get(my_peers[0] + '/getBlock/0')
    unused_outputs = []
    unused_outputs = processBlock(r.content, unused_outputs)
    fh = open('blockchain/block' + str(block_num), 'wb')
    fh.write(r.content)
    fh.close()
    block_num += 1

    while r.status_code == 200:
        r = requests.get(my_peers[0] + '/getBlock/' + str(block_num))
        unused_outputs = processBlock(r.content, unused_outputs)
        fh = open('blockchain/block' + str(block_num), 'wb')
        fh.write(r.content)
        fh.close()
        block_num += 1

    return unused_outputs

def getPendingTxns(my_peers):

    peer = random.choice(my_peers)
    r = requests.get(peer + '/getPendingTransactions')

    return r.json

def processBlock(blockbytes, unused_outputs):

    num_txs = int.from_bytes(blockbytes[116:120], 'big')
    curr_index = 120
    with blockbytes as bb, curr_index as ci:
        txns = []
        for i in range(num_txns):
            size_txn = int.from_bytes(bb[ci:ci+4], 'big')
            ci += 4
            txnID = sha256(bb[ci:ci+size_txn]).digest()
            num_inputs = int.from_bytes(bb[ci:ci+4], 'big')
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
            num_outputs = int.from_bytes(bb[ci:ci+4], 'big')
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
                unused_outputs[txnID][i] = {"Publickey":pubkey, "coins":num_coins}

            flag, unused_outputs = ValidateTxn(Tx(num_inputs, inputs, num_outputs, outputs),
                                              unused_outputs)

    return unused_outputs

def init(genesis_url, my_url):

    my_peers = findPeers(genesis_url, my_url)
    unused_outputs = getBlockchain(my_peers)
    PendingTxns = getPendingTxns(my_peers)

    return my_peers, unused_outputs, PendingTxns


