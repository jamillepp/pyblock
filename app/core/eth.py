from eth_account import Account
Account.enable_unaudited_hdwallet_features()

def create_wallet():
    acct = Account.create()
    return acct.address, acct.key.hex()
