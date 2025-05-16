import streamlit as st
from datetime import datetime
import pedala_teste_2
from openai import OpenAI
import os
import json
import re
import html
import streamlit.components.v1 as components
import pandas as pd
import base64
import random
from utils.openai_helper import analyze_cycling_conditions
from utils.echarts_helper import (
    generate_historical_chart,
    generate_prediction_chart,
    generate_route_elevation_chart
)
from utils.new_gauge_chart import generate_improved_gauge_chart
from pdf_generator import gerar_pdf_roteiro

# Função para inicializar ou reiniciar o estado da aplicação
def inicializar_sessao(reiniciar=False):
    """
    Inicializa ou reinicia o estado da sessão do Streamlit
    
    Args:
        reiniciar (bool): Se True, limpa todos os dados existentes antes de inicializar
    """
    if reiniciar:
        # Lista de chaves que queremos manter mesmo após reinício
        keep_keys = ['sensor_data_history']
        
        # Salvar temporariamente os valores das chaves que queremos manter
        temp_values = {}
        for key in keep_keys:
            if key in st.session_state:
                temp_values[key] = st.session_state[key]
        
        # Limpar todas as chaves
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Restaurar as chaves que queremos manter
        for key, value in temp_values.items():
            st.session_state[key] = value
    
    # Inicializar valores padrão
    if 'page' not in st.session_state:
        st.session_state.page = 'form'
    if 'data' not in st.session_state:
        st.session_state.data = {}
    if 'sensor_data_history' not in st.session_state:
        st.session_state.sensor_data_history = []
    if 'app_reiniciado' not in st.session_state:
        st.session_state.app_reiniciado = False

# Inicializar estado da aplicação na primeira execução
inicializar_sessao()

# Configura API keys
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
GMAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

# Verificar se temos chave do Google Maps
has_gmaps = GMAPS_KEY is not None and GMAPS_KEY.strip() != ""
if has_gmaps:
    import googlemaps
    gmaps = googlemaps.Client(key=GMAPS_KEY)

# Configuração da página
st.set_page_config(
    page_title="🚲 Pedala SJC",
    page_icon="🚴",
    layout="wide"
)

# CSS para estilizar os cards de sensores
st.markdown("""
<style>
  body { background-color: #121212; color: #f0f0f0; font-family: inherit; }
  .stTextInput input, .stSelectbox div[data-baseweb="select"] div,
  .stSlider [data-baseweb="slider"] {
    background-color: #333 !important; color: #f0f0f0 !important;
    border-radius: 8px !important; height: 3em !important; line-height: 3em !important;
  }
  .stSlider [data-baseweb="slider"] { padding: 0.5em !important; }
  .stButton button {
    background-color: #3498db; color: white; border-radius: 8px;
    font-weight: bold; height: 3em; transition: all 0.3s;
  }
  .stButton button:hover {
    background-color: #2980b9; transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
  }
  .sensor-card {
    background: white; color: black; text-align: center;
    padding: 1.2rem; border-radius: 8px; margin: 0.25rem;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
    height: 145px; /* Altura fixa para todos os sensores */
    width: 100%; /* Largura consistente */
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  .sensor-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0,0,0,0.3);
  }
  .sensor-icon { 
    font-size: 2.5rem; 
    margin-top: 0.5rem;
    display: block;
  }
  .charts-container {
    background-color: #1e2a38;
    border-radius: 12px;
    padding: 1rem;
    margin-top: 1rem;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
  }
  .hanna-illustration {
    border-radius: 12px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    margin: 1rem 0;
    transition: transform 0.3s ease;
  }
  .hanna-illustration:hover {
    transform: scale(1.02);
  }
  .pdf-link {
    display: inline-block;
    background-color: #3498db;
    color: white;
    padding: 10px 15px;
    text-align: center;
    text-decoration: none;
    font-size: 16px;
    border-radius: 8px;
    cursor: pointer;
    margin-top: 10px;
    transition: background-color 0.3s, transform 0.3s;
  }
  .pdf-link:hover {
    background-color: #2980b9;
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
  }
  .action-button-primary {
    background-color: #3498db !important; 
  }
  .action-button-secondary {
    background-color: #2ecc71 !important;
  }
</style>
""", unsafe_allow_html=True)

# Funções auxiliares

def traduzir_com_openai(texto_original):
    """
    Traduz um texto do inglês para português usando OpenAI
    
    Args:
        texto_original (str): Texto em inglês a ser traduzido
        
    Returns:
        str: Texto traduzido para português
    """
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    # do not change this unless explicitly requested by the user
    try:
        # Pré-processamento: corrigir erros comuns antes da tradução
        texto_corrigido = texto_original
        texto_corrigido = texto_corrigido.replace("Contemue", "Continue")
        texto_corrigido = texto_corrigido.replace("seguemdo", "seguindo")
        texto_corrigido = texto_corrigido.replace("Destemo", "Destination")
        texto_corrigido = texto_corrigido.replace("sulleste", "southeast")
        texto_corrigido = texto_corrigido.replace("norteleste", "northeast")
        
        # Criar prompt melhorado para tradução
        prompt = f"""Traduza as instruções de navegação abaixo do inglês para português brasileiro formal.
Mantenha nomes próprios de ruas/locais como estão.
Formate corretamente as direções (norte, sul, leste, oeste) em português.

Os termos específicos para traduzir consistentemente são:
- "Head" → "Siga"
- "Turn right" → "Vire à direita" 
- "Turn left" → "Vire à esquerda"
- "Continue onto" → "Continue pela"
- "Continue to follow" → "Continue seguindo pela"
- "northeast/southeast/etc" → "nordeste/sudeste/etc"
- "Walk your bicycle" → "Desça da bicicleta"
- "toward" → "em direção a"
- "Pass by" → "Passe por"
- "on the right" → "à direita"
- "on the left" → "à esquerda"
- "Restricted usage road" → "Estrada de uso restrito"
- "Destination will be" → "O destino estará"
- "Slight right/left" → "Vire levemente à direita/esquerda"

Texto para traduzir:
{texto_corrigido}

Retorne APENAS a tradução limpa, sem comentários.
"""
        
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        # Obter tradução
        traducao = resp.choices[0].message.content.strip()
        return traducao
    except Exception as e:
        print(f"Erro na tradução: {str(e)}")
        # Se falhar, usar sistema de substituições mais abrangente
        texto_pt = texto_original
        
        # Correções de erros comuns
        texto_pt = texto_pt.replace("Contemue", "Continue")
        texto_pt = texto_pt.replace("seguemdo", "seguindo")
        texto_pt = texto_pt.replace("Destemo", "Destino")
        texto_pt = texto_pt.replace("sulleste", "sudeste")
        texto_pt = texto_pt.replace("norteleste", "nordeste")
        
        # Traduções básicas
        texto_pt = texto_pt.replace("Head", "Siga")
        texto_pt = texto_pt.replace("Turn right", "Vire à direita")
        texto_pt = texto_pt.replace("Turn left", "Vire à esquerda")
        texto_pt = texto_pt.replace("Continue onto", "Continue pela")
        texto_pt = texto_pt.replace("Continue to follow", "Continue seguindo pela")
        texto_pt = texto_pt.replace("Walk your bicycle", "Desça da bicicleta")
        texto_pt = texto_pt.replace("toward", "em direção a")
        texto_pt = texto_pt.replace("Pass by", "Passe por")
        texto_pt = texto_pt.replace("on the right", "à direita")
        texto_pt = texto_pt.replace("on the left", "à esquerda")
        texto_pt = texto_pt.replace("in", "em")
        texto_pt = texto_pt.replace("Destination", "Destino")
        texto_pt = texto_pt.replace("will be", "estará")
        texto_pt = texto_pt.replace("northeast", "nordeste")
        texto_pt = texto_pt.replace("southeast", "sudeste")
        texto_pt = texto_pt.replace("northwest", "noroeste")
        texto_pt = texto_pt.replace("southwest", "sudoeste")
        texto_pt = texto_pt.replace("Restricted usage road", "Estrada de uso restrito")
        texto_pt = texto_pt.replace("Slight right", "Vire levemente à direita")
        texto_pt = texto_pt.replace("Slight left", "Vire levemente à esquerda")
        
        return texto_pt

# — Ícones por sensor e faixa de valores —
sensor_icons = {
    "temperatura": [(-273,0,"🥶"), (0,15,"🧥"), (15,25,"🌤️"), (25,35,"☀️"), (35,1000,"🔥")],
    "umidade":     [(0,20,"🌵"), (20,40,"💧"), (40,60,"🌦️"), (60,80,"☔"), (80,100,"🌊")],
    "pressao":     [(0,980,"🌪️"), (980,1000,"💨"), (1000,1013,"☁️"), (1013,1025,"🌬️"), (1025,1100,"🎈")],
    "luminosidade":[(0,50,"🌑"), (50,300,"🌘"), (300,600,"🌕"), (600,800,"🌈"), (800,2000,"🔆")],
}

def get_sensor_icon(key: str, value: float) -> str:
    for low, high, icon in sensor_icons.get(key, []):
        if low <= value < high:
            return icon
    return "❓"

