# -*- coding: utf-8 -*-
"""

@author: rafaelfvcs
Canal YouTube - Analistas Quant - https://bit.ly/CanalYouTube-Analistas-Quant

===== >>>   AULA 13 - PROJETO FINAL CURSO: Robô MHI (apenas para uso didático)

https://lu-yi-hsun.github.io/iqoptionapi_private/
"""

from iqoptionapi.stable_api import IQ_Option
import configparser
from datetime import datetime
import time
from pytz import timezone
import sys

arq = configparser.RawConfigParser()
arq.read('config.txt')

email = arq.get('LOGIN','email')
senha = arq.get('LOGIN','senha')

def fazerConexao(email,senha,tipoConta = 'PRACTICE'):
    API = IQ_Option(email,senha)

    API.connect()
    
    API.change_balance(tipoConta)  # REAL
    
    conectado = False
    if API.check_connect()==True:
        print("Ok a conexão foi estabelecida!")
        conectado = True
    else:
        print("Tivemos problemas na conexão!")
        conectado = False
    return API, conectado

def timestamp2dataHora(x, timezone_='America/Sao_Paulo'):
    d = datetime.fromtimestamp(x,tz=timezone(timezone_))
    return str(d)

def infosContaIQ(api):
    conta = api.get_profile_ansyc()
    nome = conta['name']
    moeda = conta['currency']
    data_criacao = timestamp2dataHora(conta['created'])
    return conta, nome, moeda, data_criacao

def coleta2000Candles(ativo, API):
    tempo = time.time()
    candles = []
    for _ in range(2):
        c = API.get_candles(ativo,60,1000,tempo)
        candles = c + candles
        tempo = c[0]['from']-1
    return candles 


def payout(par, tipo,  API, timeframe = 1):
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
			time.sleep(1)
		API.unsubscribe_strike_list(par, timeframe)
		return d
def estrategiaR7(ativo, API):
    velas = API.get_candles(ativo, 60, 1, time.time())
    velas[0] = 'A' if velas[0]['open'] < velas[0]['close'] else 'B' if velas[0]['open'] > velas[0]['close'] else 'D'
    cores = velas[0]
    if cores == 'A':
        cores = 'call'
    if cores == 'B':
        cores = 'put'    
    return cores

def coletaCores3ultimasVelasM1(ativo, API):
    # A - Alta, B - Baixa, D - Doji
    velas = API.get_candles(ativo, 60, 3, time.time())     
    velas[0] = 'A' if velas[0]['open'] < velas[0]['close'] else 'B' if velas[0]['open'] > velas[0]['close'] else 'D'
    velas[1] = 'A' if velas[1]['open'] < velas[1]['close'] else 'B' if velas[1]['open'] > velas[1]['close'] else 'D'
    velas[2] = 'A' if velas[2]['open'] < velas[2]['close'] else 'B' if velas[2]['open'] > velas[2]['close'] else 'D'
    cores = velas[0] + ' ' + velas[1] + ' ' + velas[2]   
    return cores

def coletaCoresultimaVelasM1(ativo, API):
    # A - Alta, B - Baixa, D - Doji
    velas = API.get_candles(ativo, 60, 1, time.time())     
    velas[0] = 'A' if velas[0]['open'] < velas[0]['close'] else 'B' if velas[0]['open'] > velas[0]['close'] else 'D'
    cores = velas[0]
    return cores

def direcional_MHI(cores):
    direcao = ''
    
    if cores.count('A') > cores.count('B') and cores.count('D')==0:
        direcao = 'put'
    
    if cores.count('B') > cores.count('A') and cores.count('D')==0:
        direcao = 'call'
    return direcao

def stop(lucro, gain, loss):
    if lucro <= -loss:
        print('Atenção: Infelizmente atingimos o Stop Loss !')
        sys.exit() 
    if lucro >= gain:
        print('Atenção: Parabéns você bateu a meta do dia - Stop Gain!')
        sys.exit()

def Martingale(entrada, payout):
    # payout precisa está em percentual: ex 0.9
    aposta = entrada * (1+payout)/payout
    return aposta


API, conectado = fazerConexao(email,senha)


ativo = 'EURUSD'
payout = payout(ativo,'digital',API)


