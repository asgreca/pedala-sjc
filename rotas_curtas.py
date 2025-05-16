"""
Módulo específico para lidar com rotas curtas (≤10km).
Esta implementação prioriza a distância exata sobre a qualidade da rota.
"""
import os
import re
import html
import math
import googlemaps
import streamlit as st

def gerar_rota_curta(origem: str, distancia: int = 10):
    """
    Gera uma rota circular curta (≤10km) com foco em respeitar a distância solicitada
    
    Args:
        origem (str): Endereço de origem (e retorno) da rota
        distancia (int): Distância desejada em km
        
    Returns:
        tuple: HTML do mapa, texto descritivo da rota, dados de elevação
    """
    # Obter a chave da API do Google Maps
    GMAPS_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    if not GMAPS_KEY:
        return "", "<p>Mapa não disponível sem a chave do Google Maps API</p>", []
    
    try:
        # Inicializar o cliente do Google Maps
        gmaps = googlemaps.Client(key=GMAPS_KEY)
        
        # Geocodificar o endereço de origem
        geocode_result = gmaps.geocode(origem)
        if not geocode_result:
            return "", "<p>Não foi possível encontrar o endereço especificado.</p>", []
        
        # Obter coordenadas da origem
        start_lat = geocode_result[0]['geometry']['location']['lat']
        start_lng = geocode_result[0]['geometry']['location']['lng']
        
        # Calcular pontos próximos baseados na distância solicitada
        # Usar um fator extremamente pequeno para distâncias curtas
        print(f"Gerando rota CURTA de {distancia}km a partir de {origem}")
        
        # Ajustar o fator de coordenadas com base na distância (experimentação)
        # Estes valores são aproximados e podem precisar de ajustes
        # Para São José dos Campos, estamos usando fatores bem conservadores
        if distancia <= 5:
            # Para rotas muito curtas (0-5km)
            factor = 0.002
        elif distancia <= 10:
            # Para rotas curtas (5-10km)
            factor = 0.004
        else:
            # Para rotas médias (10-15km)
            factor = 0.008
            
        print(f"Usando fator de coordenadas: {factor}")
        
        # Gerar diferentes opções de waypoints muito próximos para testar
        routes_to_try = []
        
        # Considerando que estamos em São José dos Campos, usar pontos de referência conhecidos
        central_points = [
            "Praça Afonso Pena, São José dos Campos, SP",
            "Parque Vicentina Aranha, São José dos Campos, SP",
            "Mercado Municipal, São José dos Campos, SP"
        ]
        
        # Pontos cartesianos ao redor da origem
        directions = [
            # Norte e Sul (apenas um waypoint)
            [f"{start_lat + factor},{start_lng}"],  # Norte
            [f"{start_lat - factor},{start_lng}"],  # Sul
            # Leste e Oeste (apenas um waypoint) 
            [f"{start_lat},{start_lng + factor}"],  # Leste
            [f"{start_lat},{start_lng - factor}"],  # Oeste
            # Nordeste (apenas um waypoint)
            [f"{start_lat + factor * 0.7},{start_lng + factor * 0.7}"],
            # Usar pontos de referência conhecidos centrais
            [central_points[0]],
            [central_points[1]]
        ]
        
        # Para rotas um pouco mais longas, adicionar dois waypoints
        if distancia >= 5:
            directions.extend([
                # Norte e Leste (dois waypoints)
                [f"{start_lat + factor * 0.5},{start_lng}", f"{start_lat},{start_lng + factor * 0.5}"],
                # Norte e Oeste (dois waypoints)
                [f"{start_lat + factor * 0.5},{start_lng}", f"{start_lat},{start_lng - factor * 0.5}"],
                # Sul e Leste (dois waypoints)
                [f"{start_lat - factor * 0.5},{start_lng}", f"{start_lat},{start_lng + factor * 0.5}"],
                # Sul e Oeste (dois waypoints)
                [f"{start_lat - factor * 0.5},{start_lng}", f"{start_lat},{start_lng - factor * 0.5}"]
            ])
        
        # Testar todas as opções e escolher a melhor
        best_route = None
        best_distance_diff = float('inf')
        
        for waypoints in directions:
            try:
                route = gmaps.directions(
                    origin=origem,
                    destination=origem,
                    waypoints=waypoints,
                    mode="bicycling",
                    optimize_waypoints=True
                )
                
                if route:
                    # Calcular a distância da rota
                    distance = sum(leg['distance']['value'] for leg in route[0]['legs'])/1000
                    distance_diff = abs(distance - distancia)
                    
                    print(f"Opção com waypoints {waypoints}: {distance:.1f}km (diferença: {distance_diff:.1f}km)")
                    
                    # Adicionar os waypoints usados ao objeto de rota para refereência quando gerar o mapa
                    route[0]['waypoints_used'] = waypoints
                    
                    # Salvar a rota e sua diferença para comparação posterior
                    routes_to_try.append({
                        "route": route,
                        "distance": distance,
                        "diff": distance_diff,
                        "waypoints": waypoints
                    })
                    
                    # Atualizar a melhor rota encontrada
                    if distance_diff < best_distance_diff:
                        best_route = route
                        best_distance_diff = distance_diff
                        
                        # Se a rota estiver dentro da tolerância de 0.5km, sair do loop
                        if distance_diff <= 0.5:
                            print(f"✓ Encontrada rota ideal: {distance:.1f}km (diferença: {distance_diff:.1f}km)")
                            break
            except Exception as e:
                print(f"Erro ao gerar rota com waypoints {waypoints}: {str(e)}")
        
        # Se temos várias opções, escolher a melhor
        if routes_to_try:
            # Ordenar por diferença (menor primeiro)
            routes_to_try.sort(key=lambda x: x["diff"])
            
            # Imprimir as 3 melhores opções
            print("\nMelhores opções:")
            for i, route_option in enumerate(routes_to_try[:3]):
                print(f"{i+1}. Distância: {route_option['distance']:.1f}km, " +
                      f"Diferença: {route_option['diff']:.1f}km, " +
                      f"Waypoints: {route_option['waypoints']}")
            
            # Usar a melhor rota
            if routes_to_try[0]["diff"] <= 2.0:  # Dentro da tolerância de 2km
                best_route = routes_to_try[0]["route"]
                best_distance = routes_to_try[0]["distance"]
                print(f"\n✓ Selecionada rota com {best_distance:.1f}km " +
                      f"(diferença de {routes_to_try[0]['diff']:.1f}km)")
            else:
                print(f"\n⚠️ A melhor rota tem {routes_to_try[0]['distance']:.1f}km, " +
                      f"que excede a tolerância de 2km da distância solicitada ({distancia}km)")
        
        # Se não encontrou nenhuma rota adequada
        if not best_route:
            return "", "<p>Não foi possível encontrar uma rota adequada para a distância solicitada.</p>", []
            
        # Gerar a rota final
        directions = best_route
            
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
        
        # Preparar os waypoints para o JavaScript
        waypoints_js = ""
        for waypoint in best_route[0]['waypoints_used']:
            if isinstance(waypoint, str) and ',' in waypoint:
                # É uma coordenada lat,lng
                lat, lng = waypoint.split(',')
                waypoints_js += f"""
        {{
          location: new google.maps.LatLng({lat}, {lng})
        }},"""
            else:
                # É um endereço
                waypoints_js += f"""
        {{
          location: "{waypoint}"
        }},"""
        
        # Remover a vírgula final se houver waypoints
        if waypoints_js:
            waypoints_js = waypoints_js.rstrip(',')
        
        # Gerar HTML do mapa - agora com os waypoints usados para gerar a rota
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
    
    // IMPORTANTE: Usar OS MESMOS waypoints que foram usados para calcular a rota
    directionsService.route({{
      origin: "{origem}",
      destination: "{origem}",
      waypoints: [{waypoints_js}],
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
        
        # Imprimir mensagem de sucesso com a distância da rota gerada
        print(f"✓ Rota curta gerada com sucesso: {distancia_calculada:.1f}km")
        
        return mapa_html, texto, elevation_data
    
    except Exception as e:
        st.error(f"Erro ao gerar rota curta: {str(e)}")
        return "", f"<p>Não foi possível gerar a rota curta: {str(e)}</p>", []