# — Funções para gerar o guia e a rota —
def gerar_prompt(relatorio: str, nivel: str, distancia: int, endereco: str, horario: str, estilo: str) -> str:
    tom = {
        "Iniciante": "😜 Solta a zoeira de leve, mas passa a real! Use gírias básicas de ciclismo, seja motivador e bem explicativo.",
        "Intermediário": "🚵 Papo de quem já conhece o rolê. Use gírias intermediárias de ciclista e dicas mais técnicas.",
        "Avançado": "🚴‍♀️ Conversa entre veteranos. Use gírias avançadas, fale de cadência, técnicas de subida e recuperação.",
        "Profissional": "🏆 Papo de elite do pedal. Foque em alto rendimento, treinamento específico e desempenho competitivo.",
        # Manter compatibilidade com código antigo
        "Moderado": "😎 Papo reto de parceiro de pedal que já manja do rolê.",
        "Experiente": "🚴‍♂️ Troca técnica entre veteranos experientes que já encaram trilhas sinistras."
    }.get(nivel, "😎 Papo reto de parceiro de pedal.")
    
    return f"""
# 🌟 Guia Prático do Pedal Urbano em São José dos Campos 🌟

{tom}

Hoje vamos fazer um rolê de **EXATAMENTE {distancia} km** no período da **{horario}**, saindo de **{endereco}**, com visual no estilo **{estilo}**.  
Use estes dados e o clima como norte:

{relatorio}

IMPORTANTE: Divida seu guia em 3 partes bem definidas, usando MUITOS emojis e gírias de ciclismo:

## 📍 ROTEIRO E EXPLICAÇÃO
Explique o roteiro que você escolheu e PORQUE ele é perfeito para esse perfil de ciclista. A rota DEVE ter EXATAMENTE {distancia} km, ser CÍCLICA (começar e terminar no mesmo ponto) e levar em conta o nível do ciclista, horário e clima.

## 🔧 DICAS DE PEDALADA
Dê dicas técnicas de pedalada específicas para o nível {nivel}, como se você fosse um treinador experiente. Personalize as dicas para o terreno de São José dos Campos, o tipo de pedal ({estilo}), distância ({distancia}km) e horário ({horario}).

## 💪 DICAS DE SAÚDE E TREINO
Forneça conselhos de saúde, nutrição e treino específicos para esse perfil de ciclista. Ajuste as dicas conforme o nível de experiência, distância e condições do pedal.

Liste o roteiro em 5 passos claros, mencionando ruas ou pontos de referência REAIS em São José dos Campos.

Use linguagem descontraída com MUITAS gírias de ciclismo, escreva como um ciclista falaria com outro, cheio de expressões típicas do universo do ciclismo brasileiro. Seja divertido e informativo ao mesmo tempo!
"""

def gerar_guia(relatorio: str, nivel: str, distancia: int, endereco: str, horario: str, estilo: str) -> dict:
    """
    Gera um guia de pedalada personalizado com linguagem de ciclista (método antigo)
    
    Args:
        relatorio (str): Dados de sensores e condições climáticas
        nivel (str): Nível de experiência do ciclista
        distancia (int): Distância desejada em km
        endereco (str): Endereço de partida
        horario (str): Período do dia (manhã, tarde, noite)
        estilo (str): Estilo visual da pedalada
        
    Returns:
        dict: Contendo o texto do guia personalizado
    """    
    # Preparar o prompt base
    prompt = gerar_prompt(relatorio, nivel, distancia, endereco, horario, estilo)
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        # Obter o texto do guia
        guia_texto = resp.choices[0].message.content
    except Exception as e:
        st.error(f"Erro ao gerar guia: {str(e)}")
        guia_texto = f"""
        # 🚲 Guia de Pedalada: {distancia}km na {horario}
        
        Desculpe, não foi possível gerar um guia personalizado. 
        
        **Dicas gerais:**
        - Verifique o clima antes de sair
        - Leve água suficiente
        - Use capacete e equipamentos de segurança
        - Prefira ciclovias e ruas menos movimentadas
        
        **Roteiro sugerido:**
        1. Comece em {endereco}
        2. Siga para o Parque Santos Dumont, São José dos Campos
        3. Passe pela Avenida São José
        4. Visite o centro da cidade
        5. Retorne ao ponto de partida
        """
    
    # Retornar apenas o guia de texto
    return {
        "texto": guia_texto
    }

def gerar_guia_com_rota(relatorio: str, nivel: str, distancia_real: float, endereco: str, horario: str, estilo: str, dados_rota: dict) -> str:
    """
    Gera um guia de pedalada personalizado com base em uma rota já calculada
    
    Args:
        relatorio (str): Dados de sensores e condições climáticas
        nivel (str): Nível de experiência do ciclista
        distancia_real (float): Distância real calculada da rota em km
        endereco (str): Endereço de partida
        horario (str): Período do dia (manhã, tarde, noite)
        estilo (str): Estilo visual da pedalada
        dados_rota (dict): Dados da rota já calculada (passos, distância, etc.)
        
    Returns:
        str: Texto do guia personalizado com base na rota real
    """
    # Importar função para comparar temperatura com histórico
    from pedala_teste_2 import comparar_temperatura_historica
    # Extrair os dados relevantes da rota
    passos_rota = dados_rota.get("passos", [])
    pontos_referencia = dados_rota.get("waypoints", [])
    
    # Formatar os passos da rota para o prompt
    if passos_rota:
        passos_texto = "\n".join([f"- {passo}" for passo in passos_rota[:min(5, len(passos_rota))]])
    else:
        passos_texto = "- Rota não disponível"
    
    # Obter informações sobre a temperatura comparada com dados históricos
    try:
        # Tentar obter a temperatura atual a partir do relatorio
        temp_match = re.search(r'Temperatura:\s*([\d\.]+)°C', relatorio)
        if temp_match:
            temperatura_atual = float(temp_match.group(1))
            analise_temperatura = comparar_temperatura_historica(temperatura_atual)
            
            # Criar texto com análise da temperatura
            if analise_temperatura["status"] == "dentro":
                temp_analise_texto = f"""
📊 **Análise climática histórica**:
A temperatura atual de {analise_temperatura['temperatura_atual']:.1f}°C está dentro da faixa histórica para este mês 
(mínima: {analise_temperatura['min_historica']}°C, máxima: {analise_temperatura['max_historica']}°C).
Está {analise_temperatura['diferenca']:.1f}°C distante da média histórica de {analise_temperatura['media_historica']}°C.
"""
            elif analise_temperatura["status"] == "acima":
                temp_analise_texto = f"""
📊 **Análise climática histórica**:
⚠️ A temperatura atual de {analise_temperatura['temperatura_atual']:.1f}°C está {analise_temperatura['diferenca']:.1f}°C ACIMA 
da máxima histórica de {analise_temperatura['max_historica']}°C para este mês.
Isso representa {analise_temperatura['percentual']}% acima do normal, exigindo cuidados extras com hidratação.
"""
            else:  # abaixo
                temp_analise_texto = f"""
📊 **Análise climática histórica**:
❄️ A temperatura atual de {analise_temperatura['temperatura_atual']:.1f}°C está {analise_temperatura['diferenca']:.1f}°C ABAIXO 
da mínima histórica de {analise_temperatura['min_historica']}°C para este mês.
Isso representa {analise_temperatura['percentual']}% abaixo do normal, recomendando vestimenta adequada.
"""
        else:
            temp_analise_texto = ""
    except Exception as e:
        print(f"Erro ao analisar temperatura: {str(e)}")
        temp_analise_texto = ""
    
    # Construir um prompt específico baseado na rota real
    prompt = f"""
# 🚲 Guia Personalizado de Pedalada em São José dos Campos

Crie um guia detalhado para uma pedalada saindo de {endereco}, seguindo EXATAMENTE a rota abaixo.
A distância total é de {distancia_real:.1f} km e a pedalada será realizada no período da {horario}.
O ciclista tem nível {nivel} e prefere o estilo {estilo}.

## Dados dos sensores e condições ambientais:
{relatorio}

{temp_analise_texto}

## Rota calculada (SIGA EXATAMENTE ESTA ROTA):
{passos_texto}

## Pontos principais:
{", ".join(pontos_referencia)}

EXTREMAMENTE IMPORTANTE:
1. Estruture o guia com EXATAMENTE as seguintes seções:
   - ROTEIRO E EXPLICAÇÃO (explicando a rota acima e destacando aspectos de SEGURANÇA)
   - DICAS DE PEDALADA (específicas para o nível {nivel} e tipo de terreno da rota)
   - DICAS DE SAÚDE E TREINO

2. Prioridades de segurança para enfatizar:
   - Evite rodovias movimentadas
   - Destaque ciclovias e ciclofaixas
   - Indique trechos onde é preciso ter atenção especial
   - Para iniciantes: priorize rotas mais tranquilas e planas
   - Para avançados: identifique desafios de terreno (subidas, curvas)

2. Use uma linguagem super descontraída de ciclista, com MUITAS gírias de ciclismo brasileiro e emojis adequados ao perfil:

- Para Iniciante: Use gírias básicas como "dar um rolê", "pedalar na maciota", "rabeira", "segurar o guidão", "bater perna"
- Para Intermediário: "colar na roda", "pegar vácuo", "bater o ferro", "casquinha", "costela", "dropbar", "base"
- Para Avançado: "W/kg", "PMA", "cadência", "paceline", "pelotão", "K.O.M", "breakaway", "cortar a volta"
- Para Profissional: "wattagem", "altimetria", "intervalo", "CAT 1/2/3", "LT", "FTP", "vias aeróbicas", "potência específica"

3. Mencione TODOS os nomes de ruas e pontos da rota acima, na ordem exata apresentada.

4. Adapte as dicas considerando os dados do clima, a análise histórica da temperatura, o horário da pedalada, o nível do ciclista e o estilo escolhido. SEMPRE inclua uma seção sobre o clima, mencionando se a temperatura está acima, abaixo ou dentro das médias históricas.

Escreva como se você fosse um parceiro de pedal experiente falando diretamente com o ciclista!
"""

    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        # Obter o texto do guia
        guia_texto = resp.choices[0].message.content
    except Exception as e:
        st.error(f"Erro ao gerar guia baseado na rota: {str(e)}")
        # Criar um guia básico em caso de erro
        guia_texto = f"""
# 🚲 Guia de Pedalada: {distancia_real:.1f}km na {horario}

## 📍 ROTEIRO E EXPLICAÇÃO
Vamos pedalar por São José dos Campos! Nossa rota começa em {endereco} e percorre {distancia_real:.1f}km.

**Roteiro:**
1. Saímos de {endereco}
2. Seguimos por {passos_rota[0] if passos_rota else 'São José dos Campos'}
3. Continuamos por {passos_rota[1] if len(passos_rota) > 1 else 'vias locais'}
4. Passamos por {passos_rota[2] if len(passos_rota) > 2 else 'pontos conhecidos'}
5. Retornamos ao ponto de partida em {endereco}

## 🔧 DICAS DE PEDALADA
- Mantenha um ritmo constante
- Hidrate-se constantemente, especialmente com a temperatura e condições atuais
- Preste atenção ao tráfego

## 💪 DICAS DE SAÚDE E TREINO
- Alongue-se antes e depois da pedalada
- Mantenha uma alimentação adequada
- Descanse o suficiente após o exercício
"""
    
    return guia_texto

