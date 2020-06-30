#!/usr/bin/env python3

import requests
import random
from block import block

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

    genesis_block = block()
    genesis_block.from_bytes(r.content)
    flag, unused_outputs = genesis_block.Verify(unused_outputs)

    unused_outputs = genesis_block.process(unused_outputs)
    fh = open('blockchain/block' + str(block_num), 'wb')
    fh.write(r.content)
    fh.close()
    block_num += 1

    while r.status_code == 200:
        r = requests.get(my_peers[0] + '/getBlock/' + str(block_num))
        block = block()
        block.from_bytes(r.content)
        flag, unused_outputs = block.Verify(unused_outputs)
        unused_outputs = block.process(unused_outputs)
        fh = open('blockchain/block' + str(block_num), 'wb')
        fh.write(r.content)
        fh.close()
        block_num += 1

    return unused_outputs

def getPendingTxns(my_peers):

    peer = random.choice(my_peers)
    r = requests.get(peer + '/getPendingTransactions')

    return r.json

def init(genesis_url, my_url):

    my_peers = findPeers(genesis_url, my_url)
    unused_outputs = getBlockchain(my_peers)
    PendingTxns = getPendingTxns(my_peers)

    return my_peers, unused_outputs, PendingTxns


