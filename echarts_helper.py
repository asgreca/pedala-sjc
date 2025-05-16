import json
import random
from datetime import datetime, timedelta

def generate_sensor_gauge_chart(sensor_key, value, label, unit, range_values):
    """
    Generate an ECharts gauge chart for a sensor
    
    Args:
        sensor_key (str): Key name of the sensor
        value (float): Current value of the sensor
        label (str): Display label for the sensor
        unit (str): Unit of measurement
        range_values (list): Min and max values for the gauge
        
    Returns:
        str: HTML component with ECharts gauge
    """
    # Define color for different sensor types
    colors = {
        "temperatura": ['#2c3e50', '#3498db', '#e74c3c'],
        "umidade": ['#2c3e50', '#3498db', '#3498db'],
        "pressao": ['#2c3e50', '#16a085', '#16a085'],
        "luminosidade": ['#2c3e50', '#f39c12', '#f1c40f']
    }
    
    color = colors.get(sensor_key, ['#2c3e50', '#3498db', '#2ecc71'])
    
    # Calculate percentage for the gauge
    min_val, max_val = range_values
    percent = (value - min_val) / (max_val - min_val) * 100
    percent = max(0, min(100, percent))
    
    # Generate HTML for the chart
    html = f"""
    <div id="{sensor_key}_chart" style="width:100%;height:250px;"></div>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <script>
        var chart = echarts.init(document.getElementById('{sensor_key}_chart'));
        var option = {{
            series: [{{
                type: 'gauge',
                startAngle: 180,
                endAngle: 0,
                min: {min_val},
                max: {max_val},
                splitNumber: 5,
                itemStyle: {{
                    color: {{
                        type: 'linear',
                        x: 0,
                        y: 0,
                        x2: 1,
                        y2: 1,
                        colorStops: [
                            {{ offset: 0, color: '{color[0]}' }},
                            {{ offset: 0.5, color: '{color[1]}' }},
                            {{ offset: 1, color: '{color[2]}' }}
                        ]
                    }}
                }},
                progress: {{
                    show: true,
                    roundCap: true,
                    width: 18
                }},
                pointer: {{
                    icon: 'path://M2090.36389,615.30999 L2090.36389,615.30999 C2091.48372,615.30999 2092.40383,616.23010 2092.40383,617.34993 L2092.40383,617.34993 C2092.40383,618.46975 2091.48372,619.38987 2090.36389,619.38987 L2090.36389,619.38987 C2089.24406,619.38987 2088.32395,618.46975 2088.32395,617.34993 L2088.32395,617.34993 C2088.32395,616.23010 2089.24406,615.30999 2090.36389,615.30999 Z',
                    length: '75%',
                    width: 16,
                    offsetCenter: [0, '5%']
                }},
                axisLine: {{
                    roundCap: true,
                    lineStyle: {{
                        width: 18
                    }}
                }},
                axisTick: {{
                    splitNumber: 5,
                    lineStyle: {{
                        width: 2,
                        color: '#999'
                    }}
                }},
                splitLine: {{
                    length: 12,
                    lineStyle: {{
                        width: 3,
                        color: '#999'
                    }}
                }},
                axisLabel: {{
                    distance: 30,
                    color: '#999',
                    fontSize: 14
                }},
                title: {{
                    show: true,
                    offsetCenter: [0, '30%'],
                    fontSize: 18,
                    color: '#fff'
                }},
                detail: {{
                    backgroundColor: '#fff',
                    borderColor: '#999',
                    borderWidth: 2,
                    width: 80,
                    lineHeight: 40,
                    height: 40,
                    borderRadius: 8,
                    offsetCenter: [0, '60%'],
                    formatter: '{value} {unit}',
                    color: '#3498db',
                    fontSize: 16,
                    fontWeight: 'bold'
                }},
                data: [{{
                    value: {value:.1f},
                    name: '{label}'
                }}]
            }}]
        }};
        chart.setOption(option);
        window.addEventListener('resize', function() {{
            chart.resize();
        }});
    </script>
    """.replace('{unit}', unit).replace('{value}', '{value}')
    
    return html

