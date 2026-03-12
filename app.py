import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Flask, render_template_string, request, jsonify
import requests
from datetime import datetime, timedelta
import io
import base64
import numpy as np
import json
import csv
from pathlib import Path

app = Flask(__name__)

DATA_DIR = Path('weather_data')
DATA_DIR.mkdir(exist_ok=True)

SHAHARLAR = {
    'toshkent': {
        'name': 'Toshkent', 'lat': 41.2995, 'lon': 69.2401,
        'region': 'Toshkent viloyati', 'population': '2,574,000',
        'area': '334.8 km²', 'timezone': 'Asia/Tashkent'
    },
    'samarqand': {
        'name': 'Samarqand', 'lat': 39.6270, 'lon': 66.9750,
        'region': 'Samarqand viloyati', 'population': '546,000',
        'area': '108 km²', 'timezone': 'Asia/Samarkand'
    },
    'buxoro': {
        'name': 'Buxoro', 'lat': 39.7744, 'lon': 64.4286,
        'region': 'Buxoro viloyati', 'population': '280,000',
        'area': '39.4 km²', 'timezone': 'Asia/Samarkand'
    },
    'xiva': {
        'name': 'Xiva', 'lat': 41.3781, 'lon': 60.3640,
        'region': 'Xorazm viloyati', 'population': '89,000',
        'area': '8.3 km²', 'timezone': 'Asia/Samarkand'
    },
    'urganch': {
        'name': 'Urganch', 'lat': 41.5500, 'lon': 60.6333,
        'region': 'Xorazm viloyati', 'population': '140,000',
        'area': '29 km²', 'timezone': 'Asia/Samarkand'
    },
    'andijon': {
        'name': 'Andijon', 'lat': 40.7821, 'lon': 72.3442,
        'region': 'Andijon viloyati', 'population': '441,700',
        'area': '74.3 km²', 'timezone': 'Asia/Tashkent'
    },
    'namangan': {
        'name': 'Namangan', 'lat': 41.0011, 'lon': 71.6725,
        'region': 'Namangan viloyati', 'population': '597,000',
        'area': '145 km²', 'timezone': 'Asia/Tashkent'
    },
    'fargona': {
        'name': "Farg'ona", 'lat': 40.3842, 'lon': 71.7843,
        'region': "Farg'ona viloyati", 'population': '288,000',
        'area': '95.6 km²', 'timezone': 'Asia/Tashkent'
    },
    'qarshi': {
        'name': 'Qarshi', 'lat': 38.8606, 'lon': 65.7891,
        'region': 'Qashqadaryo viloyati', 'population': '260,000',
        'area': '74.3 km²', 'timezone': 'Asia/Samarkand'
    },
    'termiz': {
        'name': 'Termiz', 'lat': 37.2242, 'lon': 67.2783,
        'region': 'Surxondaryo viloyati', 'population': '136,200',
        'area': '36 km²', 'timezone': 'Asia/Samarkand'
    },
    'guliston': {
        'name': 'Guliston', 'lat': 40.4897, 'lon': 68.7842,
        'region': 'Sirdaryo viloyati', 'population': '90,300',
        'area': '20.3 km²', 'timezone': 'Asia/Tashkent'
    },
    'jizzax': {
        'name': 'Jizzax', 'lat': 40.1158, 'lon': 67.8422,
        'region': 'Jizzax viloyati', 'population': '170,000',
        'area': '50 km²', 'timezone': 'Asia/Samarkand'
    },
    'navoiy': {
        'name': 'Navoiy', 'lat': 40.0844, 'lon': 65.3792,
        'region': 'Navoiy viloyati', 'population': '144,200',
        'area': '35 km²', 'timezone': 'Asia/Samarkand'
    }
}

def get_uzbek_day(english_day):
    kunlar = {
        'Monday': 'Dushanba', 'Tuesday': 'Seshanba', 'Wednesday': 'Chorshanba',
        'Thursday': 'Payshanba', 'Friday': 'Juma', 'Saturday': 'Shanba', 'Sunday': 'Yakshanba'
    }
    return kunlar.get(english_day, english_day)

