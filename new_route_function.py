def gerar_rota_e_embed(origem: str, passos: list[str], distancia: int = 15):
    """
    Gera uma rota circular e um mapa HTML embutível que respeita a distância solicitada
    
    Args:
        origem (str): Endereço de origem (e retorno) da rota
        passos (list[str]): Lista de pontos de referência da rota
        distancia (int): Distância desejada em km
        
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
                for factor_mult in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]:
                    factor = base_factor * factor_mult * perfil_fator
                    
                    # Criar pontos de waypoint
                    north = f"{start_lat + factor * estilo_config['lat_bias']},{start_lng}"
                    east = f"{start_lat},{start_lng + factor * estilo_config['lng_bias']}"
                    
                    try:
                        # Gerar rota de teste
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
                            distance_diff = abs(test_distance - distancia)
                            
                            # Se for melhor, guardar esta rota
                            if distance_diff < best_distance_diff:
                                best_route = test_route
                                best_distance_diff = distance_diff
                                
                                # Se estiver dentro de 2km da distância desejada, parar
                                if distance_diff <= 2.0:
                                    break
                    except:
                        # Silenciosamente continuar para a próxima tentativa
                        pass
                
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
        strokeColor: '#3498db',
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