def generate_historical_chart(data_history):
    """
    Generate an ECharts line chart for historical sensor data
    
    Args:
        data_history (list): List of historical sensor readings
        
    Returns:
        str: HTML component with ECharts line chart
    """
    if not data_history:
        return "<div>No historical data available</div>"
    
    # Extract timestamps and sensor values
    timestamps = [entry.get('timestamp', '') for entry in data_history]
    
    temperatura_values = [entry.get('temperatura', 0) for entry in data_history]
    umidade_values = [entry.get('umidade', 0) for entry in data_history]
    pressao_values = [entry.get('pressao', 0) for entry in data_history]
    luminosidade_values = [entry.get('luminosidade', 0) for entry in data_history]
    
    # Scale values to similar ranges for better visualization
    pressao_scaled = [(p - 1000) * 2 for p in pressao_values]
    luminosidade_scaled = [l / 10 for l in luminosidade_values]
    
    # Generate HTML for the chart
    html = f"""
    <div id="history_chart" style="width:100%;height:400px;"></div>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <script>
        var chart = echarts.init(document.getElementById('history_chart'));
        var option = {{
            backgroundColor: '#1e2a38',
            title: {{
                text: 'Histórico de Sensores',
                left: 'center',
                textStyle: {{
                    color: '#ecf0f1'
                }}
            }},
            tooltip: {{
                trigger: 'axis',
                axisPointer: {{
                    type: 'cross',
                    label: {{
                        backgroundColor: '#6a7985'
                    }}
                }}
            }},
            legend: {{
                data: ['Temperatura (°C)', 'Umidade (%)', 'Pressão (rel)', 'Luminosidade (rel)'],
                top: 30,
                textStyle: {{
                    color: '#ecf0f1'
                }}
            }},
            grid: {{
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            }},
            xAxis: [{{
                type: 'category',
                boundaryGap: false,
                data: {json.dumps(timestamps)},
                axisLabel: {{
                    color: '#ecf0f1'
                }},
                axisLine: {{
                    lineStyle: {{
                        color: '#34495e'
                    }}
                }}
            }}],
            yAxis: [{{
                type: 'value',
                axisLabel: {{
                    color: '#ecf0f1'
                }},
                axisLine: {{
                    lineStyle: {{
                        color: '#34495e'
                    }}
                }},
                splitLine: {{
                    lineStyle: {{
                        color: '#34495e',
                        opacity: 0.3
                    }}
                }}
            }}],
            series: [
                {{
                    name: 'Temperatura (°C)',
                    type: 'line',
                    stack: 'Total',
                    lineStyle: {{
                        width: 3
                    }},
                    showSymbol: true,
                    areaStyle: {{
                        opacity: 0.3,
                        color: {{
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                {{offset: 0, color: '#e74c3c'}},
                                {{offset: 1, color: 'rgba(231, 76, 60, 0)'}}
                            ]
                        }}
                    }},
                    emphasis: {{
                        focus: 'series'
                    }},
                    color: '#e74c3c',
                    data: {json.dumps(temperatura_values)}
                }},
                {{
                    name: 'Umidade (%)',
                    type: 'line',
                    stack: 'Total',
                    lineStyle: {{
                        width: 3
                    }},
                    showSymbol: true,
                    areaStyle: {{
                        opacity: 0.3,
                        color: {{
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                {{offset: 0, color: '#3498db'}},
                                {{offset: 1, color: 'rgba(52, 152, 219, 0)'}}
                            ]
                        }}
                    }},
                    emphasis: {{
                        focus: 'series'
                    }},
                    color: '#3498db',
                    data: {json.dumps(umidade_values)}
                }},
                {{
                    name: 'Pressão (rel)',
                    type: 'line',
                    stack: 'Total',
                    lineStyle: {{
                        width: 3
                    }},
                    showSymbol: true,
                    areaStyle: {{
                        opacity: 0.3,
                        color: {{
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                {{offset: 0, color: '#16a085'}},
                                {{offset: 1, color: 'rgba(22, 160, 133, 0)'}}
                            ]
                        }}
                    }},
                    emphasis: {{
                        focus: 'series'
                    }},
                    color: '#16a085',
                    data: {json.dumps(pressao_scaled)}
                }},
                {{
                    name: 'Luminosidade (rel)',
                    type: 'line',
                    stack: 'Total',
                    lineStyle: {{
                        width: 3
                    }},
                    showSymbol: true,
                    areaStyle: {{
                        opacity: 0.3,
                        color: {{
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                {{offset: 0, color: '#f39c12'}},
                                {{offset: 1, color: 'rgba(243, 156, 18, 0)'}}
                            ]
                        }}
                    }},
                    emphasis: {{
                        focus: 'series'
                    }},
                    color: '#f39c12',
                    data: {json.dumps(luminosidade_scaled)}
                }}
            ]
        }};
        chart.setOption(option);
        window.addEventListener('resize', function() {{
            chart.resize();
        }});
    </script>
    """
    
    return html

