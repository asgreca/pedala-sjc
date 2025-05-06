"""
Improved gauge chart visualization for the cycling app
"""

def generate_improved_gauge_chart(sensor_key, value, label, unit, range_values):
    """
    Generate an improved ECharts gauge chart for sensor data
    
    Args:
        sensor_key (str): Key name of the sensor
        value (float): Current value of the sensor
        label (str): Display label for the sensor
        unit (str): Unit of measurement
        range_values (list): Min and max values for the gauge
        
    Returns:
        str: HTML component with ECharts gauge
    """
    min_val, max_val = range_values
    
    # Normalize value to 0-1 range for the gauge
    normalized_value = (value - min_val) / (max_val - min_val)
    normalized_value = max(0, min(1, normalized_value))
    
    # Define color ranges based on sensor type
    color_ranges = {
        "temperatura": [
            [0.25, '#FF6E76'],  # Cool
            [0.5, '#FDDD60'],   # Mild
            [0.75, '#58D9F9'],  # Moderate
            [1, '#7CFFB2']      # Hot
        ],
        "umidade": [
            [0.25, '#7CFFB2'],  # Dry
            [0.5, '#58D9F9'],   # Low
            [0.75, '#FDDD60'],  # Moderate
            [1, '#FF6E76']      # Humid
        ],
        "pressao": [
            [0.25, '#FF6E76'],  # Low
            [0.5, '#FDDD60'],   # Normal Low
            [0.75, '#58D9F9'],  # Normal High
            [1, '#7CFFB2']      # High
        ],
        "luminosidade": [
            [0.25, '#2B2E4A'],  # Dark
            [0.5, '#58D9F9'],   # Low Light
            [0.75, '#FDDD60'],  # Bright
            [1, '#FF6E76']      # Very Bright
        ]
    }
    
    # Get color ranges for this sensor or use default
    color_range = color_ranges.get(sensor_key, [
        [0.25, '#FF6E76'],
        [0.5, '#FDDD60'],
        [0.75, '#58D9F9'],
        [1, '#7CFFB2']
    ])
    
    # Format labels for the gauge based on sensor type
    label_formatter = ""
    if sensor_key == "temperatura":
        label_formatter = """
        function (value) {
          if (value === 0.875) {
            return 'Hot';
          } else if (value === 0.625) {
            return 'Warm';
          } else if (value === 0.375) {
            return 'Mild';
          } else if (value === 0.125) {
            return 'Cool';
          }
          return '';
        }
        """
    elif sensor_key == "umidade":
        label_formatter = """
        function (value) {
          if (value === 0.875) {
            return 'High';
          } else if (value === 0.625) {
            return 'Humid';
          } else if (value === 0.375) {
            return 'Mild';
          } else if (value === 0.125) {
            return 'Dry';
          }
          return '';
        }
        """
    elif sensor_key == "pressao":
        label_formatter = """
        function (value) {
          if (value === 0.875) {
            return 'High';
          } else if (value === 0.625) {
            return 'Normal';
          } else if (value === 0.375) {
            return 'Low';
          } else if (value === 0.125) {
            return 'Very Low';
          }
          return '';
        }
        """
    elif sensor_key == "luminosidade":
        label_formatter = """
        function (value) {
          if (value === 0.875) {
            return 'Bright';
          } else if (value === 0.625) {
            return 'Good';
          } else if (value === 0.375) {
            return 'Low';
          } else if (value === 0.125) {
            return 'Dark';
          }
          return '';
        }
        """
    else:
        label_formatter = """
        function (value) {
          if (value === 0.875) {
            return 'High';
          } else if (value === 0.625) {
            return 'Good';
          } else if (value === 0.375) {
            return 'Low';
          } else if (value === 0.125) {
            return 'Poor';
          }
          return '';
        }
        """
    
    # Generate the chart HTML
    html = f"""
    <div id="{sensor_key}_gauge" style="width:100%;height:250px;"></div>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <script>
      var chart = echarts.init(document.getElementById('{sensor_key}_gauge'));
      var option = {{
        series: [
          {{
            type: 'gauge',
            startAngle: 180,
            endAngle: 0,
            center: ['50%', '75%'],
            radius: '90%',
            min: 0,
            max: 1,
            splitNumber: 8,
            axisLine: {{
              lineStyle: {{
                width: 6,
                color: {str(color_range)}
              }}
            }},
            pointer: {{
              icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
              length: '12%',
              width: 20,
              offsetCenter: [0, '-60%'],
              itemStyle: {{
                color: 'auto'
              }}
            }},
            axisTick: {{
              length: 12,
              lineStyle: {{
                color: 'auto',
                width: 2
              }}
            }},
            splitLine: {{
              length: 20,
              lineStyle: {{
                color: 'auto',
                width: 5
              }}
            }},
            axisLabel: {{
              color: '#464646',
              fontSize: 14,
              distance: -60,
              rotate: 'tangential',
              formatter: {label_formatter}
            }},
            title: {{
              offsetCenter: [0, '-10%'],
              fontSize: 16,
              color: '#fff'
            }},
            detail: {{
              fontSize: 22,
              offsetCenter: [0, '-35%'],
              valueAnimation: true,
              formatter: function (value) {{
                return '{value:.1f} {unit}';
              }},
              color: 'inherit'
            }},
            data: [
              {{
                value: {normalized_value},
                name: '{label}'
              }}
            ]
          }}
        ]
      }};
      
      // Convert the normalized value back to actual value for display
      option.series[0].data[0].value = {value:.1f};
      
      chart.setOption(option);
      window.addEventListener('resize', function() {{
        chart.resize();
      }});
    </script>
    """.replace("'{value:.1f} {unit}'", "'" + str(value) + " " + unit + "'")
    
    return html
