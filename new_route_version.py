import streamlit as st
import re
import html
from openai import OpenAI
import os
import googlemaps

def gerar_rota_e_embed_simplificada(origem, passos, distancia=15):
    """
    Versão simplificada da função gerar_rota_e_embed que retorna apenas os principais pontos
    
    Args:
        origem (str): Endereço de origem
        passos (list): Lista de pontos de referência
        distancia (int): Distância desejada
        
    Returns:
        tuple: HTML do mapa, texto simplificado da rota, dados de elevação
    """
    # Configurações iniciais
    GMAPS_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    gmaps = googlemaps.Client(key=GMAPS_KEY)
    
    # Código da função original para gerar a rota...
    # [Copiar o código principal da função original]
    
    # Modificar apenas a parte final para retornar resumo simplificado
    try:
        # Extrair apenas as principais vias/ruas da rota
        vias_principais = []
        
        for rua in ruas_traduzidas:
            # Procurar menções a ruas, avenidas e praças
            if "R. " in rua or "Rua " in rua or "Av. " in rua or "Avenida " in rua or "Pça. " in rua or "Praça " in rua:
                # Extrair a parte que menciona a via
                for palavra in rua.split():
                    if palavra in ["R.", "Rua", "Av.", "Avenida", "Pça.", "Praça"]:
                        inicio = rua.find(palavra)
                        # Extrair a via (até 4 palavras após o tipo da via)
                        partes = rua[inicio:].split()
                        via = " ".join(partes[:min(5, len(partes))])
                        
                        # Limpar instruções adicionais
                        via = via.split(" em direção")[0]
                        via = via.split(" após")[0]
                        via = via.split(" Passe por")[0]
                        
                        # Adicionar apenas se for única
                        if via not in vias_principais and len(via) > 5:
                            vias_principais.append(via)
        
        # Limitar a quantidade para não sobrecarregar
        vias_principais = vias_principais[:8]
        
        # Se não encontrou vias principais, usar as primeiras 5 instruções
        if not vias_principais and ruas_traduzidas:
            vias_principais = [rua for rua in ruas_traduzidas[:5]]
        
        # Criar texto simplificado
        texto = f"""
### 🗺️ Resumo da Rota  
**Origem e retorno:** {origem}  
**Distância total:** {distancia_total}  

**Principais vias da rota:**  
<ol>
{''.join(f"<li>{via}</li>" for via in vias_principais)}
</ol>
"""
        return mapa_html, texto, elevation_data
        
    except Exception as e:
        st.error(f"Erro ao gerar resumo simplificado: {str(e)}")
        return mapa_html, texto_original, elevation_data