def generate_prediction_chart(current_data, current_hour):
    """
    Generate an ECharts chart with weather predictions for the next hours
    
    Args:
        current_data (dict): Current sensor readings
        current_hour (int): Current hour of the day
        
    Returns:
        str: HTML component with ECharts prediction chart
    """
    # Get current values
    temperatura = current_data.get('temperatura', 25)
    umidade = current_data.get('umidade', 50)
    
    # Generate predictions for the next 8 hours
    hours = [(current_hour + i) % 24 for i in range(8)]
    hour_labels = [f"{h}:00" for h in hours]
    
    # Generate plausible temperature predictions
    temp_predictions = []
    humid_predictions = []
    
    for i in range(8):
        # Temperature tends to rise until 14:00 and then fall
        hour = hours[i]
        if hour < 14 and hour > 6:
            temp_change = random.uniform(0, 1.5)
        else:
            temp_change = random.uniform(-1.5, 0)
            
        # Add some randomness
        temp_predictions.append(round(temperatura + temp_change * (i+1) + random.uniform(-1, 1), 1))
        
        # Humidity tends to decrease during the day and increase at night
        if 8 <= hour <= 18:
            humid_change = random.uniform(-3, -0.5)
        else:
            humid_change = random.uniform(0.5, 3)
            
        humid_predictions.append(round(min(100, max(0, umidade + humid_change * (i+1) + random.uniform(-2, 2))), 1))
    
    # Calculate comfort index (a simple metric based on temp and humidity)
    comfort_index = []
    for t, h in zip(temp_predictions, humid_predictions):
        # Simple heat index approximation
        if t >= 27 and h >= 40:
            # Hot and humid - less comfortable
            comfort = max(0, 10 - (t - 20) * 0.4 - (h - 40) * 0.05)
        elif t <= 15:
            # Cold - less comfortable
            comfort = max(0, 10 - (20 - t) * 0.4)
        else:
            # Mild temperature and moderate humidity - more comfortable
            comfort = min(10, 10 - abs(t - 23) * 0.2 - abs(h - 50) * 0.02)
            
        comfort_index.append(round(comfort, 1))
    
    # Calculate best riding time index (0-10)
    riding_index = []
    for i, (h, t, hu) in enumerate(zip(hours, temp_predictions, humid_predictions)):
        # Factors affecting ride quality:
        # 1. Temperature (ideal around 18-25°C)
        # 2. Humidity (ideal around 40-60%)
        # 3. Time of day (avoid rush hours 7-9, 17-19)
        
        temp_factor = 10 - min(10, abs(t - 22) * 0.5)
        humid_factor = 10 - min(10, abs(hu - 50) * 0.05)
        
        # Time factor (rush hours penalty)
        time_factor = 10
        if 7 <= h <= 9 or 17 <= h <= 19:
            time_factor = 6  # Rush hour penalty
            
        # If it's dark (before 6AM or after 7PM)
        if h < 6 or h >= 19:
            time_factor -= 2  # Darkness penalty
            
        # Calculate overall riding quality
        ride_quality = (temp_factor * 0.4 + humid_factor * 0.2 + time_factor * 0.4)
        riding_index.append(round(ride_quality, 1))
    
    # Generate HTML for the chart
    html = f"""
    <div id="prediction_chart" style="width:100%;height:400px;"></div>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <script>
        var chart = echarts.init(document.getElementById('prediction_chart'));
        var option = {{
            backgroundColor: '#1e2a38',
            title: {{
                text: 'Previsão para as Próximas Horas',
                left: 'center',
                textStyle: {{
                    color: '#ecf0f1'
                }}
            }},
            tooltip: {{
                trigger: 'axis',
                axisPointer: {{
                    type: 'cross',
                    label: {{
                        backgroundColor: '#6a7985'
                    }}
                }},
                formatter: function(params) {{
                    var result = params[0].name + '<br/>';
                    params.forEach(function(param) {{
                        var value = param.value;
                        var unit = '';
                        if (param.seriesName.includes('Temperatura')) {{
                            unit = ' °C';
                        }} else if (param.seriesName.includes('Umidade')) {{
                            unit = ' %';
                        }} else {{
                            unit = '/10';
                        }}
                        result += 
                            '<span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:' + 
                            param.color + '"></span>' + 
                            param.seriesName + ': ' + value + unit + '<br/>';
                    }});
                    return result;
                }}
            }},
            legend: {{
                data: ['Temperatura', 'Umidade', 'Índice de Conforto', 'Qualidade para Pedalar'],
                top: 30,
                textStyle: {{
                    color: '#ecf0f1'
                }}
            }},
            grid: {{
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            }},
            xAxis: [{{
                type: 'category',
                boundaryGap: false,
                data: {json.dumps(hour_labels)},
                axisLabel: {{
                    color: '#ecf0f1'
                }},
                axisLine: {{
                    lineStyle: {{
                        color: '#34495e'
                    }}
                }}
            }}],
            yAxis: [{{
                type: 'value',
                name: 'Temperatura / Umidade',
                min: 0,
                max: 100,
                position: 'left',
                axisLabel: {{
                    color: '#ecf0f1',
                    formatter: '{{value}}'
                }},
                axisLine: {{
                    lineStyle: {{
                        color: '#34495e'
                    }}
                }},
                splitLine: {{
                    lineStyle: {{
                        color: '#34495e',
                        opacity: 0.3
                    }}
                }}
            }}, {{
                type: 'value',
                name: 'Índices',
                min: 0,
                max: 10,
                position: 'right',
                axisLabel: {{
                    color: '#ecf0f1',
                    formatter: '{{value}}'
                }},
                axisLine: {{
                    lineStyle: {{
                        color: '#34495e'
                    }}
                }},
                splitLine: {{
                    show: false
                }}
            }}],
            series: [
                {{
                    name: 'Temperatura',
                    type: 'line',
                    yAxisIndex: 0,
                    lineStyle: {{
                        width: 3
                    }},
                    showSymbol: true,
                    emphasis: {{
                        focus: 'series'
                    }},
                    color: '#e74c3c',
                    data: {json.dumps(temp_predictions)}
                }},
                {{
                    name: 'Umidade',
                    type: 'line',
                    yAxisIndex: 0,
                    lineStyle: {{
                        width: 3
                    }},
                    showSymbol: true,
                    emphasis: {{
                        focus: 'series'
                    }},
                    color: '#3498db',
                    data: {json.dumps(humid_predictions)}
                }},
                {{
                    name: 'Índice de Conforto',
                    type: 'bar',
                    yAxisIndex: 1,
                    barWidth: '40%',
                    emphasis: {{
                        focus: 'series'
                    }},
                    color: '#2ecc71',
                    data: {json.dumps(comfort_index)}
                }},
                {{
                    name: 'Qualidade para Pedalar',
                    type: 'line',
                    yAxisIndex: 1,
                    lineStyle: {{
                        width: 4,
                        type: 'dashed'
                    }},
                    showSymbol: true,
                    symbolSize: 10,
                    emphasis: {{
                        focus: 'series'
                    }},
                    color: '#f39c12',
                    data: {json.dumps(riding_index)},
                    markPoint: {{
                        data: [
                            {{ type: 'max', name: 'Melhor Horário' }}
                        ],
                        label: {{
                            formatter: 'Melhor Horário',
                            position: 'top'
                        }}
                    }}
                }}
            ]
        }};
        chart.setOption(option);
        window.addEventListener('resize', function() {{
            chart.resize();
        }});
    </script>
    """
    
    return html

