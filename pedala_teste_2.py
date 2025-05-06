from datetime import datetime
import os
import faiss
import pickle
import numpy as np
import json
import locale
from dotenv import load_dotenv
from openai import OpenAI
import requests
import gdown
import tempfile

# Carrega variáveis de ambiente
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# URLs dos arquivos FAISS no Google Drive
INDEX_URL = "https://drive.google.com/file/d/1cs4c3Uwvn1sEyG4_Dc8rkscJeaxeh4TO/view?usp=share_link"
PKL_URL = "https://drive.google.com/file/d/1YT_OgYIzPh9P72cLhtEeLDnkxYKov6Ku/view?usp=share_link"

# Caminhos locais para salvar os arquivos baixados
ARQUIVO_INDEX = os.path.join(os.path.dirname(__file__), 'vetor_univesp.index')
ARQUIVO_META = os.path.join(os.path.dirname(__file__), 'vetor_univesp.pkl')

def download_file_from_google_drive(url, output_path):
    """Baixa arquivos do Google Drive usando gdown."""
    try:
        gdown.download(url, output_path, quiet=False, fuzzy=True)
        return True
    except Exception as e:
        print(f"Erro ao baixar arquivo: {e}")
        return False

# Tenta baixar e carregar índice FAISS e metadados, ou cria um modelo simulado se não conseguir
try:
    # Baixa os arquivos se eles não existirem localmente
    if not os.path.exists(ARQUIVO_INDEX):
        print(f"Baixando arquivo de índice FAISS de {INDEX_URL}")
        download_success = download_file_from_google_drive(INDEX_URL, ARQUIVO_INDEX)
        if not download_success:
            raise Exception("Não foi possível baixar o arquivo de índice")
    
    if not os.path.exists(ARQUIVO_META):
        print(f"Baixando arquivo de metadados FAISS de {PKL_URL}")
        download_success = download_file_from_google_drive(PKL_URL, ARQUIVO_META)
        if not download_success:
            raise Exception("Não foi possível baixar o arquivo de metadados")
    
    # Carrega os arquivos
    index = faiss.read_index(ARQUIVO_INDEX)
    with open(ARQUIVO_META, 'rb') as f:
        metadados = pickle.load(f)
    
    print("Arquivos FAISS carregados com sucesso!")
    
except Exception as e:
    # Cria um índice FAISS simples para simulação
    print(f"Erro ao carregar arquivos FAISS: {e}")
    print("Criando índice simulado.")
    dimension = 1536  # Dimensão dos embeddings da OpenAI
    index = faiss.IndexFlatL2(dimension)
    metadados = [
        """Data: 15/05/2023, Hora: 10:30, Temperatura: 22.5°C, Umidade: 65%, Pressão: 1013.2 hPa, Luminosidade: 680 lux.
        Condições ideais para ciclismo, com céu parcialmente nublado proporcionando boa visibilidade.
        """,
        """Data: 20/06/2023, Hora: 15:45, Temperatura: 28.3°C, Umidade: 48%, Pressão: 1010.5 hPa, Luminosidade: 850 lux.
        Clima quente mas com umidade moderada, recomendada hidratação frequente durante o percurso.
        """,
        """Data: 05/07/2023, Hora: 08:15, Temperatura: 18.2°C, Umidade: 75%, Pressão: 1015.8 hPa, Luminosidade: 450 lux.
        Manhã com neblina leve, visibilidade reduzida em algumas áreas mais baixas da cidade.
        """,
        """Data: 10/08/2023, Hora: 17:30, Temperatura: 24.1°C, Umidade: 55%, Pressão: 1012.3 hPa, Luminosidade: 380 lux.
        Final de tarde com condições agradáveis, vento leve de sudeste favorecendo percursos na direção norte.
        """,
        """Data: 22/09/2023, Hora: 12:00, Temperatura: 26.8°C, Umidade: 45%, Pressão: 1009.7 hPa, Luminosidade: 920 lux.
        Meio-dia com sol forte, recomendado uso de protetor solar e óculos de proteção UV.
        """
    ]
    # Criamos embeddings simulados para cada metadado
    dummy_embeddings = np.random.random((len(metadados), dimension)).astype('float32')
    index.add(dummy_embeddings)

# Variáveis globais para uso externo
data = ""
dados_sensor = {}