def get_uzbek_month(month_num):
    oylar = {
        1: 'Yanvar', 2: 'Fevral', 3: 'Mart', 4: 'Aprel',
        5: 'May', 6: 'Iyun', 7: 'Iyul', 8: 'Avgust',
        9: 'Sentabr', 10: 'Oktabr', 11: 'Noyabr', 12: 'Dekabr'
    }
    return oylar.get(month_num, '')

def get_weather_condition(temp, precipitation):
    if precipitation > 5:
        return {'name': 'Kuchli yomg\'ir', 'icon': '🌧️', 'color': '#4A90E2', 'bg': '#E6F0FA'}
    elif precipitation > 2:
        return {'name': 'Yomg\'ir', 'icon': '🌦️', 'color': '#357ABD', 'bg': '#F0F5FA'}
    elif precipitation > 0.5:
        return {'name': 'Yengil yomg\'ir', 'icon': '☔', 'color': '#5C9BD5', 'bg': '#F5F8FA'}
    elif temp >= 35:
        return {'name': 'Jazirama issiq', 'icon': '☀️', 'color': '#FF6B6B', 'bg': '#FFE5B4'}
    elif temp >= 30:
        return {'name': 'Quyoshli', 'icon': '☀️', 'color': '#FF8C42', 'bg': '#FFF2D7'}
    elif temp >= 25:
        return {'name': 'Ochiq', 'icon': '⛅', 'color': '#F4A261', 'bg': '#FFFFFF'}
    elif temp >= 20:
        return {'name': 'Ochiq', 'icon': '⛅', 'color': '#6B7280', 'bg': '#F8F9FA'}
    elif temp >= 15:
        return {'name': 'Bulutli', 'icon': '☁️', 'color': '#64748B', 'bg': '#F0F2F5'}
    elif temp >= 10:
        return {'name': 'Bulutli', 'icon': '☁️', 'color': '#475569', 'bg': '#E9ECEF'}
    else:
        return {'name': 'Salqin', 'icon': '🌥️', 'color': '#334155', 'bg': '#E1E8ED'}

def save_weather_data(city_key, forecast_data, days):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    city = SHAHARLAR[city_key]['name']
    
    json_data = {
        'city': city, 'city_key': city_key,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'forecast_days': days, 'forecast': forecast_data
    }
    
    json_file = DATA_DIR / f"{city_key}_{days}kun_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    csv_file = DATA_DIR / f"{city_key}_{days}kun_{timestamp}.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Sana', 'Hafta kuni', 'Max °C', 'Min °C', "Yog'in mm", 'Shamol m/s', 'Holat'])
        for day in forecast_data:
            writer.writerow([
                day['full_date'], day['weekday'], day['temp_max'],
                day['temp_min'], day['precipitation'], day['wind_speed'],
                day['condition']['name']
            ])

def fetch_weather_from_api(city_key, days):
    city = SHAHARLAR[city_key]
    params = {
        "latitude": city['lat'], "longitude": city['lon'],
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "wind_speed_10m_max"],
        "timezone": city['timezone'], "forecast_days": days
    }
    try:
        response = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None

def process_api_data(api_data, days):
    forecast = []
    today = datetime.now().date()
    for i in range(days):
        current_date = today + timedelta(days=i+1)
        temp_max = round(api_data['daily']['temperature_2m_max'][i])
        temp_min = round(api_data['daily']['temperature_2m_min'][i])
        precipitation = api_data['daily']['precipitation_sum'][i]
        wind_speed = round(api_data['daily']['wind_speed_10m_max'][i], 1)
        condition = get_weather_condition(temp_max, precipitation)
        weekday = get_uzbek_day(current_date.strftime('%A'))
        forecast.append({
            'date': current_date.strftime('%d.%m'), 'full_date': current_date.strftime('%d.%m.%Y'),
            'weekday': weekday, 'weekday_short': weekday[:2],
            'temp_max': temp_max, 'temp_min': temp_min,
            'precipitation': precipitation, 'wind_speed': wind_speed,
            'condition': condition
        })
    return forecast