def extrair_passos_do_guia(guia_md: str) -> list[str]:
    passos = []
    
    # Procurar por menções de ruas, avenidas e pontos de referência
    # Primeiro, vamos procurar por itens numerados que frequentemente contêm os passos da rota
    for line in guia_md.splitlines():
        # Verificar padrões como "1. Rua X" ou "- Avenida Y" ou mesmo "**Ponto Z**:"
        locais_pattern = r'\*\*([^*]+)\*\*|(?:^\s*[\-\d]\.?\s*)([^:]+):|(?:até|pela|no|na|ao|para|por)\s+((?:Rua|R\.|Avenida|Av\.|Praça|Parque)\s+[^\s,\.]+(?:\s+[^\s,\.]+){0,3})'
        matches = re.findall(locais_pattern, line, re.IGNORECASE)
        
        for match in matches:
            # Pegar a parte não vazia do match
            match_texto = next((m for m in match if m), "")
            if not match_texto:
                continue
                
            # Limpar o texto (remover emojis, símbolos, etc)
            passo_limpo = re.sub(r'[^\w\s,]', '', match_texto).strip()
            
            # Se contém palavras como "Rua", "Avenida", "Parque", etc., é provável que seja um endereço
            if any(palavra in passo_limpo for palavra in ["Rua", "Avenida", "Av.", "R.", "Praça", "Parque", "Alameda"]):
                # Extrair apenas o nome da rua/local
                rua_pattern = r'((?:Rua|R\.|Avenida|Av\.|Praça|Parque|Alameda)\s+[^\s,\.]+(?:\s+[^\s,\.]+){0,3})'
                rua_match = re.search(rua_pattern, passo_limpo, re.IGNORECASE)
                
                if rua_match:
                    passo_limpo = rua_match.group(1)
            
            # Garantir que realmente temos um local e não apenas uma palavra genérica
            if len(passo_limpo.split()) >= 2 and not passo_limpo.startswith(("Hora", "Começamos", "Segura", "Fechamos", "Curte", "Missão", "Aqui")):
                # Adicionar a cidade se não estiver presente
                if "São José dos Campos" not in passo_limpo and "SJC" not in passo_limpo:
                    passo_limpo += ", São José dos Campos, SP"
                    
                passos.append(passo_limpo)
    
    # Verificar se encontramos pontos de referência válidos em negrito (formato alternativo)
    if not passos:
        destaque_pattern = r'\*\*([^*]+)\*\*'
        for match in re.finditer(destaque_pattern, guia_md):
            texto = match.group(1).strip()
            # Verificar se o texto parece ser um ponto no roteiro (começa com número, por exemplo)
            if re.match(r'^\d+\.', texto) or "Rua" in texto or "Avenida" in texto or "Parque" in texto or "Praça" in texto:
                # Extrair o local após o número se houver
                local = re.sub(r'^\d+\.\s*', '', texto)
                if len(local.split()) >= 2:  # Garantir que não é apenas uma palavra
                    if "São José dos Campos" not in local and "SJC" not in local:
                        local += ", São José dos Campos, SP"
                    passos.append(local)
    
    # Se não encontramos passos usando o padrão acima, tentar procurar por nomes de ruas ou locais conhecidos
    if not passos:
        # Padrão para encontrar nomes de ruas e avenidas
        ruas_pattern = r'(?:Rua|Avenida|Av\.|R\.) [A-ZÀ-Úa-zà-ú\s]+'
        matches = re.findall(ruas_pattern, guia_md)
        for match in matches:
            passos.append(f"{match}, São José dos Campos, SP")
    
    # Se ainda assim não temos passos, vamos usar alguns pontos conhecidos de São José dos Campos
    if not passos:
        passos = [
            "Praça Afonso Pena, São José dos Campos, SP",
            "Parque Santos Dumont, São José dos Campos, SP",
            "Shopping Centro, São José dos Campos, SP",
            "Parque Vicentina Aranha, São José dos Campos, SP"
        ]
        
    # Limitar a 5 passos para não sobrecarregar a API
    return passos[:5]

