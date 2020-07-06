# IITKBucks

Giving an argument 'queueflag' to the Worker Thread. The miner checks for an item in the queue every 100 nonces (just a flag). If there is one, mining stops and the function returns. The thread is joined when the server receives a new block. (more testing needed!!)
