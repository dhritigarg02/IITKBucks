#!/usr/bin/env python3

from Crypto.Signature import pss

def ValidateTxn(Txn, unused_outputs):

    flag = True
    total_input_coins = 0
    total_output_coins = 0
    temp_used_outputs = {}

    for Input in Txn.inputs:
        try:
            total_input_coins += unused_outputs[Input.transID][Input.index]["coins"]
        except:
            flag = False
            return flag
    for Output in Txn.outputs:
        total_output_coins += int.from_bytes(Output.amount, 'big')

    if total_output_coins > total_input_coins:
        flag = False
        return flag

    for Input in Txn.inputs:
        try:
            verifier = pss.new(unused_outputs[Input.transID][Input.index]["Publickey"])
            data = Input.transID + Input.index.to_bytes(4, 'big') + Txn.num_outputs.to_bytes(4, 'big') + Txn.output_bytes
            verifier.verify(data, Input.signature)

            temp_used_outputs[Input.transID][Input.index] = unused_outputs[Input.transID].pop[Input.index]
        except:
            for transId in temp_used_outputs:
                if transID in unused_outputs:
                    unused_outputs.update(temp_used_outputs[transID])
                else:
                    unused_outputs[transID] = temp_used_outputs[transID]

            flag = False
            return flag