stop_gain = 1000 # Ganho total diário
stop_loss = 1000 # Perda total diário
valor_entrada_b = 100  # Valor das entradas nos trades
martingale = 2       # Quantidade de Martingales 
delay      = 2       # Atraso para entrada nos trades

#----------------------------------------------------------------------
lucro = 0
cont = 0    # Variável para contar o número de candles
total_trades = 0
n_espera = 5 # dicionario que coleta a qtd de candle de epera para os ciclos
novoCandle = False

#contagem de acertos
ttWins = 0
ttLoss = 0
velaAtual = 0

while True:
    
    d = datetime.now()
    minutos = d.minute
    segundos = d.second
    
    entrar = False
    #entrar = False #(minutos >= 3.58 and minutos <= 4) or (minutos >= 7.58 and minutos <= 8) or (minutos >= 0.58 and minutos <= 1)
    
    
    novoCandle = (segundos == (60-delay))  # atenção iremos ter uma ativação de 2 em 2 por novo candle
    
    if(novoCandle): 
        cont += 1
        

    print(ativo,', NewBar? - ', novoCandle, " - Num Bar = ", cont, ", Seg = ", segundos, ", Trade = ",total_trades)
    #entrada = True 
    
    if( cont == n_espera ): # ATENÇÃO: Para avaliar nova vela!!!
        entrar = True
        cont = 0
    
    if entrar:
        print('\n\n ATENÇÃO: Robô vai efetuas trade!')
        
        print(':::: Verificando as cores dos candles: ', end='')
        
        velas = API.get_candles(ativo, 60, 3, time.time())
             
        cores = coletaCores3ultimasVelasM1(ativo, API)
       
        direcao = direcional_MHI(cores)

        if direcao == 'call':
            direcaoEntrada = 'A'
        else:
            direcaoEntrada = 'B'     
        
        if direcao =='':
            print('Não vamos operar... Cores indefinidas: ', cores)
            entrar = False
        else:
            print(":: As cores das três útlimas velas foram: ", cores)
        
        if (direcao=='call' or direcao == 'put'):
            
            print('Direção da aposta:',direcao)
            
            valor_entrada = valor_entrada_b
      
            while True:
                
                d = datetime.now()
                minutos = d.minute
                segundos = d.second
                
                print(ativo,', NewBar? - ', novoCandle, " - Num Bar = ", cont, ", Seg = ", segundos, ", Trade = ",total_trades)
                
                if segundos == 58:
                
                    status,id_ = API.buy(valor_entrada, ativo, direcao, 1)
                    cont += 1
                    print('Estamos posicionados numa '+direcao)
                    total_trades += 1

                    break

                time.sleep(1)
                    
            contador = 1
            if status:
                while True:
                    d = datetime.now()
                    minutos = d.minute
                    segundos = d.second
                    checkcor = coletaCoresultimaVelasM1(ativo, API)

                    if direcaoEntrada ==  checkcor:
                        print('Estamos VENCENDO a operação, mas precisamos aguardar o fim da vela')
                        print(f'direção: ' + direcao + ' cor da vela: ' + checkcor)
                        print(f'Aguardando término da operação: {str(contador)} segundos')
                        print('----------------------------------------------------------------------------------')
                    else:
                        print('Estamos PERDENDO a operação, mas precisamos aguardar o fim da vela')
                        print(f'direção: ' + direcao + ' cor da vela: ' + checkcor)
                        print(f'Aguardando término da operação: {str(contador)} segundos')
                        print('----------------------------------------------------------------------------------')                                
                    
                    if(contador == 45):
                        print('A operação está quase terminando, vamos aguardar o resultado...')
                        status,valor = API.check_win_v4(id_)
                        print('Estamos checando o resultado da operação: ', status)
                    
                    if status == 'win':
                        cont = 0
                        break
                    if status == 'loose':
                        print('Perdemos a operação, vamos preparar o Martingale')
                        contador = 1
                        status,id_ = API.buy(valor_entrada, ativo, direcao, 1)
                        
                    time.sleep(1)
                    contador += 1
                    cont = 0      

                                
            else:
                print('\nERRO AO REALIZAR OPERAÇÃO\n\n')
    
    
    time.sleep(1)

