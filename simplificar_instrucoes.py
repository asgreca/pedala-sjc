def simplificar_instruções_rota(ruas_traduzidas):
    """
    Simplifica as instruções da rota para mostrar apenas pontos principais
    
    Args:
        ruas_traduzidas (list): Lista de instruções completas da rota
        
    Returns:
        list: Lista de principais vias/pontos da rota
    """
    ruas_simplificadas = []
    ruas_principais = []
    
    for rua in ruas_traduzidas:
        # Verificar se é uma instrução que menciona uma avenida, rua ou praça importante
        if "Av. " in rua or "Avenida " in rua or "R. " in rua or "Rua " in rua or "Pça " in rua or "Praça " in rua:
            # Simplificar a instrução para mostrar apenas o essencial
            partes = rua.split(" em direção ")
            partes = partes[0].split(" após ")
            partes = partes[0].split(" Passe por ")
            
            # Limpar e adicionar
            instrucao_simplificada = partes[0].strip()
            
            # Remover instruções duplicadas ou muito similares
            if instrucao_simplificada not in ruas_simplificadas:
                ruas_simplificadas.append(instrucao_simplificada)
                
                # Identificar as vias principais para o resumo
                if "Av. " in instrucao_simplificada or "Avenida " in instrucao_simplificada or "R. " in instrucao_simplificada or "Rua " in instrucao_simplificada:
                    for parte in instrucao_simplificada.split():
                        if parte.startswith(("Av.", "Avenida", "R.", "Rua", "Pça", "Praça")):
                            via_principal = parte
                            # Tentar capturar o nome completo da via
                            indice = instrucao_simplificada.find(via_principal)
                            if indice >= 0:
                                resto = instrucao_simplificada[indice + len(via_principal):].strip()
                                palavras_nome = resto.split(" ")[0:3]  # Pegar até 3 palavras para o nome
                                nome_via = via_principal + " " + " ".join([p for p in palavras_nome if not p.startswith("(") and not p.endswith(")")])
                                if nome_via not in ruas_principais and len(nome_via) > 5:
                                    ruas_principais.append(nome_via)
    
    # Remover duplicatas e limitar a quantidade de pontos principais
    ruas_principais = list(dict.fromkeys(ruas_principais))[:7]  # Limitar a 7 pontos principais
    
    # Se não conseguir extrair ruas principais, retornar as primeiras instruções simplificadas
    if not ruas_principais and ruas_simplificadas:
        return ruas_simplificadas[:5]
        
    return ruas_principais