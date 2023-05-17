from iqoptionapi.stable_api import IQ_Option
import configparser
from datetime import datetime
from pytz import timezone
import time
import pandas as pd
import sys

arq = configparser.RawConfigParser()
arq.read('config.txt')

email = arq.get('LOGIN', 'email')
senha = arq.get('LOGIN', 'senha')

ativo = 'EURUSD'

def direcional_MHI(cores):
    direcao = ''
    
    if cores.count('A') > cores.count('B') and cores.count('D')==0:
        direcao = 'put'
    
    if cores.count('B') > cores.count('A') and cores.count('D')==0:
        direcao = 'call'
    return direcao

def stoploss(lucro, gain, loss):
    if lucro <= loss:
        print('Atenção: Infelizmente atingimos o Stop Loss !')
        sys.exit()
    if lucro >= gain:
        print('Parabéns: você bateu a meta do dia - Stop Gain!')    
        sys.exit()

def Martingale(entrada, payout):
    aposta = entrada * (1+payout)/payout
    return aposta

def payout(par, tipo, API, timeframe = 1):
    if tipo == 'turbo':
        a = API.get_all_profit()
        return int(100 * a[par]['turbo'])
    elif tipo == 'digital':
        API.subscribe_strike_list(par, timeframe)
        while True:
            d = API.get_digital_current_profit(par, timeframe)
            if d != False:
                d = int(d)
                break
        API.unsubscribe_strike_list(par, timeframe)
        return d        


def coletaAtivos():
    ID = dict({(cd, at) for at,cd in API.get_all_ACTIVES_OPCODE().items()})
    return ID

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

def coletacandles(cadamil, API):
        
    tempo = time.time()
    candles = []
    for _ in range(cadamil):
        c = API.get_candles(ativo, 60, 2000, tempo)
        candles = c + candles
        tempo = c[0]['from'] - 1

    df = pd.DataFrame(candles)
    
    df['from'] = pd.to_datetime(df['from'], unit='s')
    df['to'] = pd.to_datetime(df['from'], unit='s')
    
    return df 

if __name__ == "__main__":
        # Código a ser executado somente quando o módulo é executado diretamente
        # Pode estar vazio ou conter código de teste ou exemplo

    API, conectado = fazerConexao(email, senha)

    ativos = API.get_all_open_time()

    for a in ativos['turbo']:
        if ativos['turbo'][a]['open'] == True:
            print('[ TURBO ]:'+a+' | Payout: '+str(payout(a, 'turbo', API))+'%')

    novos_candles = coletacandles(1, API)

    API.start_candles_stream(ativo, 60, 1)

    print(coletaAtivos())

    #print(payout(ativo, 'turbo', API))

    #executa ordem na corretora

    ativo = 'EURUSD-OTC'
    lotes = 2
    direcao = 'call'
    timeframe = 1

    status, ID =  API.buy(lotes,ativo,direcao,timeframe)

    #avaliando as horas


    espera_seg = 10

    conts = 1
    contm = 0

    def coletaCores3ultimasVelasM1(ativo, API):
        ativo = 'EURUSD-OTC'
        velas = API.get_candles(ativo, 60, 3, time.time())
        
        velas[0] = 'A' if velas[0]['open'] > velas[0]['close'] else 'B' if velas[0]['open'] == velas[0]['close'] else 'D'
        velas[1] = 'A' if velas[1]['open'] > velas[1]['close'] else 'B' if velas[1]['open'] == velas[1]['close'] else 'D'
        velas[2] = 'A' if velas[2]['open'] > velas[2]['close'] else 'B' if velas[2]['open'] == velas[2]['close'] else 'D'
        
        cores = velas[0] + ' ' + velas[1] + ' ' + velas[2]
        
        return cores

    print(coletaCores3ultimasVelasM1('EURUSD-OTC', API))

    
    

    while True:
        d = datetime.now(tz=timezone('America/Sao_Paulo'))
        print(d)

        minutos = d.minute
        horas = d.hour
        segundos = d.second

        if segundos == 0:
            contm += 1
            print('Temos um novo minuto')

        if conts == espera_seg:
            print('Aguardando '+str(espera_seg)+' segundos')
            conts = 0

        if contm == 5:
            print('Avaliar a estratégia MHI')
            contm = 0

        time.sleep(1)
        conts += 1