def generate_test_forecast(city_key, days):
    city = SHAHARLAR[city_key]
    forecast = []
    today = datetime.now().date()
    for i in range(days):
        current_date = today + timedelta(days=i+1)
        month = current_date.month
        if 6 <= month <= 8:
            base_temp = 35
        elif 3 <= month <= 5:
            base_temp = 25
        elif 9 <= month <= 11:
            base_temp = 20
        else:
            base_temp = 10
        temp_max = base_temp + np.random.randint(-3, 4)
        temp_min = temp_max - 8 - np.random.randint(0, 3)
        precipitation = np.random.choice([0, 0, 0, 0.5, 1, 2])
        wind_speed = round(4 + 3 * np.random.random(), 1)
        condition = get_weather_condition(temp_max, precipitation)
        weekday = get_uzbek_day(current_date.strftime('%A'))
        forecast.append({
            'date': current_date.strftime('%d.%m'), 'full_date': current_date.strftime('%d.%m.%Y'),
            'weekday': weekday, 'weekday_short': weekday[:2],
            'temp_max': temp_max, 'temp_min': temp_min,
            'precipitation': precipitation, 'wind_speed': wind_speed,
            'condition': condition
        })
    return forecast

def get_weather(city_key, days=7):
    api_data = fetch_weather_from_api(city_key, days)
    if api_data:
        forecast = process_api_data(api_data, days)
    else:
        forecast = generate_test_forecast(city_key, days)
    save_weather_data(city_key, forecast, days)
    return forecast

