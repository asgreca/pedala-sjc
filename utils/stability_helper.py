"""
Módulo para gerar imagens usando a API da Stability AI
"""
import os
import requests
import base64
import json
import streamlit as st
from io import BytesIO
from PIL import Image

def generate_cartoon_image(prompt, style="cartoon"):
    """
    Gera uma imagem estilo cartoon usando a API da Stability AI
    
    Args:
        prompt (str): Descrição do que deve ser gerado na imagem
        style (str): Estilo da imagem (cartoon, realistic, etc)
        
    Returns:
        str: Base64 da imagem gerada ou None se falhar
    """
    # Verificar se temos a chave da API
    STABILITY_API_KEY = os.environ.get('STABILITY_API_KEY')
    if not STABILITY_API_KEY:
        st.warning("⚠️ Chave da API da Stability AI não configurada!")
        return None
    
    try:
        # Adicionar estilo ao prompt
        if style == "cartoon":
            enhanced_prompt = f"Cartoon style illustration, transparent background, clean colorful vector art: {prompt}"
        else:
            enhanced_prompt = prompt
            
        # Configurar a requisição para a API (endpoint para Stable Diffusion XL)
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Corpo da requisição com parâmetros suportados
        payload = {
            "text_prompts": [
                {"text": enhanced_prompt, "weight": 1}
            ],
            "cfg_scale": 7,
            "height": 512,
            "width": 512,
            "samples": 1,
            "steps": 30,
            "style_preset": "cartoon"
        }
        
        # Fazer a requisição para a API
        response = requests.post(url, headers=headers, json=payload)
        
        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Extrair o base64 da imagem
            data = response.json()
            if 'artifacts' in data and len(data['artifacts']) > 0:
                image_base64 = data['artifacts'][0]['base64']
                return image_base64
        else:
            st.error(f"Erro ao gerar imagem: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        st.error(f"Erro ao gerar imagem: {str(e)}")
        return None
        
def base64_to_image(base64_str):
    """
    Converte uma string base64 para uma imagem PIL
    
    Args:
        base64_str (str): String base64 da imagem
        
    Returns:
        PIL.Image: Objeto imagem ou None se falhar
    """
    try:
        image_data = base64.b64decode(base64_str)
        image = Image.open(BytesIO(image_data))
        return image
    except Exception as e:
        st.error(f"Erro ao converter base64 para imagem: {str(e)}")
        return None

def save_image(base64_str, filename):
    """
    Salva uma imagem base64 em um arquivo
    
    Args:
        base64_str (str): String base64 da imagem
        filename (str): Nome do arquivo para salvar
        
    Returns:
        bool: True se sucesso, False se falha
    """
    try:
        image = base64_to_image(base64_str)
        if image:
            image.save(filename)
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao salvar imagem: {str(e)}")
        return False

def generate_cycling_guide_image(guide_text, perfil="Intermediário", estilo="urbano"):
    """
    Gera uma imagem para o guia de ciclismo com base no texto e perfil
    
    Args:
        guide_text (str): Texto do guia com dicas de ciclismo
        perfil (str): Perfil do ciclista (Iniciante, Intermediário, etc)
        estilo (str): Estilo de pedalada (urbano, montanha, etc)
        
    Returns:
        str: Base64 da imagem gerada ou None se falhar
    """
    # Extrair palavras-chave do guia
    palavras_chave = extract_keywords(guide_text)
    
    # Criar prompt base com base no perfil e estilo
    base_prompts = {
        "Iniciante": "Beginner cyclist enjoying a relaxed bike ride",
        "Intermediário": "Confident cyclist riding through scenic routes",
        "Avançado": "Experienced cyclist in professional gear",
        "Profissional": "Professional cyclist in racing position"
    }
    
    style_prompts = {
        "urbano": "in urban city environment with buildings",
        "montanha": "on mountain trails with scenic views",
        "parques": "through beautiful parks with trees and nature",
        "familiar": "with family, safe bike path with children"
    }
    
    # Construir prompt completo
    base_prompt = base_prompts.get(perfil, base_prompts["Intermediário"])
    style_prompt = style_prompts.get(estilo, style_prompts["urbano"])
    
    # Adicionar palavras-chave do guia
    keyword_prompt = ", ".join(palavras_chave[:5])  # Limitar a 5 palavras-chave
    
    final_prompt = f"{base_prompt} {style_prompt}, {keyword_prompt}, cheerful colors, São José dos Campos, bright daylight"
    
    # Gerar a imagem
    return generate_cartoon_image(final_prompt)
    
def extract_keywords(text, max_keywords=5):
    """
    Extrai palavras-chave de um texto
    
    Args:
        text (str): Texto para extrair palavras-chave
        max_keywords (int): Número máximo de palavras-chave
        
    Returns:
        list: Lista de palavras-chave
    """
    # Lista de palavras-chave importantes para ciclismo
    cycling_keywords = [
        "ciclista", "bicicleta", "pedalada", "rota", "trilha", 
        "montanha", "parque", "urbano", "familiar", "segurança",
        "capacete", "equipamento", "hidratação", "manhã", "tarde",
        "sol", "chuva", "clima", "elevação", "distância"
    ]
    
    # Fazer parsing do texto e encontrar palavras-chave
    found_keywords = []
    text_lower = text.lower()
    
    for keyword in cycling_keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
            if len(found_keywords) >= max_keywords:
                break
    
    # Se não encontrou palavras suficientes, adicionar algumas genéricas
    if len(found_keywords) < 3:
        default_keywords = ["ciclismo", "pedalada", "São José dos Campos"]
        for kw in default_keywords:
            if kw not in found_keywords:
                found_keywords.append(kw)
                if len(found_keywords) >= max_keywords:
                    break
    
    return found_keywords