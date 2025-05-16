import streamlit as st
import streamlit.components.v1 as components
import json

def render_gauge_chart(value, min_val, max_val, title, color_ranges=None, height=300):
    """
    Render a gauge chart for sensor data
    
    Parameters:
    - value (float): The value to display
    - min_val (float): Minimum value on the gauge
    - max_val (float): Maximum value on the gauge
    - title (str): Chart title
    - color_ranges (list): List of color ranges in format [(min, max, color)]
    - height (int): Chart height in pixels
    
    Returns:
    - None: Renders the chart directly in Streamlit
    """
    if color_ranges is None:
        color_ranges = [
            [min_val, max_val * 0.3, '#91cc75'],  # Green for good conditions
            [max_val * 0.3, max_val * 0.7, '#fac858'],  # Yellow for moderate
            [max_val * 0.7, max_val, '#ee6666']   # Red for poor conditions
        ]
    
    # Format the value for display
    formatted_value = f"{value:.1f}"
    
    # Create the chart options
    options = {
        "tooltip": {
            "formatter": "{a} <br/>{b} : {c}"
        },
        "series": [{
            "name": title,
            "type": "gauge",
            "detail": {"formatter": formatted_value, "fontSize": 20},
            "data": [{"value": value, "name": title}],
            "axisLine": {
                "lineStyle": {
                    "width": 15,
                    "color": color_ranges
                }
            },
            "pointer": {
                "itemStyle": {
                    "color": "auto"
                }
            },
            "axisTick": {
                "distance": -15,
                "length": 5,
                "lineStyle": {
                    "color": "#fff",
                    "width": 1
                }
            },
            "splitLine": {
                "distance": -15,
                "length": 15,
                "lineStyle": {
                    "color": "#fff",
                    "width": 2
                }
            },
            "axisLabel": {
                "distance": -25,
                "color": "#fff",
                "fontSize": 12
            },
            "detail": {
                "valueAnimation": True,
                "formatter": f"{formatted_value}",
                "color": "inherit"
            },
            "min": min_val,
            "max": max_val
        }]
    }
    
    # Render the chart
    chart_code = f"""
    <div id="chart_container_{hash(title)}" style="width:100%;height:{height}px;"></div>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.3.2/dist/echarts.min.js"></script>
    <script type="text/javascript">
        var chartDom = document.getElementById('chart_container_{hash(title)}');
        var myChart = echarts.init(chartDom);
        var option = {options};
        myChart.setOption(option);
        window.addEventListener('resize', function() {{
            myChart.resize();
        }});
    </script>
    """.replace("{options}", json.dumps(options))
    
    components.html(chart_code, height=height)