def executar_analise():
    global data, dados_sensor

    dt = datetime.now()
    data_hora = dt.strftime("%d/%m/%Y %H:%M")
    data = dt.strftime("%d/%m/%Y")

    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
        dia_semana = dt.strftime('%A').capitalize()
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'pt_BR')
            dia_semana = dt.strftime('%A').capitalize()
        except:
            dia_semana = "Indefinido"

    relatorio_completo = ""
    relatorio_completo += f"🚲 **Relatório de Análise de Pedalada** 🚲\n"
    relatorio_completo += f"📅 Data/Hora: {data_hora} ({dia_semana})\n\n"

    # === Simula sensores com LLM ===
    prompt = """Gere dados aleatórios realistas para sensores em São José dos Campos. 
    Retorne um JSON com:
    - "temperatura": valor em °C (float)
    - "umidade": percentual (float)
    - "pressao": valor em hPa (float)
    - "luminosidade": valor em lux (float)"""

    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Você é um gerador de dados de sensores."},
                {"role": "user", "content": prompt}
            ]
        )
        sensor_data = json.loads(response.choices[0].message.content)

        temperatura = float(sensor_data['temperatura'])
        umidade = float(sensor_data['umidade'])
        pressao = float(sensor_data['pressao'])
        luminosidade = float(sensor_data['luminosidade'])

        dados_sensor = {
            "data_hora": data_hora,
            "temperatura": temperatura,
            "umidade": umidade,
            "pressao": pressao,
            "luminosidade": luminosidade,
            "hora_num": round(dt.hour + dt.minute / 60, 2)
        }

        relatorio_completo += "🌡️ **Dados dos Sensores**:\n"
        relatorio_completo += f"- Temperatura: {temperatura}°C\n"
        relatorio_completo += f"- Umidade: {umidade}%\n"
        relatorio_completo += f"- Pressão: {pressao} hPa\n"
        relatorio_completo += f"- Luminosidade: {luminosidade} lux\n\n"

    except Exception as e:
        relatorio_completo += f"❌ Erro na geração de dados: {e}\n"
        return relatorio_completo

    # === Busca FAISS ===
    texto_consulta = (
        f"Temperatura: {temperatura}°C, Umidade: {umidade}%, "
        f"Pressão: {pressao} hPa, Luminosidade: {luminosidade} lux, "
        f"Hora_num: {dados_sensor['hora_num']}"
    )

    try:
        def gerar_embedding(texto: str) -> np.ndarray:
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = client.embeddings.create(
                input=[texto],
                model="text-embedding-ada-002"
            )
            return np.array(response.data[0].embedding, dtype='float32')

        vetor = gerar_embedding(texto_consulta)
        vetor = np.expand_dims(vetor, axis=0)
        distancias, indices = index.search(vetor, 5)
        similares = [metadados[i] for i in indices[0]]

        relatorio_completo += "🔍 **Registros Históricos Similares**:\n"
        registros_texto = ""
        for i, item in enumerate(similares, 1):
            registros_texto += f"\n🔹 Registro {i}:\n{item.strip()}\n"
        relatorio_completo += registros_texto + "\n"

    except Exception as e:
        relatorio_completo += f"\n❌ Erro na busca FAISS: {e}\n"
        return relatorio_completo

    # === Análise com LLM ===
    prompt_analise = f"""
Você é um especialista em clima e ciclismo urbano de São José dos Campos.

📌 Dados atuais:
- Data/Hora: {data_hora}
- Dia da semana: {dia_semana}
- Temperatura: {temperatura}°C
- Umidade: {umidade}%
- Pressão: {pressao} hPa
- Luminosidade: {luminosidade} lux

Registros históricos similares:
{registros_texto}

🧠 Tarefa:
1. Analise comparativa com histórico
2. Avalie segurança para pedalar
3. Considere finais de semana/feriados
4. Recomendação prática e responsável
"""

    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Especialista em clima e ciclismo urbano."},
                {"role": "user", "content": prompt_analise}
            ]
        )
        analise_final = resposta.choices[0].message.content.strip()
        relatorio_completo += "🧠 **Análise Final e Recomendação**:\n"
        relatorio_completo += analise_final + "\n"

    except Exception as e:
        relatorio_completo += f"\n❌ Erro na geração da análise final: {e}\n"

    return relatorio_completo
