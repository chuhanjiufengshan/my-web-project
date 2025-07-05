from flask import Flask, render_template
import mysql.connector
from datetime import datetime
import requests
import os

app = Flask(__name__)

@app.route('/')
def show_data():
    try:
        # 数据库连接
        conn = mysql.connector.connect(
            host="36.134.92.118",
            port=13326,
            user="hs_hc_xhgr",
            password="L#xhgr@2025",
            database="hs_hc_rl_xhgr"
        )
        cursor = conn.cursor()
        # 查询数据
        cursor.execute("SELECT * FROM dat_heatsourceoutletdata WHERE GetTime > '2025-06-01 00:00:00' ORDER BY GetTime DESC LIMIT 1000")
        data = cursor.fetchall()

        # 获取实时日期
        date_str = datetime.now().strftime('%Y-%m-%d')

        # 调用 Open-Meteo API 获取实时温度，基于 Hohhot 坐标
        latitude = 40.8463  # Hohhot 纬度
        longitude = 111.7330  # Hohhot 经度
        url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
        try:
            response = requests.get(url, timeout=5)
            weather_data = response.json()
            latest_temp = weather_data['current_weather']['temperature']
        except (requests.RequestException, KeyError, ValueError):
            # 如果 API 失败，获取本地温度
            cursor.execute("SELECT SupplyTemp FROM dat_heatsourceoutletdata ORDER BY GetTime DESC LIMIT 1")
            temp = cursor.fetchone()
            latest_temp = temp[0] if temp else 0

        conn.close()
        return render_template('index.html', data=data, date=date_str, latest_temp=latest_temp)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')