def render_cycling_comfort_chart(weather_data, height=400):
    """
    Render a radar chart showing cycling comfort based on weather data
    
    Parameters:
    - weather_data (dict): Weather/sensor data
    - height (int): Chart height in pixels
    
    Returns:
    - None: Renders the chart directly in Streamlit
    """
    # Calculate comfort metrics on a scale of 0-100
    temp_comfort = min(100, max(0, 100 - abs(weather_data.get("temperatura", 25) - 22) * 5))
    humidity_comfort = min(100, max(0, 100 - abs(weather_data.get("umidade", 50) - 50)))
    wind_comfort = min(100, max(0, 100 - weather_data.get("vento", 10) * 2))
    
    # Higher is better for these (inversely proportional to discomfort)
    uv_comfort = min(100, max(0, 100 - weather_data.get("indice_uv", 5) * 10))
    air_quality_comfort = min(100, max(0, 100 - weather_data.get("qualidade_ar", 50) / 2))
    
    # Overall comfort score
    overall = (temp_comfort + humidity_comfort + wind_comfort + uv_comfort + air_quality_comfort) / 5
    
    options = {
        "title": {
            "text": "Cycling Comfort Analysis",
            "textStyle": {"color": "#ffffff"}
        },
        "tooltip": {},
        "legend": {
            "data": ["Comfort Score", "Ideal Conditions"],
            "textStyle": {"color": "#ffffff"}
        },
        "radar": {
            "indicator": [
                {"name": "Temperature", "max": 100},
                {"name": "Humidity", "max": 100},
                {"name": "Wind", "max": 100},
                {"name": "UV Protection", "max": 100},
                {"name": "Air Quality", "max": 100}
            ],
            "axisName": {
                "color": "#ffffff"
            }
        },
        "series": [{
            "name": "Comfort vs Ideal",
            "type": "radar",
            "data": [
                {
                    "value": [temp_comfort, humidity_comfort, wind_comfort, uv_comfort, air_quality_comfort],
                    "name": "Comfort Score",
                    "areaStyle": {
                        "color": "rgba(76, 175, 80, 0.6)"
                    },
                    "lineStyle": {
                        "width": 2,
                        "color": "#4CAF50"
                    }
                },
                {
                    "value": [90, 90, 90, 90, 90],
                    "name": "Ideal Conditions",
                    "lineStyle": {
                        "width": 1,
                        "color": "#ffffff",
                        "type": "dashed"
                    }
                }
            ]
        }]
    }
    
    # Render the chart
    chart_code = f"""
    <div id="chart_container_comfort" style="width:100%;height:{height}px;"></div>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.3.2/dist/echarts.min.js"></script>
    <script type="text/javascript">
        var chartDom = document.getElementById('chart_container_comfort');
        var myChart = echarts.init(chartDom);
        var option = {options};
        myChart.setOption(option);
        window.addEventListener('resize', function() {{
            myChart.resize();
        }});
    </script>
    """
    chart_code = chart_code.replace("{options}", json.dumps(options))
    
    components.html(chart_code, height=height)
    
    return overall

def render_line_chart(x_data, y_data, title, x_label, y_label, height=300):
    """
    Render a line chart for time-series data
    
    Parameters:
    - x_data (list): X-axis data points
    - y_data (list): Y-axis data points
    - title (str): Chart title
    - x_label (str): X-axis label
    - y_label (str): Y-axis label
    - height (int): Chart height in pixels
    
    Returns:
    - None: Renders the chart directly in Streamlit
    """
    options = {
        "title": {
            "text": title,
            "textStyle": {"color": "#ffffff"}
        },
        "tooltip": {
            "trigger": "axis"
        },
        "xAxis": {
            "type": "category",
            "data": x_data,
            "name": x_label,
            "nameTextStyle": {"color": "#ffffff"},
            "axisLabel": {"color": "#ffffff"}
        },
        "yAxis": {
            "type": "value",
            "name": y_label,
            "nameTextStyle": {"color": "#ffffff"},
            "axisLabel": {"color": "#ffffff"}
        },
        "series": [{
            "data": y_data,
            "type": "line",
            "smooth": True,
            "itemStyle": {"color": "#4CAF50"},
            "areaStyle": {
                "color": {
                    "type": "linear",
                    "x": 0,
                    "y": 0,
                    "x2": 0,
                    "y2": 1,
                    "colorStops": [{
                        "offset": 0,
                        "color": "rgba(76, 175, 80, 0.8)"
                    }, {
                        "offset": 1,
                        "color": "rgba(76, 175, 80, 0.1)"
                    }]
                }
            }
        }]
    }
    
    # Render the chart
    chart_code = f"""
    <div id="chart_container_{hash(title)}" style="width:100%;height:{height}px;"></div>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.3.2/dist/echarts.min.js"></script>
    <script type="text/javascript">
        var chartDom = document.getElementById('chart_container_{hash(title)}');
        var myChart = echarts.init(chartDom);
        var option = {options};
        myChart.setOption(option);
        window.addEventListener('resize', function() {{
            myChart.resize();
        }});
    </script>
    """.replace("{options}", json.dumps(options))
    
    components.html(chart_code, height=height)
