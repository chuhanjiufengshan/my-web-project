from flask import Flask, render_template, request
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

        # 获取最新就地实时温度
        cursor.execute("SELECT SupplyTemp FROM dat_heatsourceoutletdata ORDER BY GetTime DESC LIMIT 1")
        latest_local_temp = cursor.fetchone()
        latest_local_temp = latest_local_temp[0] if latest_local_temp else 0.0

        beijing_tz = pytz.timezone('Asia/Shanghai')
        beijing_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M')
        date_str = beijing_time.split()[0]
        time_str = beijing_time.split()[1]

        latitude = 40.811
        longitude = 111.652
        api_key = "ff631380a35a418ca30101758250707"
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={latitude},{longitude}&aqi=no"
        try:
            response = requests.get(url, timeout=5)
            weather_data = response.json()
            print("WeatherAPI Response:", weather_data)
            weather_temp = weather_data['current']['temp_c']
            weather_code = weather_data['current']['condition']['code']

            weather_status = "晴天"
            if weather_code in [1063, 1150, 1153]:  # 毛毛雨
                weather_status = "毛毛雨"
            elif weather_code in [1183, 1186, 1198]:  # 小雨
                weather_status = "小雨"
            elif weather_code in [1189, 1192, 1240]:  # 中雨
                weather_status = "中雨"
            elif weather_code in [1195, 1243]:  # 大雨
                weather_status = "大雨"
            elif weather_code in [1198, 1201]:  # 暴雨
                weather_status = "暴雨"
            elif weather_code in [1006, 1030, 1003]:  # 阴天或多云
                weather_status = "阴"
            elif weather_code == 1000:  # 晴天
                weather_status = "晴天"

            windspeed = weather_data['current']['wind_kph'] / 3.6
            winddirection = weather_data['current']['wind_degree']

            wind_level = "无风"
            if windspeed >= 0.3 and windspeed < 1.6:  # 1 级
                wind_level = "1级 微风"
            elif windspeed <= 3.3:  # 2 级
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
            weather_temp = 0.0
            weather_status = "未知"
            wind_level = "未知"
            wind_direction = ""

        conn.close()
        return render_template('index.html', data=data, date=date_str, time=time_str, 
                            latest_local_temp=latest_local_temp, 
                            weather_temp=weather_temp, 
                            weather_status=weather_status, 
                            wind_level=wind_level, 
                            wind_direction=wind_direction)

    @app.route('/data', methods=['POST'])
    def receive_data():
        try:
            data = request.data.decode('utf-8')
            conn = mysql.connector.connect(
                host="36.134.92.118",
                port=13326,
                user="hs_hc_xhgr",
                password="L#xhgr@2025",
                database="hs_hc_rl_xhgr"
            )
            cursor = conn.cursor()
            cursor.execute("INSERT INTO dat_heatsourceoutletdata (GetTime, SupplyTemp) VALUES (NOW(), %s)", (data.replace('TEMP:', ''),))
            conn.commit()
            conn.close()
            return "Data received", 200
        except Exception as e:
            return f"Error: {str(e)}", 500

    if __name__ == '__main__':
        app.run(debug=True, port=int(os.environ.get('PORT', 10000)), host='0.0.0.0')