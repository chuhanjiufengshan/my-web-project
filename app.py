from flask import Flask, render_template
import mysql.connector
from datetime import datetime
import requests
import os
import pytz

app = Flask(__name__)

@app.route('/')
def show_data():
    try:
        conn = mysql.connector.connect(
            host="36.134.92.118",
            port=13326,
            user="hs_hc_xhgr",
            password="L#xhgr@2025",
            database="hs_hc_rl_xhgr"
        )
        cursor = conn.cursor()
        start_date = os.environ.get('START_DATE', '2025-07-01 00:00:00')
        cursor.execute("SELECT * FROM dat_heatsourceoutletdata WHERE GetTime >= %s ORDER BY GetTime DESC LIMIT 1000", (start_date,))
        data = cursor.fetchall()

        beijing_tz = pytz.timezone('Asia/Shanghai')
        beijing_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M')
        date_str = beijing_time.split()[0]
        time_str = beijing_time.split()[1]

        latitude = 40.8463
        longitude = 111.7330
        url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true&hourly=weathercode,temperature_2m,windspeed_10m,winddirection_10m"
        try:
            response = requests.get(url, timeout=5)
            weather_data = response.json()
            print("API Response:", weather_data)  # 调试输出
            current_weather = weather_data['current_weather']
            latest_temp = current_weather['temperature']
            weather_code = current_weather['weathercode']

            hourly_data = weather_data.get('hourly', {})
            if hourly_data:
                windspeed = hourly_data.get('windspeed_10m', [0])[-1]
                winddirection = hourly_data.get('winddirection_10m', [0])[-1]
            else:
                windspeed = 0
                winddirection = 0

            weather_status = "晴天"
            wind_level = "无风"
            if weather_code in [51, 53]:  # 毛毛雨
                weather_status = "毛毛雨"
            elif weather_code in [55, 61]:  # 小雨
                weather_status = "小雨"
            elif weather_code in [63, 80]:  # 中雨
                weather_status = "中雨"
            elif weather_code in [65, 81]:  # 大雨
                weather_status = "大雨"
            elif weather_code in [67, 82]:  # 暴雨
                weather_status = "暴雨"
            elif weather_code in [3, 45, 48]:  # 阴天
                weather_status = "阴"

            if windspeed >= 0.3 and windspeed <= 1.5:
                wind_level = "1级 微风"
            elif windspeed <= 3.3:
                wind_level = "2级 轻风"
            elif windspeed <= 5.4:
                wind_level = "3级 微风"
            elif windspeed <= 7.9:
                wind_level = "4级 和风"
            elif windspeed <= 10.7:
                wind_level = "5级 清风"
            elif windspeed <= 13.8:
                wind_level = "6级 强风"
            elif windspeed <= 17.1:
                wind_level = "7级 疾风"
            elif windspeed <= 20.7:
                wind_level = "8级 大风"
            elif windspeed <= 24.4:
                wind_level = "9级 烈风"
            elif windspeed <= 28.4:
                wind_level = "10级 狂风"
            elif windspeed <= 32.6:
                wind_level = "11级 暴风"
            else:
                wind_level = "12级 飓风"

            wind_direction = ""
            if 0 <= winddirection < 22.5 or 337.5 <= winddirection <= 360:
                wind_direction = "北风"
            elif 22.5 <= winddirection < 67.5:
                wind_direction = "东北风"
            elif 67.5 <= winddirection < 112.5:
                wind_direction = "东风"
            elif 112.5 <= winddirection < 157.5:
                wind_direction = "东南风"
            elif 157.5 <= winddirection < 202.5:
                wind_direction = "南风"
            elif 202.5 <= winddirection < 247.5:
                wind_direction = "西南风"
            elif 247.5 <= winddirection < 292.5:
                wind_direction = "西风"
            elif 292.5 <= winddirection < 337.5:
                wind_direction = "西北风"

        except (requests.RequestException, KeyError, ValueError) as e:
            print("Weather API Error:", e)
            cursor.execute("SELECT SupplyTemp FROM dat_heatsourceoutletdata ORDER BY GetTime DESC LIMIT 1")
            temp = cursor.fetchone()
            latest_temp = temp[0] if temp else 0
            weather_status = "未知"
            wind_level = "未知"
            wind_direction = ""

        conn.close()
        return render_template('index.html', data=data, date=date_str, time=time_str, latest_temp=latest_temp, weather_status=weather_status, wind_level=wind_level, wind_direction=wind_direction)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5001)), host='0.0.0.0')