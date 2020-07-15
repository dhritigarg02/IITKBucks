#!/usr/bin/env python3

from PyInquirer import prompt
from PyInquirer import Validator, ValidationError
from Crypto.PublicKey import RSA
import requests
from build import BuildTxn

print('\nWelcome to the IITKBucks user interface!\n')

def options(answers):
    if answers['action'] == 0:
        addAlias()
    elif answers['action'] == 1:
        key_generation()
    elif answers['action'] == 2:
        getBalance()
    elif answers['action'] == 3:
        Transfer()
    else:
        print('\nThank you!\n')
        quit()

class KeyPathValidator(Validator):
    def validate(self, document):
        try:
            fh = open(document.text)
        except:
            raise ValidationError(message = 'Please enter a valid path!',
                    cursor_position=len(document.text))

class NumberValidator(Validator):
    def validate(self, document):
        try:
            int(document(text))
        except:
            raise ValidationError(message = 'Please enter a number!',
                    cursor_position=len(document.text))

def Alias_or_pubKey():

    _questions_ = [{
                'type' : 'list',
                'name' : 'IDtype',
                'message' : 'Please select the ID type you would like to input:',
                'choices' : ['Alias', 'Public Key']}]
    alias = [{
                'type' : 'input',
                'name' : 'alias',
                'message' : 'Please enter an alias:'}]
    publickey = [{
                'type' : 'input',
                'name' : 'pubkey',
                'message' : 'Please enter path to the public key file:',
                'validate' : KeyPathValidator}]

    answers = prompt(_questions_)

    if answers['IDtype'] == 'Public Key':
        answer = prompt(publickey)
        return {'pubkey': answer['pubkey'], 'alias': None}
    else:
        answer = prompt(alias)
        return {'pubkey' : None, 'alias' : answer['alias']}
        

def addAlias():    
    
    _questions_ = [
            {
                'type' : 'input',
                'name' : 'alias',
                'message' : 'Please enter an alias:'},
            {
                'type' : 'input',
                'name' : 'publickey',
                'message' : 'Please enter path to the public key file:',
                'validate' : KeyPathValidator}
            ]

    answers = prompt(_questions_)

    publickey = open(answers['publickey'], 'rb').read()
    data = {
            'alias':answers['alias'], 
            'publickey':publickey
            }
    r = requests.post(MY_URL+'/addAlias', json = data)

    print('\n' + r.text + '\n')
    answers = prompt(questions)
    options(answers)

def key_generation():
    key_pair = RSA.generate(2048)

    private_key = key_pair.exportKey("PEM")
    public_key = key_pair.publickey().exportKey("PEM")

    sk = open("private.pem", "wb")
    sk.write(private_key)
    sk.close()

    pk = open("public.pem", "wb")
    pk.write(public_key)
    pk.close()

    print('\nExported keys as \'private.pem\' and \'public.pem\'\n')
    answers = prompt(questions)
    options(answers)

def getBalance():

    answer = Alias_or_pubKey()

    if answer['pubkey'] != None:
        pubkey = open(answer['pubkey'], 'rb').read()
        data = {'publicKey': pubkey}
        r = requests.post(MY_URL+'/getUnusedOutputs', json = data)

    else:
        r = requests.post(MY_URL+'/getUnusedOutputs', json = answer)

    if r.status_code == 200:
        response = r.json()
        balance = 0
        for output in response["unusedOutputs"]:
            balance += output["amount"]
        print("\nYour account balance is:", balance)
    else:
        print('\n' + r.text + '\n')

    answers = prompt(_questions_)
    options(answers)

def Transfer():

    Txn = {}

    keys = [
            {
                'type' : 'input',
                'name' : 'pubkey',
                'message' : 'Please enter path to your public key file:',
                'validate' : KeyPathValidator},
            {
                'type' : 'input',
                'name' : 'privkey',
                'message' : 'Please enter path to your private key file:',
                'validate' : KeyPathValidator}
            ]
    num_outputs = [
            {
                'type' : 'input',
                'name' : 'num_outputs',
                'message' : 'Please enter the number of outputs:',
                'validate' : NumberValidator}
            ]
    amount = [
            {
                'type' : 'input',
                'name' : 'amount',
                'message' : 'Please enter the amount of coins to be transferred to this recipient:',
                'validate' : NumberValidator}
            ]
    txnfees = [
            {
                'type': 'input',
                'name': 'txnfees',
                'message' : 'Please enter the transaction fee you would like to leave:',
                'validate' : NumberValidator}
            ]

    keys = prompt(keys)
    Txn['keys'] = keys
    pubkey = open(keys['pubkey'], 'rb').read()
    json = {'publicKey': pubkey}
    r = requests.post(MY_URL+'/getUnusedOutputs', json = json)
    if r.status_code == 200:
        Txn['unused_outputs'] = r.json()['unusedOutputs']
        balance = 0
        for output in Txn['unused_outputs']:
            balance += output['amount']
        Txn['balance'] = balance
        print("\nYour account balance is:", balance, '\n')

        answer = prompt(num_outputs)
        outputs = []
        total_amount = 0

        for i in range(answer['num_outputs']):

            print('\nData for Output', i+1)
            print('For recipient:')
            outputs.append({})
            answer = Alias_or_pubKey()
            if answer['alias'] != None:
                r = requests.post(MY_URL + '/getPublicKey', json = answer)
                if r.status_code == 200:
                    data = r.json()
                    outputs[i]['publicKey'] = data['publicKey']
                else:
                    raise ValidationError(message = r.text,
                            cursor_position=len(document.text))
            else:
                pubkey = open(answer['pubkey'], 'rb').read()
                outputs[i]['publicKey'] = pubkey

            answer = prompt(amount)
            total_amount += answer['amount']
            outputs[i]['amount'] = answer['amount']
            print('\n')
        
        Txn['outputs'] = outputs
        answer = prompt(txnfees)
        total_amount += answer['txnfees']
        Txn['txnfees'] = txnfees
        Txn['total_amount'] = total_amount

        if total_amount > balance:
            print('Total amount required for this transaction exceeds account balance!!')
            quit()
        else:
            Transaction = BuildTxn(Txn)
            json_txn = Transaction.toJson()
            r = requests.post(MY_URL + 'newTransaction', json = json_txn)
            print('\nCreated transaction successfully!\n')

    else:
        print('\n' + r.text + '\n')

    answers = prompt(_questions_)
    options(answers)


questions = [
        {
            'type' : 'list',
            'name' : 'action',
            'message' : 'What action would you like to perform?',
            'choices' : [
                {
                    "name" : 'Add an alias',
                    "value" : 0 },
                {
                    "name" : 'Generate a public-private key pair',
                    "value" : 1},
                {
                    "name" : 'Check balance for an account',
                    "value" : 2},
                {
                    "name" : 'Transfer bucks',
                    "value" : 3},
                {
                    "name" : 'Quit',
                    "value" : 4}
                ]
            }
        ]

answers = prompt(questions)
options(answers)


 