def gerar_rota_e_embed(origem: str, passos: list[str], distancia: int = 15, forcar_distancia: bool = False):
    """
    Gera uma rota circular e um mapa HTML embutível que respeita a distância solicitada
    
    Args:
        origem (str): Endereço de origem (e retorno) da rota
        passos (list[str]): Lista de pontos de referência da rota
        distancia (int): Distância desejada em km
        forcar_distancia (bool): Se True, força a distância a ficar próxima do valor solicitado
        
    Returns:
        tuple: HTML do mapa, texto descritivo da rota, dados de elevação
    """
    global has_gmaps, GMAPS_KEY, gmaps
    
    if not passos:
        return "", "<p>Não foi possível extrair passos para a rota.</p>", []
    
    # Se não temos acesso ao Google Maps, retornamos uma mensagem explicativa
    if not has_gmaps:
        return "", "<p>Mapas indisponíveis sem uma chave de API do Google Maps.</p>", []
        
    # Preparar waypoints
    waypoints_to_use = []
    for passo in passos:
        # Certificar que cada waypoint tem a cidade incluída
        if "São José dos Campos" not in passo and "SJC" not in passo:
            waypoint = f"{passo}, São José dos Campos, SP"
        else:
            waypoint = passo
        waypoints_to_use.append(waypoint)
    
    # Definir client de Maps, se necessário
    try:
        if not gmaps:
            GMAPS_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
            if GMAPS_KEY:
                gmaps = googlemaps.Client(key=GMAPS_KEY)
                has_gmaps = True
            else:
                st.warning("⚠️ Chave da API do Google Maps não encontrada!")
                has_gmaps = False
                return "", "<p>Mapa não disponível sem a chave do Google Maps API</p>", []
        
        # Perfis de ciclista para personalizar a rota
        ciclista_fatores = {
            "Iniciante": 0.6,      # Iniciantes: rotas mais curtas
            "Intermediário": 0.8,   # Intermediários: rotas médias
            "Avançado": 1.0,        # Avançados: rotas completas
            "Profissional": 1.2     # Profissionais: rotas mais desafiadoras
        }
        
        # Ajustes por estilo de pedalada
        estilo_ajustes = {
            "urbano": {"lat_bias": 0.8, "lng_bias": 1.2},   # Urbano: áreas centrais
            "montanha": {"lat_bias": 1.5, "lng_bias": 0.8}, # Montanha: mais elevação
            "parques": {"lat_bias": 1.2, "lng_bias": 1.0},  # Parques: equilibrado
            "familiar": {"lat_bias": 0.6, "lng_bias": 0.6}  # Familiar: rotas mais curtas
        }
        
        # Tentar obter dados da sessão
        try:
            nivel_ciclista = st.session_state.data['nivel']
            estilo_pedalada = st.session_state.data['estilo']
        except:
            nivel_ciclista = "Intermediário"
            estilo_pedalada = "urbano"
        
        # Aplicar fatores de perfil
        perfil_fator = ciclista_fatores.get(nivel_ciclista, 0.8)
        estilo_config = estilo_ajustes.get(estilo_pedalada, {"lat_bias": 1.0, "lng_bias": 1.0})
        
        directions = None
        
        # Gerar a rota usando pontos cardeais
        with st.spinner("Gerando rota personalizada..."):
            # Obter coordenadas da origem
            geocode_result = gmaps.geocode(origem)
            if geocode_result:
                start_lat = geocode_result[0]['geometry']['location']['lat']
                start_lng = geocode_result[0]['geometry']['location']['lng']
                
                # Calcular raio base baseado na distância solicitada
                raio_km = distancia / (2 * 3.14)  # Raio aproximado
                
                # Calcular fator para distância desejada
                base_factor = 0.002 * distancia
                
                # Ajustar pelo perfil e estilo
                best_route = None
                best_distance_diff = float('inf')
                
                # Tentar várias combinações para encontrar a rota ideal
                # Usar mais multiplicadores para ter mais chances de encontrar uma rota adequada
                for factor_mult in [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]:
                    factor = base_factor * factor_mult * perfil_fator
                    
                    # Criar pontos de waypoint - usando mais variações
                    north = f"{start_lat + factor * estilo_config['lat_bias']},{start_lng}"
                    east = f"{start_lat},{start_lng + factor * estilo_config['lng_bias']}"
                    south = f"{start_lat - factor * estilo_config['lat_bias']},{start_lng}"
                    west = f"{start_lat},{start_lng - factor * estilo_config['lng_bias']}"
                    
                    # Diferentes combinações de pontos
                    waypoint_sets = [
                        [north, east],
                        [north, west],
                        [south, east], 
                        [south, west],
                        [north, south],
                        [east, west]
                    ]
                    
                    for waypoints in waypoint_sets:
                        try:
                            # Gerar rota de teste
                            test_route = gmaps.directions(
                                origin=origem,
                                destination=origem,
                                waypoints=waypoints,
                                mode="bicycling",
                                optimize_waypoints=True
                            )
                            
                            if test_route:
                                # Calcular distância desta rota
                                test_distance = sum(leg['distance']['value'] for leg in test_route[0]['legs'])/1000
                                distance_diff = abs(test_distance - distancia)
                                
                                # Tolerância SEMPRE 2.0 km no máximo
                                tolerancia = 2.0
                                
                                # Verificar se está dentro do limite e não ultrapassa a distância solicitada em mais de 2km
                                if distance_diff <= tolerancia and test_distance <= distancia + tolerancia:
                                    # Rota dentro da tolerância, mas damos preferência para rotas menores ou iguais à solicitada
                                    if test_distance <= distancia:
                                        best_route = test_route
                                        best_distance_diff = distance_diff
                                        break  # Sai do loop de waypoints
                                    # Se não for menor, guarda como melhor opção até agora
                                    elif distance_diff < best_distance_diff:
                                        best_route = test_route
                                        best_distance_diff = distance_diff
                                # Se for melhor, mas ainda dentro da tolerância, guardar esta rota
                                elif test_distance <= distancia + tolerancia and distance_diff < best_distance_diff:
                                    best_route = test_route
                                    best_distance_diff = distance_diff
                        except:
                            # Silenciosamente continuar para a próxima tentativa
                            pass
                    
                    # Se encontrou uma rota adequada, interromper o loop de multiplicadores
                    tolerancia = 2.0  # Tolerância fixa de 2km, sem exceções
                    if best_distance_diff <= tolerancia:
                        break
                
                # Priorizar os waypoints extraídos do guia
                try:
                    # Primeiro tentar com os waypoints específicos do guia
                    if len(waypoints_to_use) >= 2:
                        specific_directions = gmaps.directions(
                            origin=origem,
                            destination=origem,
                            waypoints=waypoints_to_use[:min(5, len(waypoints_to_use))],  # Limite de 5 waypoints intermediários
                            mode="bicycling",
                            optimize_waypoints=True
                        )
                        if specific_directions:
                            directions = specific_directions
                except Exception as e:
                    st.warning(f"Não foi possível gerar rota com pontos específicos: {str(e)}")

                # Se conseguiu com pontos específicos, verificar se a distância está dentro da tolerância
                if directions:
                    # Calcular a distância total da rota com pontos específicos
                    total_distance = sum(leg['distance']['value'] for leg in directions[0]['legs'])/1000
                    # Se a distância exceder a tolerância, descartar esta rota
                    if abs(total_distance - distancia) > 2.0:
                        directions = None
                        # Apenas registrar o erro no log, não mostrar ao usuário
                        print(f"ERRO: Rota gerada de {total_distance:.1f}km excede a tolerância de ±2km da distância solicitada ({distancia}km)")
                        
                # Se não conseguiu com pontos específicos ou a distância excedeu, usar a melhor rota circular calculada
                if not directions and best_route:
                    # Verificar se a melhor rota está dentro da tolerância
                    best_distance = sum(leg['distance']['value'] for leg in best_route[0]['legs'])/1000
                    if abs(best_distance - distancia) <= 2.0:
                        directions = best_route
                    else:
                        # Só logar o erro, não mostrar ao usuário
                        print(f"ERRO: Nenhuma rota dentro da tolerância de ±2km foi encontrada. A melhor rota tem {best_distance:.1f}km")
            
            # Se ainda não tem rota, tentar rota mais simples
            if not directions:
                try:
                    test_directions = gmaps.directions(
                        origin=origem,
                        destination=origem,
                        mode="bicycling"
                    )
                    
                    # Verificar se a distância está dentro da tolerância
                    if test_directions:
                        test_distance = sum(leg['distance']['value'] for leg in test_directions[0]['legs'])/1000
                        if abs(test_distance - distancia) <= 2.0:
                            directions = test_directions
                        else:
                            # Apenas registrar no log, não mostrar ao usuário
                            print(f"ERRO: Rota básica de {test_distance:.1f}km excede a tolerância de ±2km da distância solicitada ({distancia}km)")
                except Exception as e:
                    st.error(f"Erro ao gerar rota básica: {str(e)}")
            
            # Se nenhuma tentativa funcionou
            if not directions:
                return "", "<p>Não foi possível gerar um roteiro para o endereço especificado.</p>", []
        
        # Obter dados de elevação
        elevation_data = []
        try:
            max_steps = 5
            step_count = 0
            
            for leg in directions[0]['legs']:
                for step in leg['steps']:
                    if step_count >= max_steps:
                        break
                        
                    start_loc = step['start_location']
                    try:
                        elevation_result = gmaps.elevation((start_loc['lat'], start_loc['lng']))
                        if elevation_result:
                            elevation_data.append({
                                'distance': len(elevation_data) * 0.5,
                                'elevation': elevation_result[0]['elevation']
                            })
                    except:
                        pass
                    step_count += 1
        except:
            pass
        
        # Calcular distância total
        distancia_total = sum(leg['distance']['value'] for leg in directions[0]['legs'])/1000
        distancia_total = f"{distancia_total:.1f} km"
        
        # Extrair instruções
        ruas = [html.unescape(re.sub(r'<[^>]+>', '', step['html_instructions']))
               for leg in directions[0]['legs'] for step in leg['steps']]
        
        # Traduzir instruções
        ruas_traduzidas = []
        for rua in ruas:
            # Substituições básicas de inglês para português
            rua_pt = rua.replace("Turn right", "Vire à direita")
            rua_pt = rua_pt.replace("Turn left", "Vire à esquerda")
            rua_pt = rua_pt.replace("Continue onto", "Continue pela")
            rua_pt = rua_pt.replace("Continue to follow", "Continue seguindo pela")
            rua_pt = rua_pt.replace("Head", "Siga")
            rua_pt = rua_pt.replace("Destination", "Destino")
            rua_pt = rua_pt.replace("north", "norte")
            rua_pt = rua_pt.replace("south", "sul")
            rua_pt = rua_pt.replace("east", "leste")
            rua_pt = rua_pt.replace("west", "oeste")
            rua_pt = rua_pt.replace("Walk your bicycle", "Desça da bicicleta")
            rua_pt = rua_pt.replace("toward", "em direção a")
            rua_pt = rua_pt.replace("Pass by", "Passe por")
            rua_pt = rua_pt.replace("on the right", "à direita")
            rua_pt = rua_pt.replace("on the left", "à esquerda")
            rua_pt = rua_pt.replace("in", "em")
            rua_pt = rua_pt.replace("m)", "m)")
            
            # Traduções adicionais (caso rota simplificada não funcione)
            rua_pt = rua_pt.replace("take the", "pegue a")
            rua_pt = rua_pt.replace("take the 1st", "pegue a 1ª")
            rua_pt = rua_pt.replace("take the 2nd", "pegue a 2ª")
            rua_pt = rua_pt.replace("take the 3rd", "pegue a 3ª")
            rua_pt = rua_pt.replace("take the 4th", "pegue a 4ª")
            rua_pt = rua_pt.replace("take the 5th", "pegue a 5ª")
            rua_pt = rua_pt.replace("exit", "saída")
            rua_pt = rua_pt.replace("At the roundabout", "Na rotatória")
            rua_pt = rua_pt.replace("At", "Em")
            rua_pt = rua_pt.replace("roundabout", "rotatória")
            rua_pt = rua_pt.replace("Enter", "Entre na")
            rua_pt = rua_pt.replace("and", "e")
            rua_pt = rua_pt.replace("the", "a")
            rua_pt = rua_pt.replace("your", "sua")
            rua_pt = rua_pt.replace("until", "até")
            rua_pt = rua_pt.replace("will be", "estará")
            rua_pt = rua_pt.replace("for", "por")
            rua_pt = rua_pt.replace("next", "próximo")
            rua_pt = rua_pt.replace("Slight", "Levemente")
            rua_pt = rua_pt.replace("Keep", "Mantenha-se")
            rua_pt = rua_pt.replace("right", "direita")
            rua_pt = rua_pt.replace("left", "esquerda")
            
            ruas_traduzidas.append(rua_pt)
        
        # Gerar HTML do mapa
        mapa_html = f"""
<div id="map" style="height:500px; border-radius:12px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);"></div>
<script>
  function initMap() {{
    const map = new google.maps.Map(document.getElementById("map"), {{
      zoom: 14,
      center: {{ lat: {directions[0]['legs'][0]['start_location']['lat']}, lng: {directions[0]['legs'][0]['start_location']['lng']} }},
      styles: [
        {{
          "featureType": "all",
          "elementType": "labels.text.fill",
          "stylers": [{{ "color": "#ffffff" }}]
        }},
        {{
          "featureType": "all",
          "elementType": "labels.text.stroke",
          "stylers": [{{ "color": "#000000" }}, {{ "lightness": 13 }}]
        }},
        {{
          "featureType": "administrative",
          "elementType": "geometry.fill",
          "stylers": [{{ "color": "#000000" }}]
        }},
        {{
          "featureType": "administrative",
          "elementType": "geometry.stroke",
          "stylers": [{{ "color": "#144b53" }}, {{ "lightness": 14 }}, {{ "weight": 1.4 }}]
        }},
        {{
          "featureType": "landscape",
          "elementType": "all",
          "stylers": [{{ "color": "#08304b" }}]
        }},
        {{
          "featureType": "poi",
          "elementType": "geometry",
          "stylers": [{{ "color": "#0c4152" }}, {{ "lightness": 5 }}]
        }},
        {{
          "featureType": "road.highway",
          "elementType": "geometry.fill",
          "stylers": [{{ "color": "#3498db" }}]
        }},
        {{
          "featureType": "road.highway",
          "elementType": "geometry.stroke",
          "stylers": [{{ "color": "#2980b9" }}, {{ "lightness": 25 }}]
        }},
        {{
          "featureType": "road.arterial",
          "elementType": "geometry.fill",
          "stylers": [{{ "color": "#2c3e50" }}]
        }},
        {{
          "featureType": "road.arterial",
          "elementType": "geometry.stroke",
          "stylers": [{{ "color": "#0b3d51" }}, {{ "lightness": 16 }}]
        }},
        {{
          "featureType": "road.local",
          "elementType": "geometry",
          "stylers": [{{ "color": "#000000" }}]
        }},
        {{
          "featureType": "transit",
          "elementType": "all",
          "stylers": [{{ "color": "#146474" }}]
        }},
        {{
          "featureType": "water",
          "elementType": "all",
          "stylers": [{{ "color": "#021019" }}]
        }}
      ]
    }});
    const directionsService = new google.maps.DirectionsService();
    const directionsRenderer = new google.maps.DirectionsRenderer({{
      map: map,
      polylineOptions: {{
        strokeColor: '#e74c3c',
        strokeWeight: 6,
        strokeOpacity: 0.9
      }}
    }});
    directionsService.route({{
      origin: "{origem}",
      destination: "{origem}",
      waypoints: [
        // É essencial ter pelo menos um waypoint para rotas circulares
        // Calcular um ponto ao norte do ponto de partida
        {{
          location: new google.maps.LatLng(
            {directions[0]['legs'][0]['start_location']['lat'] + 0.02}, 
            {directions[0]['legs'][0]['start_location']['lng']}
          )
        }}
      ],
      travelMode: google.maps.TravelMode.BICYCLING,
      optimizeWaypoints: true,
    }}, (result, status) => {{
      if (status === "OK") directionsRenderer.setDirections(result);
      else alert("Falha na rota: " + status);
    }});
  }}
</script>
<script src="https://maps.googleapis.com/maps/api/js?key={GMAPS_KEY}&callback=initMap" async defer></script>
"""
        
        # Gerar texto da rota
        texto = f"""
### 🗺️ Resumo da Rota  
**Origem e retorno:** {origem}  
**Distância total:** {distancia_total}  

**Passos detalhados:**  
<ol>
{''.join(f"<li>{rua}</li>" for rua in ruas_traduzidas)}
</ol>
"""
        return mapa_html, texto, elevation_data
        
    except Exception as e:
        st.error(f"Erro ao gerar rota: {str(e)}")
        return "", f"<p>Não foi possível gerar a rota: {str(e)}</p>", []
        
    try:
        # ⭐ Melhorar os pontos de referência adicionando a cidade para evitar erros NOT_FOUND
        waypoints_completos = []
        for passo in passos:
            # Certificar que cada waypoint tem a cidade incluída
            if "São José dos Campos" not in passo and "SJC" not in passo:
                waypoint = f"{passo}, São José dos Campos, SP"
            else:
                waypoint = passo
            waypoints_completos.append(waypoint)
        
        # Primeiro tentamos com todos os pontos (até 5, que é o máximo que o Google Maps permite no plano gratuito)
        max_waypoints = min(len(waypoints_completos), 5)
        waypoints_to_use = waypoints_completos[0:max_waypoints]
        
        # Processar pontos de referência internamente, sem mostrar ao usuário
        
        # ⭐ Uso da API com tratamento de erros mais robusto
        try:
            # Remover ponto A → ponto A sem waypoints dá distância zero
            # Então vamos gerar uma rota circular usando algoritmo específico
            
            # Definir fatores específicos baseados no tipo de ciclista e estilo
            # Escondendo logs de processamento e mensagens de status
            with st.spinner(f"Gerando rota personalizada de {distancia} km..."):
                # Usar nível e estilo para personalizar rota
                # 1. Usar fatores diferentes por perfil
                ciclista_fatores = {
                    "Iniciante": 0.6,       # Iniciantes: rotas mais curtas, menos elevação
                    "Intermediário": 0.8,    # Intermediários: rotas médias
                    "Avançado": 1.0,         # Avançados: rotas completas
                    "Profissional": 1.2      # Profissionais: rotas mais desafiadoras
                }
                
                # 2. Aplicar ajustes por estilo de pedalada
                estilo_ajustes = {
                    "urbano": {"lat_bias": 0.8, "lng_bias": 1.2},      # Urbano: preferência para áreas centrais
                    "montanha": {"lat_bias": 1.5, "lng_bias": 0.8},     # Montanha: mais elevação
                    "parques": {"lat_bias": 1.2, "lng_bias": 1.0},      # Parques: equilibrado
                    "familiar": {"lat_bias": 0.6, "lng_bias": 0.6}      # Familiar: rotas mais curtas e seguras
                }
                
                # Pegar perfil do ciclista da sessão
                try:
                    nivel_ciclista = data['nivel']
                    estilo_pedalada = data['estilo']
                except:
                    nivel_ciclista = "Intermediário"
                    estilo_pedalada = "urbano"
                
                # Aplicar fatores baseados no perfil
                perfil_fator = ciclista_fatores.get(nivel_ciclista, 0.8)
                estilo_config = estilo_ajustes.get(estilo_pedalada, {"lat_bias": 1.0, "lng_bias": 1.0})
                
                # Calcular raio base baseado na distância solicitada
                raio_km = distancia / (2 * 3.14)  # Raio aproximado para obter a distância desejada
                
                # Obter as coordenadas da origem
                geocode_result = gmaps.geocode(origem)
                best_route = None
                best_distance_diff = float('inf')
                
                if geocode_result:
                    start_lat = geocode_result[0]['geometry']['location']['lat']
                    start_lng = geocode_result[0]['geometry']['location']['lng']
                    
                    # Tentar diferentes fatores até encontrar uma distância próxima da solicitada
                    # Fator inicial baseado na distância solicitada
                    base_factor = 0.002 * distancia
                    
                    # Variações do fator para tentar diferentes distâncias - mais precisas para respeitar a tolerância de 2km
                    factor_variations = [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3]
                    
                    # Aplicar o ajuste de perfil mas sem ultrapassar limites razoáveis para a distância
                    factor_variations = [max(0.5, min(1.3, f * perfil_fator)) for f in factor_variations]
                    
                    # Tentar diversos fatores até encontrar a melhor rota dentro da tolerância
                    for factor_mult in factor_variations:
                        factor = base_factor * factor_mult
                        
                        # Aplicar fatores de estilo para direções diferentes (norte, leste, etc)
                        north_factor = factor * estilo_config["lat_bias"]
                        east_factor = factor * estilo_config["lng_bias"]
                        
                        # Criar pontos cardeais para este teste
                        north = f"{start_lat + north_factor},{start_lng}"
                        east = f"{start_lat},{start_lng + east_factor}"
                        
                        # Gerar rota com estes pontos
                        try:
                            test_route = gmaps.directions(
                                origin=origem,
                                destination=origem,
                                waypoints=[north, east],
                                mode="bicycling",
                                optimize_waypoints=True
                            )
                            
                            if test_route:
                                # Calcular distância desta rota
                                test_distance = sum(leg['distance']['value'] for leg in test_route[0]['legs'])/1000
                                
                                # Verificar se está dentro da tolerância (2km)
                                distance_diff = abs(test_distance - distancia)
                                
                                # Se for mais próxima da distância solicitada, salvar como melhor rota
                                if distance_diff < best_distance_diff:
                                    best_route = test_route
                                    best_distance_diff = distance_diff
                                    
                                    # Se diferença < 2km, temos uma rota boa o suficiente
                                    if distance_diff <= 2.0:
                                        break
                                        
                        except Exception as e:
                            # Silenciosamente continuar para o próximo fator
                            pass
                    
                    # Usar a melhor rota encontrada
                    if best_route:
                        directions = best_route
                    else:
                        # Se nenhuma rota foi encontrada, usar a última tentativa
                        directions = gmaps.directions(
                            origin=origem,
                            destination=origem,
                            waypoints=[north, east],
                            mode="bicycling",
                            optimize_waypoints=True
                        )
                else:
                    # Se não encontrou parques, vamos calcular pontos cardeais
                    # e criar uma rota com 4 pontos ao redor do local inicial
                    # Esconder mensagens de processamento
                    
                    # Obter as coordenadas da origem
                    geocode_result = gmaps.geocode(origem)
                    if geocode_result:
                        start_lat = geocode_result[0]['geometry']['location']['lat']
                        start_lng = geocode_result[0]['geometry']['location']['lng']
                    
                    # Cálculo de 1 km em graus (aproximadamente)
                    lat_offset = 0.009  # ~1km em latitude
                    lng_offset = 0.012  # ~1km em longitude (varia com a latitude)
                    
                    # Calcular distância radial para obter aproximadamente a metade da distância total
                    distance_factor = raio_km * 0.009  # Ajustar deslocamento para distância
                    
                    # Criar 4 pontos ao redor
                    north = f"{start_lat + distance_factor},{start_lng}"
                    east = f"{start_lat},{start_lng + distance_factor}"
                    south = f"{start_lat - distance_factor},{start_lng}"
                    west = f"{start_lat},{start_lng - distance_factor}"
                    
                    # Criar rota com 2 pontos - isso geralmente resulta em um retângulo
                    directions = gmaps.directions(
                        origin=origem,
                        destination=origem,
                        waypoints=[north, east],
                        mode="bicycling",
                        optimize_waypoints=False
                    )
                # Último recurso: usar pontos conhecidos em São José dos Campos
                if not directions:
                    waypoints = [
                        "Parque Santos Dumont, São José dos Campos, SP",
                        "Parque Vicentina Aranha, São José dos Campos, SP"
                    ]
                    
                    try:
                        directions = gmaps.directions(
                            origin=origem,
                            destination=origem,
                            waypoints=waypoints,
                            mode="bicycling",
                            optimize_waypoints=False
                        )
                    except:
                        pass
            
            if not directions:
                # Tentar com menos waypoints (sem mostrar mensagem ao usuário)
                directions = gmaps.directions(
                    origin=origem,
                    destination=origem,
                    waypoints=waypoints_to_use[0:min(2, len(waypoints_to_use))],
                    mode="bicycling",
                    optimize_waypoints=False
                )
                
                if not directions:
                    # Última tentativa: apenas origem e destino sem waypoints
                    directions = gmaps.directions(
                        origin=origem,
                        destination=origem,
                        mode="bicycling"
                    )
                    
                    if not directions:
                        return "", "<p>Não foi possível gerar um roteiro para o endereço especificado.</p>", []
        except Exception as e:
            # Tentar com formato de endereço simplificado sem notificar o usuário
            
            # ⭐ Segunda tentativa com endereços simplificados
            try:
                simplified_origin = origem.split(',')[0] + ", São José dos Campos, SP"
                simplified_waypoints = [wp.split(',')[0] + ", São José dos Campos, SP" for wp in waypoints_to_use]
                
                directions = gmaps.directions(
                    origin=simplified_origin,
                    destination=simplified_origin,
                    waypoints=simplified_waypoints[0:min(2, len(simplified_waypoints))],
                    mode="bicycling",
                    optimize_waypoints=False
                )
                
                if not directions:
                    return "", "<p>Não foi possível gerar rota mesmo com endereços simplificados.</p>", []
            except Exception as e2:
                return "", f"<p>Falha ao gerar rota após múltiplas tentativas: {str(e2)}</p>", []
            
        # ⭐ Verificar se a distância está próxima da solicitada
        distancia_calculada = sum(leg['distance']['value'] for leg in directions[0]['legs'])/1000
        # Armazenar info de distância
        distance_diff = abs(distancia_calculada - distancia)
        
        # IMPORTANTE: Garantir que a rota respeite a tolerância de 2km
        # Se a diferença for maior que 2km, tentar ajustar a rota
        if distance_diff > 2.0:
            # Tentar com menos waypoints para reduzir a distância
            with st.spinner("Refinando rota para distância ideal..."):
                for num_points in range(min(2, len(waypoints_to_use)), 0, -1):
                    try:
                        simpler_directions = gmaps.directions(
                            origin=origem,
                            destination=origem,
                            waypoints=waypoints_to_use[0:num_points],
                            mode="bicycling",
                            optimize_waypoints=True  # Otimizar para reduzir distância
                        )
                        
                        if simpler_directions:
                            simpler_distance = sum(leg['distance']['value'] for leg in simpler_directions[0]['legs'])/1000
                            
                            # Se a nova distância está mais próxima do desejado, usar esta rota
                            if abs(simpler_distance - distancia) < abs(distancia_calculada - distancia):
                                directions = simpler_directions
                                distancia_calculada = simpler_distance
                        
                    except Exception:
                        pass
                    
                # Se ainda está muito fora, tentar uma rota circular simples
                if distancia_calculada > distancia * 1.3:
                    try:
                        # Calcular a distância que precisamos para um lado (metade do total)
                        half_distance = distancia / 2
                    
                        # Obter geocodificação do endereço de origem
                        try:
                            geocode_result = gmaps.geocode(origem)
                            if geocode_result:
                                start_lat = geocode_result[0]['geometry']['location']['lat']
                                start_lng = geocode_result[0]['geometry']['location']['lng']
                            
                            # Calcular fator de distância para obter aproximadamente a distância desejada
                            # Ajuste específico para 15km que foi solicitado
                            if distancia == 15:
                                factor = 0.03  # Fator específico para gerar rota de 15km
                            else:
                                # Para outras distâncias, calcular proporcionalmente
                                factor = 0.002 * distancia  # Aproximadamente 0.03 para 15km
                            
                            # Dois pontos em lados opostos para formar um circuito mais próximo de 15km
                            point_north = f"{start_lat + factor},{start_lng}"
                            point_east = f"{start_lat},{start_lng + factor}" 
                            
                            circular_route = gmaps.directions(
                                origin=origem,
                                destination=origem,
                                waypoints=[point_north, point_east],
                                mode="bicycling"
                            )
                            
                            if circular_route:
                                circular_distance = sum(leg['distance']['value'] for leg in circular_route[0]['legs'])/1000
                                
                                # Se está mais próxima do desejado, usar esta rota
                                if abs(circular_distance - distancia) < abs(distancia_calculada - distancia):
                                    directions = circular_route
                                    distancia_calculada = circular_distance
                        except Exception:
                            # Silenciosamente ignorar erros
                            pass
                            
                    except Exception:
                        # Silenciosamente ignorar erros
                        pass
        
    except Exception as e:
        st.error(f"Erro ao acessar a API do Google Maps: {str(e)}")
        return "", f"<p>Erro ao acessar a API do Google Maps: {str(e)}</p>", []
    # usamos todas as pernas
    distancia_total = sum(leg['distance']['value'] for leg in directions[0]['legs'])/1000
    distancia_total = f"{distancia_total:.1f} km"
    ruas = [ html.unescape(re.sub(r'<[^>]+>', '', step['html_instructions']))
             for leg in directions[0]['legs'] for step in leg['steps'] ]
             
    # Traduzir instruções para português usando a API OpenAI
    with st.spinner("Traduzindo instruções da rota..."):
        # Primeiro, tentar corrigir problemas comuns nas strings de origem 
        # (como mixagem de idiomas)
        ruas_corrigidas = []
        for rua in ruas:
            # Corrigir alguns erros comuns, como palavras que ficam no idioma errado
            rua_corrigida = rua.replace("Contemue", "Continue")
            rua_corrigida = rua_corrigida.replace("norteleste", "nordeste")
            rua_corrigida = rua_corrigida.replace("Destemo", "Destino")
            rua_corrigida = rua_corrigida.replace("Slight right", "Vire levemente à direita")
            rua_corrigida = rua_corrigida.replace("Slight left", "Vire levemente à esquerda")
            rua_corrigida = rua_corrigida.replace("Restricted usage road", "Estrada de uso restrito")
            ruas_corrigidas.append(rua_corrigida)
        
        # Agora, preparar o prompt para tradução
        instrucoes_texto = "\n".join(ruas_corrigidas)
        
        # Usar o modelo OpenAI para tradução
        prompt_tradutor = f"""
Traduza as seguintes instruções de rota para português brasileiro formal e correto.
IMPORTANTE: TRADUZA CADA INSTRUÇÃO COMPLETAMENTE para português, sem deixar nenhuma parte em inglês.
Mantenha nomes de ruas/locais intactos, pois são nomes próprios (ex: Av. Engenheiro Sebastião Gualberto).
Use consistência nas traduções, sempre com o mesmo formato para instruções similares.
Traduza cada linha separadamente e mantenha o mesmo número de linhas.

Mapeamento completo de termos específicos:
- "Head" → "Siga"
- "Turn right" → "Vire à direita"
- "Turn left" → "Vire à esquerda" 
- "Turn" → "Vire"
- "Continue onto" → "Continue pela"
- "Continue to follow" → "Continue seguindo pela"
- "Continue" → "Continue"
- "northeast" → "nordeste"
- "southeast" → "sudeste" 
- "northwest" → "noroeste"
- "southwest" → "sudoeste"
- "north" → "norte"
- "south" → "sul"
- "east" → "leste"
- "west" → "oeste"
- "Walk your bicycle" → "Desça da bicicleta"
- "toward" → "em direção a"
- "Pass by" → "Passe por"
- "on the right" → "à direita"
- "on the right side" → "do lado direito"
- "on the left" → "à esquerda"
- "on the left side" → "do lado esquerdo"
- "in" → "em"
- "will be on" → "estará"
- "Restricted usage road" → "Estrada de uso restrito"
- "Destination" → "Destino"
- "Slight right" → "Vire levemente à direita"
- "Slight left" → "Vire levemente à esquerda"
- "for" → "por"
- "then" → "depois"
- "Take" → "Pegue"

Texto para traduzir:
{instrucoes_texto}

Responda APENAS com a tradução, sem comentários adicionais. Não deixe NENHUMA palavra em inglês.
"""
        
        try:
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt_tradutor}],
                temperature=0.2
            )
            
            texto_traduzido = resp.choices[0].message.content.strip()
            ruas_traduzidas = [linha.strip() for linha in texto_traduzido.split('\n') if linha.strip()]
            
            # Validar resultado da tradução
            if len(ruas_traduzidas) != len(ruas):
                st.warning(f"Tradução automática resultou em número diferente de instruções (original: {len(ruas)}, traduzido: {len(ruas_traduzidas)}). Aplicando correções.")
                
                # Tentar ajustar o tamanho da lista traduzida
                if len(ruas_traduzidas) > len(ruas):
                    # Se temos mais traduções que originais, pegar apenas as primeiras
                    ruas_traduzidas = ruas_traduzidas[:len(ruas)]
                else:
                    # Se temos menos traduções, completar com traduções básicas
                    for i in range(len(ruas_traduzidas), len(ruas)):
                        rua = ruas[i]
                        # Tradução básica mais abrangente
                        rua_pt = rua.replace("Head", "Siga")
                        rua_pt = rua_pt.replace("Turn right", "Vire à direita")
                        rua_pt = rua_pt.replace("Turn left", "Vire à esquerda")
                        rua_pt = rua_pt.replace("Turn", "Vire")
                        rua_pt = rua_pt.replace("Continue onto", "Continue pela")
                        rua_pt = rua_pt.replace("Continue to follow", "Continue seguindo pela")
                        rua_pt = rua_pt.replace("Continue", "Continue")
                        rua_pt = rua_pt.replace("Walk your bicycle", "Desça da bicicleta")
                        rua_pt = rua_pt.replace("toward", "em direção a")
                        rua_pt = rua_pt.replace("Pass by", "Passe por")
                        rua_pt = rua_pt.replace("on the right", "à direita")
                        rua_pt = rua_pt.replace("on the right side", "do lado direito")
                        rua_pt = rua_pt.replace("on the left", "à esquerda")
                        rua_pt = rua_pt.replace("on the left side", "do lado esquerdo")
                        rua_pt = rua_pt.replace("in", "em")
                        rua_pt = rua_pt.replace("Destination", "Destino")
                        rua_pt = rua_pt.replace("northeast", "nordeste")
                        rua_pt = rua_pt.replace("southeast", "sudeste")
                        rua_pt = rua_pt.replace("northwest", "noroeste")
                        rua_pt = rua_pt.replace("southwest", "sudoeste")
                        rua_pt = rua_pt.replace("north", "norte")
                        rua_pt = rua_pt.replace("south", "sul")
                        rua_pt = rua_pt.replace("east", "leste")
                        rua_pt = rua_pt.replace("west", "oeste")
                        rua_pt = rua_pt.replace("Restricted usage road", "Estrada de uso restrito")
                        rua_pt = rua_pt.replace("Slight right", "Vire levemente à direita")
                        rua_pt = rua_pt.replace("Slight left", "Vire levemente à esquerda")
                        rua_pt = rua_pt.replace("for", "por")
                        rua_pt = rua_pt.replace("then", "depois")
                        rua_pt = rua_pt.replace("Take", "Pegue")
                        rua_pt = rua_pt.replace("m)", "m)")
                        ruas_traduzidas.append(rua_pt)
        except Exception as e:
            st.warning(f"Erro na tradução avançada: {str(e)}. Usando tradução básica.")
            # Fallback para tradução básica
            ruas_traduzidas = []
            for rua in ruas:
                rua_pt = rua
                # Tradução abrangente
                rua_pt = rua_pt.replace("Head", "Siga")
                rua_pt = rua_pt.replace("Turn right", "Vire à direita")
                rua_pt = rua_pt.replace("Turn left", "Vire à esquerda")
                rua_pt = rua_pt.replace("Turn", "Vire")
                rua_pt = rua_pt.replace("Continue onto", "Continue pela")
                rua_pt = rua_pt.replace("Continue to follow", "Continue seguindo pela")
                rua_pt = rua_pt.replace("Continue", "Continue")
                rua_pt = rua_pt.replace("Walk your bicycle", "Desça da bicicleta")
                rua_pt = rua_pt.replace("toward", "em direção a")
                rua_pt = rua_pt.replace("Pass by", "Passe por")
                rua_pt = rua_pt.replace("on the right", "à direita")
                rua_pt = rua_pt.replace("on the right side", "do lado direito")
                rua_pt = rua_pt.replace("on the left", "à esquerda")
                rua_pt = rua_pt.replace("on the left side", "do lado esquerdo")
                rua_pt = rua_pt.replace("in", "em")
                rua_pt = rua_pt.replace("Destination", "Destino")
                rua_pt = rua_pt.replace("northeast", "nordeste")
                rua_pt = rua_pt.replace("southeast", "sudeste")
                rua_pt = rua_pt.replace("northwest", "noroeste")
                rua_pt = rua_pt.replace("southwest", "sudoeste")
                rua_pt = rua_pt.replace("north", "norte")
                rua_pt = rua_pt.replace("south", "sul")
                rua_pt = rua_pt.replace("east", "leste")
                rua_pt = rua_pt.replace("west", "oeste")
                rua_pt = rua_pt.replace("Restricted usage road", "Estrada de uso restrito")
                rua_pt = rua_pt.replace("Slight right", "Vire levemente à direita")
                rua_pt = rua_pt.replace("Slight left", "Vire levemente à esquerda")
                rua_pt = rua_pt.replace("for", "por")
                rua_pt = rua_pt.replace("then", "depois")
                rua_pt = rua_pt.replace("Take", "Pegue")
                ruas_traduzidas.append(rua_pt)

    # Extract elevation data for the route
    elevation_data = []
    try:
        # Limitar para não sobrecarregar a API
        max_steps = 5
        step_count = 0
        
        for leg in directions[0]['legs']:
            for step in leg['steps']:
                if step_count >= max_steps:
                    break
                    
                start_loc = step['start_location']
                # Get elevation for start point
                try:
                    elevation_result = gmaps.elevation((start_loc['lat'], start_loc['lng']))
                    if elevation_result:
                        elevation_data.append({
                            'distance': len(elevation_data) * 0.5,  # Approximated distance
                            'elevation': elevation_result[0]['elevation']
                        })
                except Exception:
                    # Ignorar erros de elevação e continuar
                    pass
                
                step_count += 1
    except Exception as e:
        st.warning(f"Não foi possível obter dados de elevação: {str(e)}")

    mapa_html = f"""
<div id="map" style="height:500px; border-radius:12px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);"></div>
<script>
  function initMap() {{
    const map = new google.maps.Map(document.getElementById("map"), {{
      zoom: 14,
      center: {{ lat: {directions[0]['legs'][0]['start_location']['lat']}, lng: {directions[0]['legs'][0]['start_location']['lng']} }},
      styles: [
        {{
          "featureType": "all",
          "elementType": "labels.text.fill",
          "stylers": [{{ "color": "#ffffff" }}]
        }},
        {{
          "featureType": "all",
          "elementType": "labels.text.stroke",
          "stylers": [{{ "color": "#000000" }}, {{ "lightness": 13 }}]
        }},
        {{
          "featureType": "administrative",
          "elementType": "geometry.fill",
          "stylers": [{{ "color": "#000000" }}]
        }},
        {{
          "featureType": "administrative",
          "elementType": "geometry.stroke",
          "stylers": [{{ "color": "#144b53" }}, {{ "lightness": 14 }}, {{ "weight": 1.4 }}]
        }},
        {{
          "featureType": "landscape",
          "elementType": "all",
          "stylers": [{{ "color": "#08304b" }}]
        }},
        {{
          "featureType": "poi",
          "elementType": "geometry",
          "stylers": [{{ "color": "#0c4152" }}, {{ "lightness": 5 }}]
        }},
        {{
          "featureType": "road.highway",
          "elementType": "geometry.fill",
          "stylers": [{{ "color": "#3498db" }}]
        }},
        {{
          "featureType": "road.highway",
          "elementType": "geometry.stroke",
          "stylers": [{{ "color": "#2980b9" }}, {{ "lightness": 25 }}]
        }},
        {{
          "featureType": "road.arterial",
          "elementType": "geometry.fill",
          "stylers": [{{ "color": "#2c3e50" }}]
        }},
        {{
          "featureType": "road.arterial",
          "elementType": "geometry.stroke",
          "stylers": [{{ "color": "#0b3d51" }}, {{ "lightness": 16 }}]
        }},
        {{
          "featureType": "road.local",
          "elementType": "geometry",
          "stylers": [{{ "color": "#000000" }}]
        }},
        {{
          "featureType": "transit",
          "elementType": "all",
          "stylers": [{{ "color": "#146474" }}]
        }},
        {{
          "featureType": "water",
          "elementType": "all",
          "stylers": [{{ "color": "#021019" }}]
        }}
      ]
    }});
    const directionsService = new google.maps.DirectionsService();
    const directionsRenderer = new google.maps.DirectionsRenderer({{
      map: map,
      polylineOptions: {{
        strokeColor: '#e74c3c',
        strokeWeight: 6,
        strokeOpacity: 0.9
      }}
    }});
    directionsService.route({{
      origin: "{origem}",
      destination: "{origem}",
      waypoints: [
        // É essencial ter pelo menos um waypoint para rotas circulares
        // Calcular um ponto ao norte do ponto de partida
        {{
          location: new google.maps.LatLng(
            {directions[0]['legs'][0]['start_location']['lat'] + 0.02}, 
            {directions[0]['legs'][0]['start_location']['lng']}
          )
        }}
      ],
      travelMode: google.maps.TravelMode.BICYCLING,
      optimizeWaypoints: true,
    }}, (result, status) => {{
      if (status === "OK") directionsRenderer.setDirections(result);
      else alert("Falha na rota: " + status);
    }});
  }}
</script>
<script src="https://maps.googleapis.com/maps/api/js?key={GMAPS_KEY}&callback=initMap" async defer></script>
"""

    # A tradução já foi feita anteriormente usando OpenAI
    # Aqui, só garantimos que temos instruções traduzidas para o português

    texto = f"""
### 🗺️ Resumo da Rota  
**Origem e retorno:** {origem}  
**Distância total:** {distancia_total}  

**Passos detalhados:**  
<ol>
{''.join(f"<li>{rua}</li>" for rua in ruas_traduzidas)}
</ol>
"""
    return mapa_html, texto, elevation_data

