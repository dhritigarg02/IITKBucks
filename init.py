#!/usr/bin/env python3

import requests
import random
from block import block
import time
from tx import Coinbase, PendingTxns

def findPeers(main_url, my_url):
    my_peers = []
    potential_peers = []

    r = requests.post(main_url + '/newPeer', json = {"url":my_url})
    if r.status_code == 200:
        my_peers.append(main_url)
    r = requests.get(main_url + '/getPeers')
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
    peer = random.choice(my_peers)
    r = requests.get(peer + '/getBlock/0')

    genesis_block = block()
    genesis_block.from_bytes(r.content)
    Blockchain = Blockchain(my_peers)
    flag = Blockchain.addBlock(genesis_block)
    block_num += 1

    while r.status_code == 200 and flag:
        peer = random.choice(my_peers)
        r = requests.get(peer + '/getBlock/' + str(block_num))
        block = block()
        block.from_bytes(r.content)
        flag = Blockchain.addBlock(block)
        block_num += 1

    return Blockchain

def init(main_url, my_url):

    my_peers = findPeers(main_url, my_url)
    Blockchain = getBlockchain(my_peers)
    Blockchain.PendingTxns.get(my_peers)
    Blockchain.my_url = my_url

    return Blockchain

def Worker(Blockchain, queueflag):

    while True:
        while not len(Blockchain.PendingTxns._list_) > 0:
            time.sleep(1)

        Blockchain.PendingTxns.sort()
        accumulator = bytes()
        BlockFees = 0
        num_txns = 0
        for i, txn in enumerate(Blockchain.PendingTxns.sorted_list):
            if not len(accumulator) < 10 ** 6:
                num_txns = i + 1
                break
            accumulator += txn.size 
            accumulator += txn._bytes_
            BlockFees += txn.getTxnFees(Blockchain.unused_outputs)

        coinbase = Coinbase()
        coinbase.new(BlockFees)
        body = num_txns.to_bytes(4, 'big') + coinbase.size + coinbase._bytes_ + accumulator

        my_block = block()
        my_block.new(Blockchain.current_index, Blockchain.target, body)

        flag = my_block.mine(queueflag)
        if flag:
            flag = Blockchain.addBlock(my_block)
            post_new_block(my_block)
        else:
            return False

def post_new_block(block):

    print(block.header)





    