def generate_route_elevation_chart(elevation_data):
    """
    Generate an ECharts chart for elevation data along a route
    
    Args:
        elevation_data (list): List of dicts with distance and elevation
        
    Returns:
        str: HTML component with ECharts elevation chart
    """
    if not elevation_data:
        return "<div>No elevation data available</div>"
    
    # Extract data from elevation_data
    distances = [point.get('distance', 0) for point in elevation_data]
    elevations = [point.get('elevation', 0) for point in elevation_data]
    
    max_elevation = max(elevations)
    min_elevation = min(elevations)
    elevation_diff = max_elevation - min_elevation
    
    # Calculate steepness data (just for visualization)
    steepness = []
    for i in range(1, len(elevations)):
        if distances[i] - distances[i-1] > 0:
            # Calculate slope percentage
            slope = (elevations[i] - elevations[i-1]) / (distances[i] - distances[i-1]) * 100
            steepness.append(round(slope, 1))
        else:
            steepness.append(0)
    steepness.insert(0, 0)  # Add a zero to the beginning for the first point
    
    # Generate HTML for the chart
    html = f"""
    <div id="elevation_chart" style="width:100%;height:300px;"></div>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <script>
        var chart = echarts.init(document.getElementById('elevation_chart'));
        var option = {{
            backgroundColor: '#1e2a38',
            title: {{
                text: 'Perfil de Elevação',
                left: 'center',
                textStyle: {{
                    color: '#ecf0f1'
                }}
            }},
            tooltip: {{
                trigger: 'axis',
                formatter: function(params) {{
                    var result = 'Distância: ' + params[0].axisValue + ' km<br/>';
                    params.forEach(function(param) {{
                        var value = param.value;
                        var unit = param.seriesName === 'Elevação' ? ' m' : ' %';
                        result += 
                            '<span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:' + 
                            param.color + '"></span>' + 
                            param.seriesName + ': ' + value + unit + '<br/>';
                    }});
                    return result;
                }}
            }},
            legend: {{
                data: ['Elevação', 'Inclinação'],
                top: 30,
                textStyle: {{
                    color: '#ecf0f1'
                }}
            }},
            grid: {{
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            }},
            xAxis: {{
                type: 'category',
                boundaryGap: false,
                data: {json.dumps(distances)},
                name: 'Distância (km)',
                nameLocation: 'middle',
                nameGap: 30,
                nameTextStyle: {{
                    color: '#ecf0f1'
                }},
                axisLabel: {{
                    color: '#ecf0f1'
                }},
                axisLine: {{
                    lineStyle: {{
                        color: '#34495e'
                    }}
                }}
            }},
            yAxis: [
                {{
                    type: 'value',
                    name: 'Elevação (m)',
                    min: {min_elevation - 5},
                    max: {max_elevation + 10},
                    position: 'left',
                    axisLabel: {{
                        color: '#ecf0f1'
                    }},
                    axisLine: {{
                        lineStyle: {{
                            color: '#34495e'
                        }}
                    }},
                    splitLine: {{
                        lineStyle: {{
                            color: '#34495e',
                            opacity: 0.3
                        }}
                    }}
                }},
                {{
                    type: 'value',
                    name: 'Inclinação (%)',
                    min: -15,
                    max: 15,
                    position: 'right',
                    axisLabel: {{
                        color: '#ecf0f1'
                    }},
                    axisLine: {{
                        lineStyle: {{
                            color: '#34495e'
                        }}
                    }},
                    splitLine: {{
                        show: false
                    }}
                }}
            ],
            visualMap: {{
                show: false,
                dimension: 1,
                pieces: [
                    {{lte: {min_elevation + elevation_diff * 0.2}, color: '#3498db'}},
                    {{gt: {min_elevation + elevation_diff * 0.2}, lte: {min_elevation + elevation_diff * 0.5}, color: '#2ecc71'}},
                    {{gt: {min_elevation + elevation_diff * 0.5}, lte: {min_elevation + elevation_diff * 0.8}, color: '#f39c12'}},
                    {{gt: {min_elevation + elevation_diff * 0.8}, color: '#e74c3c'}}
                ]
            }},
            series: [
                {{
                    name: 'Elevação',
                    type: 'line',
                    sampling: 'average',
                    yAxisIndex: 0,
                    areaStyle: {{
                        opacity: 0.8,
                        color: {{
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                {{offset: 0, color: '#3498db'}},
                                {{offset: 0.3, color: '#2ecc71'}},
                                {{offset: 0.6, color: '#f39c12'}},
                                {{offset: 1, color: '#e74c3c'}}
                            ]
                        }}
                    }},
                    data: {json.dumps(elevations)},
                    markPoint: {{
                        data: [
                            {{ type: 'max', name: 'Ponto mais alto' }},
                            {{ type: 'min', name: 'Ponto mais baixo' }}
                        ],
                        label: {{
                            color: '#fff'
                        }}
                    }}
                }},
                {{
                    name: 'Inclinação',
                    type: 'line',
                    yAxisIndex: 1,
                    lineStyle: {{
                        type: 'dashed',
                        width: 2
                    }},
                    data: {json.dumps(steepness)},
                    markLine: {{
                        data: [
                            {{ yAxis: 0, name: 'Plano' }}
                        ],
                        label: {{
                            formatter: 'Plano',
                            position: 'insideEndTop'
                        }},
                        lineStyle: {{
                            color: '#ecf0f1',
                            type: 'dashed'
                        }}
                    }}
                }}
            ]
        }};
        chart.setOption(option);
        window.addEventListener('resize', function() {{
            chart.resize();
        }});
    </script>
    """
    
    return html