# Funções para mudar de página
def go_to_results():
    """Muda para a página de resultados"""
    st.session_state.page = 'results'
    
def go_to_form():
    """Reinicia o aplicativo voltando para o formulário inicial"""
    # Usar nossa função robusta para reiniciar a sessão
    inicializar_sessao(reiniciar=True)
    
    # Marcar que o app foi reiniciado
    st.session_state.app_reiniciado = True

# Iniciar geração de PDF
def generate_pdf():
    try:
        if not all(k in st.session_state.data for k in ['guide', 'route', 'sensor']):
            st.warning("Dados insuficientes para gerar PDF. Tente novamente.")
            return None
        
        # Gerar PDF
        pdf_base64 = gerar_pdf_roteiro(
            st.session_state.data['guide'], 
            st.session_state.data['route'],
            st.session_state.data['sensor'],
            st.session_state.data['endereco'], 
            st.session_state.data['distancia'], 
            st.session_state.data['nivel'], 
            st.session_state.data['horario'], 
            st.session_state.data['estilo']
        )
        return pdf_base64
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {str(e)}")
        return None

# Interface principal
def main():
    # Página de Formulário
    if st.session_state.page == 'form':
        # Limpar página anterior completamente
        st.empty()
        
        st.title("🚲 Pedala SJC")
        st.write("Planejamento de rotas para ciclistas urbanos em São José dos Campos.")
        
        # Formulário para entrada de dados
        st.markdown("## Defina sua pedalada")
        col1, col2 = st.columns(2)

        with col1:
            endereco = st.text_input("Endereço de partida:", "Rua Coronel José Monteiro, 123")
            # Fixar cidade como São José dos Campos
            cidade = "São José dos Campos"
            estado = "SP"
            endereco_completo = f"{endereco}, {cidade} - {estado}"
            st.info("📍 Localização: São José dos Campos - SP")
            
            # Níveis
            nivel = st.radio("Nível de experiência:", 
                             ["Iniciante", "Intermediário", "Avançado", "Profissional"],
                             horizontal=True)
            
        with col2:
            distancia = st.slider("Distância da pedalada (km):", 
                                min_value=5, max_value=30, value=15, step=5)
            
            # Valores fixos para horário e estilo (não mais visíveis na interface)
            horario = "Manhã"  # Valor padrão
            visual_style = "urbano"  # Valor padrão
        
        # Botão para planejar pedalada
        if st.button("🚲 Planejar Pedalada", use_container_width=True):
            # Salvar dados do formulário
            st.session_state.data = {
                'endereco': endereco_completo,
                'nivel': nivel,
                'distancia': distancia,
                'horario': horario,
                'estilo': visual_style
            }
            go_to_results()
            st.rerun()
            
    # Página de Resultados
    elif st.session_state.page == 'results':
        # Limpar completamente a tela anterior
        st.empty()
        
        # Recuperar dados salvos
        data = st.session_state.data
        
        with st.spinner("1/6: Analisando sensores..."):
            rel = pedala_teste_2.executar_analise()
            dados = pedala_teste_2.dados_sensor
            
            # Salvar para uso no PDF
            st.session_state.data['sensor'] = dados
            
            # Store sensor data history for time-series chart
            st.session_state.sensor_data_history.append({
                "timestamp": datetime.now().strftime("%H:%M"),
                **dados
            })
            if len(st.session_state.sensor_data_history) > 10:
                st.session_state.sensor_data_history.pop(0)

        # exibir sensores
        st.markdown("---")
        st.markdown("<h3 style='text-align:center;'>📊 Dados Atuais dos Sensores</h3>", unsafe_allow_html=True)
        
        # Criar uma única linha com todos os sensores
        col1, col2, col3, col4 = st.columns(4, gap="small")
        
        # Mapear sensores para colunas diretamente
        cols = [col1, col2, col3, col4]
        
        # Definir dados dos sensores
        sensores = [
            ("🌡️ Temperatura", "temperatura", "°C"),
            ("💧 Umidade", "umidade", "%"),
            ("🧭 Pressão", "pressao", "hPa"),
            ("💡 Luminosidade", "luminosidade", "lux")
        ]
        
        # Exibir cada sensor em sua coluna
        for i, (label, k, u) in enumerate(sensores):
            with cols[i]:
                if k in dados:
                    v = dados[k]
                    st.markdown(
                        f"<div class='sensor-card'><strong>{label}</strong><br>"
                        f"{v:.1f} {u}<br><span class='sensor-icon'>{get_sensor_icon(k,v)}</span></div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.warning(f"Chave `{k}` não encontrada")

        # FLUXO INVERTIDO: Primeiro geramos a rota, depois o guia baseado na rota real
        
        # Etapa 1: Montar pontos da rota com base no nível do ciclista e estilo
        with st.spinner("2/6: Preparando rota personalizada..."):
            # IMPORTANTE: Para rotas curtas (≤10km), usar apenas um ponto próximo
            if data['distancia'] <= 10:
                # Para rotas curtas, independente do nível do ciclista, usar locais próximos ao centro
                # Com apenas 1 ponto para evitar rotas muito longas
                pontos_rota = [
                    "Praça Afonso Pena, São José dos Campos, SP"  # Apenas um ponto central
                ]
                st.info("⚠️ Para distância <= 10km, usando rota simplificada com apenas um ponto de referência.")
            elif data['distancia'] <= 15:
                # Para rotas médias curtas, usar dois pontos próximos
                pontos_rota = [
                    "Parque Vicentina Aranha, São José dos Campos, SP",
                    "Praça Afonso Pena, São José dos Campos, SP"
                ]
            else:
                # Para rotas mais longas, usar pontos de acordo com o nível
                if data['nivel'] == "Iniciante":
                    # Rotas mais planas, em ciclovias e parques, evitando ruas movimentadas
                    pontos_rota = [
                        "Parque Vicentina Aranha, São José dos Campos, SP",
                        "Praça Afonso Pena, São José dos Campos, SP", 
                        "Parque Santos Dumont, São José dos Campos, SP"
                    ]
                elif data['nivel'] == "Intermediário":
                    # Rotas moderadas com algumas subidas leves e ciclovias
                    pontos_rota = [
                        "Parque Santos Dumont, São José dos Campos, SP",
                        "Centro da Juventude, São José dos Campos, SP",
                        "Praça Afonso Pena, São José dos Campos, SP"
                    ]
                elif data['nivel'] == "Avançado":
                    # Rotas mais desafiadoras com subidas e descidas variadas
                    pontos_rota = [
                        "Parque Ribeirão Vermelho, São José dos Campos, SP",
                        "Parque da Cidade, São José dos Campos, SP",
                        "Parque Vicentina Aranha, São José dos Campos, SP"
                    ]
                else:  # Profissional
                    # Rotas com terrenos variados, incluindo subidas mais íngremes
                    pontos_rota = [
                        "Jardim Aquarius, São José dos Campos, SP",
                        "Banhado, São José dos Campos, SP",
                        "Urbanova, São José dos Campos, SP",
                        "Parque da Cidade, São José dos Campos, SP"
                    ]
            
            # Garantir que não passamos muitos pontos para rotas curtas ou médias
            if data['distancia'] <= 20 and len(pontos_rota) > 2:
                pontos_rota = pontos_rota[:2]  # Limitar a 2 waypoints
                
            # Etapa 2: Gerar a rota com base nos pontos de referência selecionados
            
            # NOVO TRATAMENTO ESPECIAL PARA ROTAS CURTAS (<=10km)
            if data['distancia'] <= 10:
                # Importar função especializada para rotas curtas
                try:
                    from rotas_curtas import gerar_rota_curta
                    # Não exibir a mensagem para não confundir o usuário
                    # st.info("⚠️ Usando algoritmo especializado para distâncias curtas (≤10km)")
                    
                    # Chamar função especializada para rotas curtas
                    mapa_html, texto_completo, elevation_data = gerar_rota_curta(
                        data['endereco'],
                        data['distancia']
                    )
                except Exception as e:
                    st.error(f"Erro ao usar função de rotas curtas: {str(e)}")
                    # Fallback para o método normal
                    mapa_html, texto_completo, elevation_data = gerar_rota_e_embed(
                        data['endereco'], 
                        pontos_rota, 
                        data['distancia'],
                        forcar_distancia=True
                    )
            else:
                # Método padrão para rotas maiores que 10km
                mapa_html, texto_completo, elevation_data = gerar_rota_e_embed(
                    data['endereco'], 
                    pontos_rota, 
                    data['distancia'],
                    forcar_distancia=True  # Parâmetro para forçar a distância correta
                )
            
            # Agora simplificar a rota para exibição
            try:
                from rota_simplificada import gerar_rota_simplificada
                # Fornecer a função e os dados já gerados para evitar importação circular
                _, texto_rota, _ = gerar_rota_simplificada(
                    data['endereco'], 
                    pontos_rota, 
                    data['distancia'],
                    mapa_html=mapa_html,
                    texto_completo=texto_completo,
                    elevation_data=elevation_data,
                    gerar_rota_e_embed=gerar_rota_e_embed
                )
            except Exception as e:
                # Em caso de erro na simplificação, usar o texto original
                texto_rota = texto_completo
                print(f"Erro ao simplificar rota: {e}")
            
            # Extrair distância total da rota gerada
            distancia_match = re.search(r"\*\*Distância total:\*\* (.+)", texto_rota)
            distancia_total = distancia_match.group(1) if distancia_match else f"{data['distancia']} km"
            
            # Extrair passos da rota 
            passos_rota = []
            for rua in re.findall(r"<li>(.+?)</li>", texto_rota):
                passos_rota.append(rua)
            
            # Armazenar dados da rota para uso posterior
            st.session_state.data['route'] = {
                "passos": passos_rota,
                "distancia_total": distancia_total,
                "elevation_data": elevation_data,
                "waypoints": [p.split(',')[0] for p in pontos_rota]  # Lista simplificada de pontos principais
            }
            
            # Extrair valor numérico da distância real
            try:
                distancia_real = float(distancia_total.split()[0])
            except:
                distancia_real = float(data['distancia'])
        
        # Etapa 3: Gerar o guia baseado na rota real calculada
        with st.spinner("3/6: Criando guia personalizado para a rota..."):
            # Usar a nova função que gera o guia com base na rota calculada
            guia_texto = gerar_guia_com_rota(
                rel, 
                data['nivel'], 
                distancia_real, 
                data['endereco'], 
                data['horario'], 
                data['estilo'],
                st.session_state.data['route']
            )
            
            # Salvar o guia para uso posterior
            st.session_state.data['guide'] = guia_texto
            
            # Mostrar o cabeçalho do guia com design atrativo
            st.markdown("<h3 style='text-align:center; background-color:#4682b4; color:#ffffff; padding:12px; border-radius:10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);'>📝 GUIA PERSONALIZADO DA PEDALADA</h3>", unsafe_allow_html=True)
            
            # Container para exibir o guia com design melhorado
            guia_container = st.container()
            with guia_container:
                # Processamos o texto markdown para HTML mantendo a formatação correta
                import markdown
                
                # Remover quaisquer símbolos # soltos que não sejam parte de cabeçalhos 
                guia_texto_limpo = re.sub(r'\n#\s*\n', '\n<hr>\n', guia_texto)
                
                # Converter o markdown para HTML 
                html_body = markdown.markdown(guia_texto_limpo)
                
                # Adicionar estilo CSS para garantir boa legibilidade
                guia_html = f"""
                <div style="background-color:#f9f9f9; border-radius:12px; padding:20px; border-left:5px solid #4682b4; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <style>
                        .guia-container h1 {{ color: #2c3e50; margin-top: 20px; margin-bottom: 15px; font-size: 1.8em; }}
                        .guia-container h2 {{ color: #2c3e50; margin-top: 18px; margin-bottom: 12px; font-size: 1.5em; }}
                        .guia-container h3 {{ color: #34495e; margin-top: 15px; margin-bottom: 10px; font-size: 1.3em; }}
                        .guia-container p {{ color: #333333; line-height: 1.6; margin-bottom: 15px; font-size: 1.1em; }}
                        .guia-container ul {{ color: #333333; padding-left: 25px; margin-bottom: 15px; }}
                        .guia-container li {{ margin-bottom: 8px; line-height: 1.5; }}
                        .guia-container strong {{ color: #2c3e50; font-weight: 700; }}
                    </style>
                    <div class="guia-container">
                        {html_body}
                    </div>
                </div>
                """
                
                st.markdown(guia_html, unsafe_allow_html=True)

        # exibir mapa
        with st.spinner("4/6: Renderizando mapa e detalhes..."):
            st.markdown("---")
            st.markdown("## 📍 Roteiro no Mapa")
            
            if has_gmaps:
                components.html(mapa_html, height=520)
                st.markdown(texto_rota, unsafe_allow_html=True)
                
                # Generate route elevation chart
                if elevation_data:
                    st.markdown("### 📊 Perfil de Elevação da Rota")
                    elevation_chart = generate_route_elevation_chart(elevation_data)
                    components.html(elevation_chart, height=300)
            else:
                st.warning("⚠️ Mapa indisponível sem a chave do Google Maps API. Adicione a chave GOOGLE_MAPS_API_KEY nas variáveis de ambiente.")
                
                # Exibir os passos da rota pelo menos
                st.markdown("### 📝 Passos Sugeridos:")
                for i, passo in enumerate(pontos_rota, 1):
                    st.markdown(f"{i}. {passo}")
                    
                # Criar um gráfico simulado de elevação
                st.markdown("### 📊 Perfil de Elevação Simulado")
                simulated_elevation = [
                    {"distance": i, "elevation": 100 + 20 * random.randint(-5, 5)} 
                    for i in range(10)
                ]
                elevation_chart = generate_route_elevation_chart(simulated_elevation)
                components.html(elevation_chart, height=300)
        
        # Adicionar botões de ação - Mais destacados e fáceis de localizar
        st.markdown("---")
        st.markdown("<h3 style='text-align:center;'>📝 Ações Disponíveis</h3>", unsafe_allow_html=True)
        
        # Criar container com espaçamento para os botões
        st.markdown("""
        <style>
        .big-button {
            background-color: #2e86de;
            color: white;
            padding: 15px 24px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 10px;
            margin: 15px 0;
            text-align: center;
            cursor: pointer;
            display: block;
            width: 100%;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transition: all 0.3s;
        }
        .big-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        }
        .big-button.green {
            background-color: #2ecc71;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Coluna para os botões
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            if st.button("🔄 Reiniciar Aplicativo", use_container_width=True, key="restart_button", help="Limpa tudo e começa um novo plano"):
                # Usar a nova função robusta para reiniciar completamente
                go_to_form()
                # Forçar o recarregamento completo da página
                st.rerun()
        
        with col2:
            if st.button("📄 Gerar PDF do Roteiro", use_container_width=True, key="pdf_button", help="Gera um PDF com todas as informações do roteiro"):
                with st.spinner("Gerando PDF do roteiro..."):
                    pdf_data = generate_pdf()
                    if pdf_data:
                        # Criar link de download
                        st.markdown(
                            f'<a href="data:application/octet-stream;base64,{pdf_data}" download="roteiro_pedalada.pdf" class="pdf-link">📥 Clique aqui para baixar o PDF do seu roteiro de pedalada</a>', 
                            unsafe_allow_html=True
                        )
                        st.success("PDF gerado com sucesso! Clique no link acima para fazer o download.")

    # Rodapé em todas as páginas
    st.markdown("---")
    st.caption("🚲 Desenvolvido para a comunidade ciclística urbana de São José dos Campos.")

if __name__ == "__main__":
    main()