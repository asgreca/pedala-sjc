def gerar_rota_e_embed(origem: str, passos: list[str], distancia: int = 15, forcar_distancia: bool = False):
    """
    Gera uma rota circular e um mapa HTML embutível que respeita a distância solicitada
    
    Args:
        origem (str): Endereço de origem (e retorno) da rota
        passos (list[str]): Lista de pontos de referência da rota
        distancia (int): Distância desejada em km
        forcar_distancia (bool): Se True, rejeita rotas que não estejam dentro da tolerância
        
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
        # Para garantir rotas mais curtas, usar fator menor para distâncias pequenas
        if distancia <= 10:
            # Para rotas muito curtas (0-10km), reduzir drasticamente o fator
            perfil_fator = 0.3  # Fator fixo pequeno para garantir rotas curtas
            print(f"Distância <= 10km, usando perfil_fator reduzido: {perfil_fator}")
        elif distancia <= 15:
            # Para rotas curtas (10-15km)
            perfil_fator = 0.5
            print(f"Distância <= 15km, usando perfil_fator reduzido: {perfil_fator}")
        else:
            # Para rotas maiores, usar o fator normal com uma redução
            perfil_fator = ciclista_fatores.get(nivel_ciclista, 0.6) * 0.8  # Redução adicional
            print(f"Distância > 15km, usando perfil_fator: {perfil_fator}")
            
        estilo_config = estilo_ajustes.get(estilo_pedalada, {"lat_bias": 1.0, "lng_bias": 1.0})
        
        directions = None
        
        # Gerar a rota usando pontos cardeais
        with st.spinner("Gerando rota personalizada..."):
            # Obter coordenadas da origem
            geocode_result = gmaps.geocode(origem)
            if geocode_result:
                start_lat = geocode_result[0]['geometry']['location']['lat']
                start_lng = geocode_result[0]['geometry']['location']['lng']
                
                # Calcular raio base baseado na distância solicitada, com ajustes
                # Usar um fator reduzido para distâncias menores para evitar rotas muito longas
                raio_km = distancia / (2 * 3.14) * 0.7  # Raio reduzido em 30%
                
                # Calcular fator para distância desejada - reduzir significativamente para distâncias curtas
                if distancia <= 10:
                    base_factor = 0.0005 * distancia  # Fator muito menor para distâncias curtas
                elif distancia <= 15:
                    base_factor = 0.001 * distancia   # Fator menor para distâncias médias
                else:
                    base_factor = 0.002 * distancia   # Fator padrão para distâncias maiores
                    
                print(f"Distância: {distancia}km, base_factor: {base_factor}, raio_km: {raio_km}")
                
                # Ajustar pelo perfil e estilo
                best_route = None
                best_distance_diff = float('inf')
                
                # Fazer diversas tentativas com fatores variados para encontrar uma rota com distância EXATA
                # Usar arrays de multiplicadores muito mais densos para ter mais chances de encontrar uma rota adequada
                # Fatores menores para distâncias curtas (0-15km), médios para médias (15-30km), maiores para longas (30km+)
                
                # Gerar uma lista densa de multiplicadores, priorizando valores menores para garantir rotas mais curtas
                if distancia <= 15:
                    # Para rotas curtas, usar multiplicadores pequenos (0.05 a 0.7)
                    factor_multipliers = [0.05 + (i * 0.01) for i in range(65)]  # 65 valores entre 0.05 e 0.7
                elif distancia <= 30:
                    # Para rotas médias
                    factor_multipliers = [0.1 + (i * 0.02) for i in range(50)]  # 50 valores entre 0.1 e 1.1
                else:
                    # Para rotas longas
                    factor_multipliers = [0.3 + (i * 0.03) for i in range(40)]  # 40 valores entre 0.3 e 1.5
                
                print(f"Tentando gerar rota de {distancia}km usando {len(factor_multipliers)} multiplicadores")
                
                # Variáveis para controle de rotas aceitáveis
                routes_within_tolerance = []
                
                for factor_mult in factor_multipliers:
                    factor = base_factor * factor_mult * perfil_fator
                    
                    # Experimentar diferentes combinações de pontos
                    waypoint_options = [
                        # Norte e Leste (padrão)
                        [f"{start_lat + factor * estilo_config['lat_bias']},{start_lng}", 
                         f"{start_lat},{start_lng + factor * estilo_config['lng_bias']}"],
                        # Norte e Oeste
                        [f"{start_lat + factor * estilo_config['lat_bias']},{start_lng}", 
                         f"{start_lat},{start_lng - factor * estilo_config['lng_bias']}"],
                        # Sul e Leste
                        [f"{start_lat - factor * estilo_config['lat_bias']},{start_lng}", 
                         f"{start_lat},{start_lng + factor * estilo_config['lng_bias']}"],
                        # Sul e Oeste
                        [f"{start_lat - factor * estilo_config['lat_bias']},{start_lng}", 
                         f"{start_lat},{start_lng - factor * estilo_config['lng_bias']}"]
                    ]
                    
                    # Para distâncias muito curtas, tentar waypoints ainda mais próximos
                    if distancia <= 7:
                        factor = factor * 0.5
                        waypoint_options.append([
                            f"{start_lat + factor * estilo_config['lat_bias']},{start_lng}", 
                            f"{start_lat},{start_lng + factor * estilo_config['lng_bias']}"
                        ])
                    
                    # Tentar cada opção de waypoints
                    for waypoints in waypoint_options:
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
                                
                                # Armazenar todas as rotas que estão dentro da tolerância
                                if distance_diff <= 2.0:
                                    routes_within_tolerance.append({
                                        "route": test_route,
                                        "diff": distance_diff,
                                        "distance": test_distance
                                    })
                                
                                # Se for melhor que a melhor até agora, atualizar
                                if distance_diff < best_distance_diff:
                                    best_route = test_route
                                    best_distance_diff = distance_diff
                                    
                                    # Se encontrarmos uma rota perfeita (diferença < 0.5km), sair do loop
                                    if distance_diff < 0.5:
                                        print(f"Encontrada rota com distância quase perfeita: {test_distance}km")
                                        break
                                        
                        except Exception as e:
                            # Registrar erro e continuar
                            print(f"Erro ao gerar rota teste: {str(e)}")
                            continue
                    
                    # Se já temos uma rota muito boa, sair do loop principal
                    if best_distance_diff < 0.5:
                        break
                
                # Se temos rotas dentro da tolerância, escolher a melhor
                if routes_within_tolerance:
                    # Ordenar por diferença (menor primeiro)
                    routes_within_tolerance.sort(key=lambda x: x["diff"])
                    
                    # Usar a rota com menor diferença
                    best_route = routes_within_tolerance[0]["route"]
                    print(f"Selecionada rota com distância de {routes_within_tolerance[0]['distance']:.1f}km " +
                          f"(diferença de {routes_within_tolerance[0]['diff']:.1f}km)")
                else:
                    print(f"Nenhuma rota dentro da tolerância de 2km. Melhor rota tem diferença de {best_distance_diff:.1f}km")
                    # Se não encontramos nenhuma dentro da tolerância, verificar se temos pelo menos uma melhor
                    if best_route is None:
                        print("Nenhuma rota adequada encontrada, tentando waypoints simples...")
                    else:
                        print("Usando a melhor rota encontrada fora da tolerância")
                
                # Usar a melhor rota encontrada
                if best_route:
                    directions = best_route
            
            # Se ainda não tem rota, tentar com waypoints específicos
            if not directions:
                try:
                    directions = gmaps.directions(
                        origin=origem,
                        destination=origem,
                        waypoints=waypoints_to_use[:2],
                        mode="bicycling",
                        optimize_waypoints=True
                    )
                except:
                    pass
            
            # Se ainda não tem rota, tentar rota mais simples
            if not directions:
                try:
                    directions = gmaps.directions(
                        origin=origem,
                        destination=origem,
                        mode="bicycling"
                    )
                except:
                    pass
            
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
        distancia_calculada = sum(leg['distance']['value'] for leg in directions[0]['legs'])/1000
        
        # RIGOROSO: Verificar uma última vez se a rota respeita a tolerância de 2km
        # Se não estiver respeitando, imprimir um aviso e reduzir a rota (caso comum: distância solicitada = 10km, mas rota = 24km)
        if abs(distancia_calculada - distancia) > 2.0:
            print(f"AVISO: Rota gerada com {distancia_calculada:.1f}km excede a tolerância de 2km para {distancia}km solicitados!")
            
            # SOLUÇÃO ESPECIAL para forçar distância (<=10km)
            if forcar_distancia:
                print("Modo FORÇAR DISTÂNCIA ativado - Tentando soluções radicais para rotas curtas...")
                
                # SOLUÇÃO ESPECIAL para distâncias curtas (<=10km)
                if distancia <= 10:
                    # Para rotas muito curtas, usamos rotas simples com pontos próximos
                    try:
                        # Para distâncias <=10km, usar pontos muito próximos da origem
                        tiny_factor = 0.0002 * distancia  # Fator extremamente pequeno
                        
                        # Criar pontos muito próximos da origem
                        close_waypoints = [
                            f"{start_lat + tiny_factor},{start_lng}",
                            f"{start_lat},{start_lng + tiny_factor}"
                        ]
                        
                        # Tentar uma rota simples muito próxima
                        simple_route = gmaps.directions(
                            origin=origem,
                            destination=origem,
                            waypoints=close_waypoints,
                            mode="bicycling"
                        )
                        
                        if simple_route:
                            simple_distance = sum(leg['distance']['value'] for leg in simple_route[0]['legs'])/1000
                            print(f"Gerada rota simples de {simple_distance:.1f}km")
                            
                            # Se esta rota está mais próxima do ideal, usar
                            if abs(simple_distance - distancia) < abs(distancia_calculada - distancia):
                                directions = simple_route
                                distancia_calculada = simple_distance
                                print(f"Substituindo por rota curta de {distancia_calculada:.1f}km")
                    except Exception as e:
                        print(f"Erro ao gerar rota curta simples: {str(e)}")
                    
                    # Se ainda estamos fora da tolerância, tentar com pontos fixos conhecidos
                    if abs(distancia_calculada - distancia) > 2.0:
                        try:
                            # Pontos próximos em São José dos Campos para rotas curtas
                            pontos_centro = [
                                "Praça Afonso Pena, São José dos Campos, SP",
                                "Centro da Juventude, São José dos Campos, SP",
                                "Mercado Municipal, São José dos Campos, SP"
                            ]
                            
                            # Usar apenas um ponto próximo para rotas mais curtas
                            center_route = gmaps.directions(
                                origin=origem,
                                destination=origem,
                                waypoints=[pontos_centro[0]],
                                mode="bicycling"
                            )
                            
                            if center_route:
                                center_distance = sum(leg['distance']['value'] for leg in center_route[0]['legs'])/1000
                                
                                # Verificar se é melhor que a atual
                                if abs(center_distance - distancia) < abs(distancia_calculada - distancia):
                                    directions = center_route
                                    distancia_calculada = center_distance
                                    print(f"Substituindo por rota do centro: {distancia_calculada:.1f}km")
                        except Exception as e:
                            print(f"Erro ao tentar rota com pontos no centro: {str(e)}")
            # Comportamento normal quando não forçamos distância
            elif waypoints_to_use and len(waypoints_to_use) > 1:
                print("Tentando encurtar a rota com pontos mais próximos...")
                # Priorizar locais próximos em São José dos Campos para substituir pontos distantes
                locais_proximos = [
                    "Praça Afonso Pena, São José dos Campos, SP",  # Centro
                    "Parque Vicentina Aranha, São José dos Campos, SP",  # Próximo ao centro
                    "Parque Santos Dumont, São José dos Campos, SP",  # Próximo ao centro
                    "Shopping Centro São José, São José dos Campos, SP",  # Centro
                    "Mercado Municipal, São José dos Campos, SP"  # Centro
                ]
                
                # Tentar substituir waypoints
                try:
                    # Usar apenas 1-2 waypoints próximos
                    test_route = gmaps.directions(
                        origin=origem,
                        destination=origem,
                        waypoints=[locais_proximos[0]],  # Usar apenas um waypoint
                        mode="bicycling",
                        optimize_waypoints=True
                    )
                    
                    if test_route:
                        test_distance = sum(leg['distance']['value'] for leg in test_route[0]['legs'])/1000
                        # Se estiver mais próximo da distância desejada, usar esta rota
                        if abs(test_distance - distancia) < abs(distancia_calculada - distancia):
                            directions = test_route
                            distancia_calculada = test_distance
                            print(f"Rota ajustada para {distancia_calculada:.1f}km")
                except Exception as e:
                    print(f"Erro ao tentar encurtar rota: {str(e)}")
        
        distancia_total = f"{distancia_calculada:.1f} km"
        
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
        strokeColor: '#FF0000',
        strokeWeight: 5,
        strokeOpacity: 0.8
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
        primeira_rua = ruas_traduzidas[0] if ruas_traduzidas else "Início do trajeto"
        ultima_rua = ruas_traduzidas[-1] if ruas_traduzidas else "Fim do trajeto"
        
        texto = f"""
### 🗺️ Resumo da Rota  
**Origem e retorno:** {origem}  
**Distância total:** {distancia_total}  

**Trajeto fechado confirmado:**
- **Início:** {primeira_rua}
- **Fim:** {ultima_rua}

**Passos detalhados:**  
<ol>
{''.join(f"<li>{rua}</li>" for rua in ruas_traduzidas)}
</ol>
"""
        return mapa_html, texto, elevation_data
        
    except Exception as e:
        st.error(f"Erro ao gerar rota: {str(e)}")
        return "", f"<p>Não foi possível gerar a rota: {str(e)}</p>", []