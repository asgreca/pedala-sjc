"""
Módulo para gerar arquivos PDF dos roteiros de pedalada
"""
import os
import base64
import re
from datetime import datetime
from fpdf import FPDF

# Função para remover emojis e caracteres não-ASCII
def limpar_texto(texto):
    """Remove emojis e caracteres especiais incompatíveis com FPDF"""
    if not texto:
        return ""
        
    # Expressão regular para remover emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # símbolos e pictogramas
        "\U0001F680-\U0001F6FF"  # transportes e mapas
        "\U0001F700-\U0001F77F"  # alembic
        "\U0001F780-\U0001F7FF"  # caracteres geométricos
        "\U0001F800-\U0001F8FF"  # símbolos miscelâneos
        "\U0001F900-\U0001F9FF"  # emojis suplementares
        "\U0001FA00-\U0001FA6F"  # símbolos adicionais
        "\U0001FA70-\U0001FAFF"  # emojis adicionais
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251" 
        "]", flags=re.UNICODE
    )
    
    # Substituir emojis por descrições
    texto = emoji_pattern.sub(r'', texto)
    
    # Substituir alguns emojis comuns por texto
    emoji_mapeamento = {
        '🚲': '[BIKE]',
        '🔥': '[FOGO]',
        '🌧️': '[CHUVA]',
        '☀️': '[SOL]',
        '🌤️': '[SOL-NUVEM]',
        '🌈': '[ARCO-IRIS]',
        '💧': '[GOTA]',
        '🚵': '[CICLISTA]',
        '🚴‍♀️': '[CICLISTA]',
        '🚴‍♂️': '[CICLISTA]',
        '🏆': '[TROFEU]',
        '📍': '[PONTO]',
        '🔧': '[FERRAMENTA]',
        '💪': '[FORTE]',
        '🌟': '[ESTRELA]',
        '😎': '[LEGAL]',
        '🏙️': '[CIDADE]',
        '🌄': '[MONTANHA]',
        '🌊': '[ONDA]',
        '🌡️': '[TERMOMETRO]',
        '😜': '[PISCADA]'
    }
    
    for emoji, descricao in emoji_mapeamento.items():
        texto = texto.replace(emoji, descricao)
    
    # Remover outros caracteres não-ASCII
    texto = re.sub(r'[^\x00-\x7F]+', '', texto)
    
    return texto

