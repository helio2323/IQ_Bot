from iqoptionapi.stable_api import IQ_Option
import configparser
from datetime import datetime
from pytz import timezone
import time
import pandas as pd

arq = configparser.RawConfigParser()
arq.read('config.txt')

email = arq.get('LOGIN', 'email')
senha = arq.get('LOGIN', 'senha')

ativo = 'EURUSD'

def fazerConexao(email, senha):
    API = IQ_Option(email, senha)

    API.connect()

    API.change_balance('PRACTICE') # PRACTICE / REAL

    conectado = False
    if API.check_connect() == True:
        print("Conectado com sucesso")
        conectado = True
    else:
        print("Erro ao conectar")
        conectado = False
    return API, conectado

def timestamp2dataHora(timestamp):
    data = datetime.fromtimestamp(timestamp, tz=timezone('America/Sao_Paulo'))
    return data
def infosContaIQ(api):
    conta = api.get_profile_ansyc()
    nome = conta['name']
    email = conta['email']
    moeda = conta['currency']
    saldo = conta['balance']
    data_criacao = timestamp2dataHora(conta['created'])
    return nome, email, moeda, saldo, data_criacao


API, conectado = fazerConexao(email, senha)

candles = API.get_candles(ativo, 60, 60, time.time())

df = pd.DataFrame(candles)

print(candles)