def create_weather_chart(forecast, city_name):
    fig = plt.figure(figsize=(14, 8))
    gs = fig.add_gridspec(2, 1, height_ratios=[2, 1], hspace=0.15)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    
    dates = [f['date'] for f in forecast]
    temp_max = [f['temp_max'] for f in forecast]
    temp_min = [f['temp_min'] for f in forecast]
    precipitation = [f['precipitation'] for f in forecast]
    
    ax1.plot(dates, temp_max, 'o-', color='#FF6B6B', linewidth=3,
             markersize=10, label='Maksimal', markerfacecolor='white',
             markeredgewidth=2.5, markeredgecolor='#FF6B6B')
    ax1.plot(dates, temp_min, 'o-', color='#4A90E2', linewidth=3,
             markersize=10, label='Minimal', markerfacecolor='white',
             markeredgewidth=2.5, markeredgecolor='#4A90E2')
    ax1.fill_between(dates, temp_min, temp_max, alpha=0.15, color='#FFB347')
    
    max_val = max(temp_max)
    min_val = min(temp_min)
    max_idx = temp_max.index(max_val)
    min_idx = temp_min.index(min_val)
    
    ax1.annotate(f'{max_val}°C', xy=(max_idx, max_val), xytext=(10, 10),
                 textcoords='offset points', fontsize=11, fontweight='bold',
                 color='#FF6B6B', bbox=dict(boxstyle='round,pad=0.3',
                                            facecolor='white', alpha=0.8))
    ax1.annotate(f'{min_val}°C', xy=(min_idx, min_val), xytext=(10, -20),
                 textcoords='offset points', fontsize=11, fontweight='bold',
                 color='#4A90E2', bbox=dict(boxstyle='round,pad=0.3',
                                            facecolor='white', alpha=0.8))
    
    ax1.set_ylabel('Harorat (°C)', fontsize=12, fontweight='500', color='#2C3E50')
    ax1.legend(loc='upper right', frameon=True, fancybox=True, shadow=True, fontsize=11)
    ax1.grid(True, alpha=0.2, linestyle='--')
    ax1.set_ylim([min(temp_min)-5, max(temp_max)+5])
    ax1.set_title(f'{city_name} · {len(forecast)} kunlik havo prognozi',
                  fontsize=16, fontweight='600', color='#1E293B', pad=20)
    
    colors = ['#4A90E2' if x > 0 else '#E8E8E8' for x in precipitation]
    bars = ax2.bar(dates, precipitation, color=colors, alpha=0.8)
    
    for bar, val in zip(bars, precipitation):
        if val > 0:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{val} mm', ha='center', va='bottom', fontsize=9,
                    fontweight='500', color='#2C3E50')
    
    ax2.set_ylabel("Yog'ingarchilik (mm)", fontsize=12, fontweight='500', color='#2C3E50')
    ax2.set_xlabel('Sana', fontsize=12, fontweight='500', color='#2C3E50')
    ax2.grid(True, alpha=0.2, axis='y', linestyle='--')
    
    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    img.seek(0)
    plt.close(fig)
    return base64.b64encode(img.getvalue()).decode()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ city_name }} ob-havo</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(145deg, #F0F4F8 0%, #E6ECF2 100%);
            color: #1E293B;
            min-height: 100vh;
            padding: 24px;
        }
        .container { max-width: 1440px; margin: 0 auto; }
        .card {
            background: rgba(255,255,255,0.9);
            backdrop-filter: blur(20px);
            border-radius: 32px;
            padding: 24px;
            box-shadow: 0 20px 40px -12px rgba(0,0,0,0.15);
            border: 1px solid rgba(255,255,255,0.6);
            margin-bottom: 24px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 24px;
        }
        .title h1 {
            font-size: 36px;
            font-weight: 700;
            background: linear-gradient(135deg, #1E293B, #334155);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
            margin-bottom: 4px;
        }
        .title p { color: #64748B; font-size: 15px; display: flex; align-items: center; gap: 8px; }
        .date-badge {
            background: white;
            padding: 12px 24px;
            border-radius: 60px;
            font-size: 15px;
            font-weight: 500;
            color: #1E293B;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid rgba(255,255,255,0.8);
        }
        .date-badge i { color: #3B82F6; margin-right: 8px; }
        .search-box {
            background: white;
            border: 1px solid #E2E8F0;
            border-radius: 60px;
            padding: 4px 4px 4px 20px;
            display: flex;
            align-items: center;
            max-width: 400px;
            margin-bottom: 24px;
            transition: all 0.2s;
        }
        .search-box:focus-within { border-color: #3B82F6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
        .search-box i { color: #94A3B8; font-size: 18px; }
        .search-box input {
            flex: 1;
            border: none;
            padding: 12px 16px;
            font-size: 15px;
            font-family: 'Inter', sans-serif;
            outline: none;
            background: transparent;
        }
        .search-box button {
            background: #1E293B;
            border: none;
            color: white;
            padding: 10px 24px;
            border-radius: 40px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .search-box button:hover { background: #0F172A; }
        .cities-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 10px;
            margin-top: 16px;
        }
        .city-card {
            background: #F8FAFC;
            border-radius: 20px;
            padding: 14px 8px;
            text-align: center;
            text-decoration: none;
            color: #334155;
            font-weight: 600;
            font-size: 14px;
            border: 1px solid #E2E8F0;
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
        }
        .city-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #3B82F6, #8B5CF6);
            opacity: 0;
            transition: opacity 0.2s ease;
        }
        .city-card:hover {
            background: white;
            border-color: #3B82F6;
            transform: translateY(-2px);
            box-shadow: 0 10px 20px -8px rgba(59,130,246,0.3);
        }
        .city-card:hover::before { opacity: 1; }
        .city-card.active {
            background: linear-gradient(135deg, #3B82F6, #8B5CF6);
            color: white;
            border-color: transparent;
            box-shadow: 0 10px 20px -8px rgba(59,130,246,0.5);
        }
        .city-card small { display: block; font-size: 10px; opacity: 0.7; margin-top: 4px; font-weight: 400; }
        .days-section {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
            margin: 24px 0;
        }
        .day-btn {
            padding: 12px 28px;
            border-radius: 60px;
            font-size: 15px;
            font-weight: 600;
            color: #475569;
            background: white;
            border: 1px solid #E2E8F0;
            text-decoration: none;
            transition: all 0.2s ease;
        }
        .day-btn:hover {
            background: #F8FAFC;
            border-color: #94A3B8;
            transform: translateY(-2px);
        }
        .day-btn.active {
            background: #1E293B;
            color: white;
            border-color: #1E293B;
        }
        .chart-container {
            background: white;
            border-radius: 28px;
            padding: 20px;
            margin-bottom: 28px;
            border: 1px solid rgba(255,255,255,0.9);
        }
        .chart-container img { width: 100%; height: auto; border-radius: 16px; }
        .forecast-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }
        .forecast-card {
            background: white;
            border-radius: 24px;
            padding: 20px 16px;
            border: 1px solid #E2E8F0;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .forecast-card::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #3B82F6, #8B5CF6);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        .forecast-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 20px 30px -10px rgba(0,0,0,0.1);
            border-color: transparent;
        }
        .forecast-card:hover::after { opacity: 1; }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        .day-name { font-weight: 700; font-size: 18px; color: #0F172A; }
        .date {
            font-size: 13px;
            color: #64748B;
            background: #F1F5F9;
            padding: 4px 8px;
            border-radius: 20px;
        }
        .weather-icon {
            font-size: 56px;
            text-align: center;
            margin: 12px 0;
            filter: drop-shadow(0 8px 12px rgba(0,0,0,0.1));
        }
        .temperature { text-align: center; margin: 12px 0; }
        .temp-max { font-size: 38px; font-weight: 700; color: #0F172A; line-height: 1; }
        .temp-min { font-size: 20px; font-weight: 500; color: #64748B; margin-left: 6px; }
        .condition {
            text-align: center;
            font-size: 15px;
            font-weight: 600;
            color: {{ forecast[0].condition.color if forecast else '#3B82F6' }};
            margin: 16px 0;
            padding: 6px 0;
            border-top: 1px dashed #E2E8F0;
            border-bottom: 1px dashed #E2E8F0;
        }
        .details {
            display: flex;
            justify-content: space-around;
            margin-top: 16px;
        }
        .detail-item { text-align: center; }
        .detail-value { font-weight: 700; font-size: 16px; color: #0F172A; }
        .detail-label {
            font-size: 11px;
            color: #94A3B8;
            margin-top: 4px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }
        .city-info {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin: 20px 0;
            padding: 16px;
            background: #F8FAFC;
            border-radius: 20px;
        }
        .info-item {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #475569;
            font-size: 14px;
        }
        .info-item i { color: #3B82F6; font-size: 16px; }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 24px;
            border-top: 2px solid rgba(255,255,255,0.8);
            color: #64748B;
            font-size: 14px;
        }
        .footer i { color: #EF4444; }
        .loading {
            display: inline-block;
            width: 24px;
            height: 24px;
            border: 3px solid #E2E8F0;
            border-top-color: #3B82F6;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .no-results {
            text-align: center;
            padding: 30px;
            color: #94A3B8;
            grid-column: 1 / -1;
        }
        .no-results i { font-size: 40px; margin-bottom: 10px; color: #CBD5E1; }
        @media (max-width: 768px) {
            body { padding: 12px; }
            .title h1 { font-size: 28px; }
            .header { flex-direction: column; align-items: flex-start; }
            .cities-grid { grid-template-columns: repeat(3, 1fr); }
        }
        @media (max-width: 480px) {
            .cities-grid { grid-template-columns: repeat(2, 1fr); }
            .forecast-grid { grid-template-columns: 1fr; }
            .days-section { justify-content: flex-start; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="header">
                <div class="title">
                    <h1><i class="fas fa-cloud-sun" style="color: #3B82F6; margin-right: 10px;"></i>O'zbekiston ob-havo</h1>
                    <p><i class="fas fa-map-marker-alt" style="color: #EF4444;"></i> {{ city_name }} · {{ city_info.region }}</p>
                </div>
                <div class="date-badge"><i class="fas fa-calendar-alt"></i> {{ current_date }}</div>
            </div>
            
            <div class="city-info">
                <div class="info-item"><i class="fas fa-users"></i> Aholisi: {{ city_info.population }}</div>
                <div class="info-item"><i class="fas fa-map"></i> Maydoni: {{ city_info.area }}</div>
                <div class="info-item"><i class="fas fa-clock"></i> Vaqt mintaqasi: {{ city_info.timezone }}</div>
            </div>
            
            <div class="search-box">
                <i class="fas fa-search"></i>
                <input type="text" id="citySearch" placeholder="Shaharni qidirish..." autocomplete="off">
                <button onclick="filterCities()"><i class="fas fa-filter"></i> Filter</button>
            </div>
            
            <div style="margin-top: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-weight: 600; color: #64748B;"><i class="fas fa-building"></i> Barcha shaharlar ({{ shaharlar|length }})</span>
                    <span style="font-size: 13px; color: #94A3B8;" id="cityCount">Hammasi</span>
                </div>
                <div class="cities-grid" id="citiesGrid">
                    {% for key, city in shaharlar.items() %}
                    <a href="/?shahar={{ key }}&days={{ days }}" 
                       class="city-card {% if shahar == key %}active{% endif %}"
                       data-name="{{ city.name|lower }}">
                        {{ city.name }}
                        <small>{{ city.region.split(' ')[0] }}</small>
                    </a>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <div class="days-section">
            <a href="/?shahar={{ shahar }}&days=3" class="day-btn {% if days == 3 %}active{% endif %}">3 kun</a>
            <a href="/?shahar={{ shahar }}&days=5" class="day-btn {% if days == 5 %}active{% endif %}">5 kun</a>
            <a href="/?shahar={{ shahar }}&days=7" class="day-btn {% if days == 7 %}active{% endif %}">7 kun</a>
            <a href="/?shahar={{ shahar }}&days=10" class="day-btn {% if days == 10 %}active{% endif %}">10 kun</a>
            <a href="/?shahar={{ shahar }}&days=14" class="day-btn {% if days == 14 %}active{% endif %}">14 kun</a>
        </div>
        
        <div class="card chart-container">
            <img src="data:image/png;base64,{{ chart }}" alt="Harorat grafigi">
        </div>
        
        <div class="forecast-grid">
            {% for day in forecast %}
            <div class="forecast-card" style="background: linear-gradient(145deg, white, {{ day.condition.bg }});">
                <div class="card-header">
                    <span class="day-name">{{ day.weekday_short }}</span>
                    <span class="date">{{ day.date }}</span>
                </div>
                <div class="weather-icon">{{ day.condition.icon }}</div>
                <div class="temperature">
                    <span class="temp-max">{{ day.temp_max }}°</span>
                    <span class="temp-min">{{ day.temp_min }}°</span>
                </div>
                <div class="condition" style="color: {{ day.condition.color }};">{{ day.condition.name }}</div>
                <div class="details">
                    <div class="detail-item">
                        <div class="detail-value">{{ "%.1f"|format(day.precipitation) }}</div>
                        <div class="detail-label"><i class="fas fa-tint"></i> mm</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-value">{{ "%.1f"|format(day.wind_speed) }}</div>
                        <div class="detail-label"><i class="fas fa-wind"></i> m/s</div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
       
    </div>
    
    <script>
        function filterCities() {
            const input = document.getElementById('citySearch');
            const filter = input.value.toLowerCase().trim();
            const cities = document.querySelectorAll('.city-card');
            let visibleCount = 0;
            
            cities.forEach(city => {
                const text = city.textContent.toLowerCase();
                if (filter === '' || text.includes(filter)) {
                    city.style.display = '';
                    visibleCount++;
                } else {
                    city.style.display = 'none';
                }
            });
            
            const countSpan = document.getElementById('cityCount');
            if (countSpan) {
                if (filter === '') {
                    countSpan.textContent = 'Hammasi';
                } else {
                    countSpan.textContent = visibleCount + ' ta topildi';
                }
            }
            
            let noResults = document.getElementById('noResults');
            if (visibleCount === 0) {
                if (!noResults) {
                    const msg = document.createElement('div');
                    msg.id = 'noResults';
                    msg.className = 'no-results';
                    msg.innerHTML = '<i class="fas fa-cloud-rain"></i><br>Hech qanday shahar topilmadi';
                    document.getElementById('citiesGrid').appendChild(msg);
                }
            } else {
                if (noResults) noResults.remove();
            }
        }
        
        document.getElementById('citySearch').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') filterCities();
        });
        
        document.addEventListener('DOMContentLoaded', function() {
            const searchInput = document.getElementById('citySearch');
            if (searchInput) searchInput.value = '';
            
            const cards = document.querySelectorAll('.forecast-card');
            cards.forEach(card => {
                card.addEventListener('mouseenter', function() { this.style.transform = 'translateY(-6px)'; });
                card.addEventListener('mouseleave', function() { this.style.transform = 'translateY(0)'; });
            });
            
            const activeCard = document.querySelector('.city-card.active');
            if (activeCard) {
                setTimeout(() => {
                    activeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
                }, 100);
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    shahar = request.args.get('shahar', 'toshkent')
    days = request.args.get('days', 7, type=int)
    if days < 1: days = 1
    if days > 16: days = 16
    if shahar not in SHAHARLAR: shahar = 'toshkent'
    
    forecast = get_weather(shahar, days)
    city_info = SHAHARLAR[shahar]
    chart = create_weather_chart(forecast, city_info['name'])
    
    now = datetime.now()
    current_date = f"{now.day} {get_uzbek_month(now.month)} {now.year}"
    update_time = now.strftime('%H:%M:%S')
    
    return render_template_string(
        HTML_TEMPLATE,
        forecast=forecast, chart=chart, shahar=shahar, days=days,
        shaharlar=SHAHARLAR, city_name=city_info['name'],
        city_info=city_info, current_date=current_date, update_time=update_time
    )

@app.route('/api/weather/<city>')
def api_weather(city):
    days = request.args.get('days', 7, type=int)
    if city not in SHAHARLAR:
        return jsonify({'error': 'Shahar topilmadi'}), 404
    forecast = get_weather(city, days)
    city_info = SHAHARLAR[city]
    return jsonify({
        'city': city_info['name'], 'region': city_info['region'],
        'forecast': forecast, 'updated': datetime.now().isoformat()
    })

@app.route('/api/cities')
def api_cities():
    cities = []
    for key, info in SHAHARLAR.items():
        cities.append({'id': key, 'name': info['name'], 'region': info['region']})
    return jsonify(cities)

@app.route('/api/health')
def api_health():
    return jsonify({
        'status': 'healthy', 'timestamp': datetime.now().isoformat(),
        'cities': len(SHAHARLAR), 'data_dir': str(DATA_DIR)
    })


import os




import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

TOKEN = "7727645806:AAG7M5WxZ3aKrEil7onoaBBYPdXrE54YfaA"

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude":41.2995,
        "longitude":69.2401,
        "current_weather":True
    }

    r = requests.get(url,params=params).json()

    temp = r["current_weather"]["temperature"]

    await update.message.reply_text(f"🌤 Toshkent ob-havo\n🌡 {temp}°C")

def run_bot():

    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("weather",weather))

    app_bot.run_polling()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))

    # botni alohida threadda ishga tushiramiz
    threading.Thread(target=run_bot, daemon=True).start()

    app.run(host='0.0.0.0', port=port)