class RoteiroPDF(FPDF):
    """Classe para gerar PDF do roteiro de pedalada"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self.set_font("Arial", "B", 20)
        
    def header(self):
        """Cabeçalho personalizado"""
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Pedala SJC - Roteiro de Pedalada", 0, 1, "C")
        self.ln(5)
        
    def footer(self):
        """Rodapé personalizado"""
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", 0, 0, "C")
        self.cell(0, 10, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 0, "R")
        
    def titulo(self, texto):
        """Adiciona um título ao PDF"""
        texto_limpo = limpar_texto(texto)
        self.set_font("Arial", "B", 16)
        self.ln(5)
        self.cell(0, 10, texto_limpo, 0, 1, "L")
        self.ln(2)
        
    def subtitulo(self, texto):
        """Adiciona um subtítulo ao PDF"""
        texto_limpo = limpar_texto(texto)
        self.set_font("Arial", "B", 12)
        self.cell(0, 8, texto_limpo, 0, 1, "L")
        self.ln(2)
        
    def texto(self, texto):
        """Adiciona um texto normal ao PDF"""
        texto_limpo = limpar_texto(texto)
        self.set_font("Arial", "", 11)
        self.multi_cell(0, 5, texto_limpo)
        self.ln(3)
        
    def lista_numerada(self, items):
        """Adiciona uma lista numerada ao PDF"""
        self.set_font("Arial", "", 11)
        for i, item in enumerate(items, 1):
            item_limpo = limpar_texto(item)
            self.cell(10, 8, f"{i}.", 0, 0)
            self.multi_cell(0, 8, item_limpo)
            
    def adicionar_dados_sensores(self, dados):
        """Adiciona os dados dos sensores ao PDF"""
        self.titulo("Condições Ambientais")
        
        temperatura_valor = None
        
        # Extrair os valores para o PDF
        if "temperatura" in dados:
            temperatura_valor = dados['temperatura']
            self.texto(f"Temperatura: {dados['temperatura']:.1f} °C")
        if "umidade" in dados:
            self.texto(f"Umidade: {dados['umidade']:.1f} %")
        if "pressao" in dados:
            self.texto(f"Pressão: {dados['pressao']:.1f} hPa")
        if "luminosidade" in dados:
            self.texto(f"Luminosidade: {dados['luminosidade']:.1f} lux")
        
        # Adicionar análise da temperatura com histórico
        if temperatura_valor is not None:
            self.subtitulo("Análise Climática Histórica")
            try:
                from pedala_teste_2 import comparar_temperatura_historica
                analise = comparar_temperatura_historica(temperatura_valor)
                
                if analise["status"] == "dentro":
                    self.texto(f"A temperatura atual de {analise['temperatura_atual']:.1f}°C está dentro da faixa histórica para este mês.")
                    self.texto(f"Mínima histórica: {analise['min_historica']}°C")
                    self.texto(f"Máxima histórica: {analise['max_historica']}°C")
                    self.texto(f"Está {analise['diferenca']:.1f}°C distante da média histórica de {analise['media_historica']}°C.")
                elif analise["status"] == "acima":
                    self.texto(f"ATENÇÃO: A temperatura atual de {analise['temperatura_atual']:.1f}°C está {analise['diferenca']:.1f}°C ACIMA da máxima histórica de {analise['max_historica']}°C para este mês.")
                    self.texto(f"Isso representa {analise['percentual']}% acima do normal, exigindo cuidados extras com hidratação.")
                else:  # abaixo
                    self.texto(f"AVISO: A temperatura atual de {analise['temperatura_atual']:.1f}°C está {analise['diferenca']:.1f}°C ABAIXO da mínima histórica de {analise['min_historica']}°C para este mês.")
                    self.texto(f"Isso representa {analise['percentual']}% abaixo do normal, recomendando vestimenta adequada.")
            except Exception as e:
                self.texto("Não foi possível obter análise climatológica histórica.")
            
        self.ln(5)


def gerar_pdf_roteiro(guia, rota, dados_sensor, endereco, distancia, nivel, horario, estilo):
    """
    Gera um PDF com o roteiro de pedalada
    
    Args:
        guia (str): Guia gerado pelo OpenAI
        rota (dict): Informações da rota (passos, distância)
        dados_sensor (dict): Dados dos sensores ambientais
        endereco (str): Endereço de partida
        distancia (int): Distância planejada
        nivel (str): Nível do ciclista
        horario (str): Horário da pedalada
        estilo (str): Estilo visual escolhido
        
    Returns:
        str: Base64 do PDF para download pelo navegador
    """
    # Criar PDF
    pdf = RoteiroPDF()
    
    # Informações gerais
    pdf.titulo("Informações da Pedalada")
    pdf.texto(f"Endereço de partida: {endereco}")
    pdf.texto(f"Distância planejada: {distancia} km")
    pdf.texto(f"Nível do ciclista: {nivel}")
    pdf.texto(f"Horário preferido: {horario}")
    pdf.texto(f"Estilo de rota: {estilo}")
    pdf.ln(10)
    
    # Dados dos sensores
    pdf.adicionar_dados_sensores(dados_sensor)
    
    # Guia gerado pelo OpenAI
    pdf.titulo("Guia da Pedalada")
    pdf.texto(guia)
    pdf.ln(10)
    
    # Rota
    pdf.titulo("Roteiro no Mapa")
    pdf.texto(f"Origem e retorno: {endereco}")
    
    # Obter a distância real da rota
    distancia_real = "Desconhecida"
    if "distancia_total" in rota and rota["distancia_total"]:
        distancia_real = rota["distancia_total"]
    pdf.texto(f"Distância total: {distancia_real}")
    
    # Adicionar passos da rota
    pdf.subtitulo("Passos detalhados:")
    if "passos" in rota and rota["passos"]:
        pdf.lista_numerada(rota["passos"])
    
    # Salvar o PDF em memória
    pdf_output = f"roteiro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(pdf_output)
    
    # Converter para base64 para download
    with open(pdf_output, "rb") as pdf_file:
        encoded = base64.b64encode(pdf_file.read()).decode('utf-8')
    
    # Remover arquivo temporário
    try:
        os.remove(pdf_output)
    except:
        pass
        
    return encoded