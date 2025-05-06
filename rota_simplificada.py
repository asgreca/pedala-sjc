import re
import html
import os
import googlemaps
from openai import OpenAI

# Evitar importação de Streamlit para não causar erro de configuração de página
def gerar_rota_simplificada(origem, passos, distancia=15, mapa_html=None, texto_completo=None, elevation_data=None, gerar_rota_e_embed=None):
    """
    Versão simplificada da função gerar_rota_e_embed que mostra apenas pontos principais
    
    Args:
        origem (str): Endereço de origem
        passos (list): Lista de pontos de referência
        distancia (int): Distância desejada
        mapa_html (str): HTML do mapa (se já gerado)
        texto_completo (str): Texto da rota (se já gerado) 
        elevation_data (list): Dados de elevação (se já gerados)
        gerar_rota_e_embed (callable): Função de geração de rota
        
    Returns:
        tuple: HTML do mapa, texto simplificado da rota, dados de elevação
    """
    try:
        # Evitar importações circulares
        if mapa_html is None or texto_completo is None or elevation_data is None:
            if gerar_rota_e_embed is None:
                # Não podemos continuar sem a função ou os dados
                return "", "<p>Erro: Função de geração de rota não fornecida</p>", []
            
            # Recuperar as chaves e criar clientes
            GMAPS_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
            gmaps = googlemaps.Client(key=GMAPS_KEY)
            
            # Usar a função fornecida para gerar a rota
            mapa_html, texto_completo, elevation_data = gerar_rota_e_embed(origem, passos, distancia)
        
        # Extrair as ruas do texto completo
        ruas_padrao = r'<li>(.*?)</li>'
        ruas_traduzidas = re.findall(ruas_padrao, texto_completo)
        
        # Extrair apenas as principais vias/ruas da rota
        vias_principais = []
        
        for rua in ruas_traduzidas:
            # Procurar menções a ruas, avenidas e praças
            if "R. " in rua or "Rua " in rua or "Av. " in rua or "Avenida " in rua or "Pça" in rua or "Praça" in rua:
                # Extrair a parte que menciona a via
                for palavra in rua.split():
                    if palavra in ["R.", "Rua", "Av.", "Avenida", "Pça.", "Praça"]:
                        inicio = rua.find(palavra)
                        if inicio >= 0:
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
        
        # Se não encontrou vias principais, usar as primeiras 5 instruções simplificadas
        if not vias_principais and ruas_traduzidas:
            vias_principais = [rua.split(" em direção")[0].split(" após")[0] for rua in ruas_traduzidas[:5]]
        
        # Extrair distância e origem do texto original
        distancia_padrao = r'Distância total:\*\* (.*?)\s'
        distancia_match = re.search(distancia_padrao, texto_completo)
        
        if distancia_match:
            distancia_total = distancia_match.group(1)
        else:
            distancia_total = f"{distancia} km (aprox.)"
            
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
        # Não usar st.error para evitar importação de streamlit
        erro_msg = f"Erro ao gerar resumo simplificado: {str(e)}"
        print(erro_msg)  # Usar print para debug
        
        # Se houve erro e gerar_rota_e_embed foi fornecido, tentar usar diretamente
        if gerar_rota_e_embed is not None:
            try:
                return gerar_rota_e_embed(origem, passos, distancia)
            except Exception as e2:
                erro_msg = f"Não foi possível gerar rota: {str(e2)}"
                print(erro_msg)
                
        # Retornar erro genérico se tudo falhar
        return "", f"<p>Não foi possível gerar rota: {str(e)}</p>", []