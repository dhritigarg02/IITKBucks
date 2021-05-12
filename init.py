#!/usr/bin/env python3

import requests
import random
from block import block, Blockchain
from Tx_classes import Tx, Output, PendingTxns

def findPeers(main_url, my_url):
    my_peers = []
    potential_peers = []
    tried_peers = []

    r = requests.post(main_url + '/newPeer', json = {"url":my_url})
    if r.status_code == 200:
        my_peers.append(main_url)
    r = requests.get(main_url + '/getPeers')
    if r.status_code == 200:
        potential_peers += r.json()["peers"]

    while len(my_peers) <= 5 and len(potential_peers) > 0:
        peer = potential_peers[0]
        r = requests.post(peer + '/newPeer', json = {"url":my_url})
        if r.status_code == 200:
            my_peers.append(peer)
        else:
            tried_peers.append(potential_peers[0])
        r = requests.get(peer + '/getPeers')
        if r.status_code == 200:
            for peer in r.json()["peers"]:
                if (peer not in potential_peers) and (peer not in tried_peers) and (peer not in my_peers):
                    potential_peers.append(peer)
        del potential_peers[0]

    print(my_peers)

    return my_peers

def getBlockchain(my_peers):

    block_num = 0
    peer = 'https://iitkbucks.pclub.in'
    r = requests.get(peer + '/getBlock/0')
    #print(r.content)
    #block0 = open('block0', 'rb').read()
    genesis_block = block()
    genesis_block.from_bytes(r.content)
    #genesis_block.from_bytes(block0)
    my_Blockchain = Blockchain(my_peers)
    my_Blockchain.block_reward = genesis_block.transactions[0].outputs[0].amount
    flag = my_Blockchain.addBlock(genesis_block)
    block_num += 1
    flag = True
    
    while flag:
        #peer = random.choice(my_peers)
        r = requests.get(peer + '/getBlock/' + str(block_num))
        if r.status_code == 200:
            nblock = block()
            nblock.from_bytes(r.content)
            flag = my_Blockchain.addBlock(nblock) 
            if flag == 0: flag = True
            block_num += 1
        else:
            flag = False
    
    return my_Blockchain

def init(main_url, my_url):

    my_peers = findPeers(main_url, my_url)
    #my_peers = [main_url]
    Blockchain = getBlockchain(my_peers)
    Blockchain.PendingTxns.get(my_peers, Blockchain.unused_outputs)
    Blockchain.my_url = my_url

    return Blockchain


    



