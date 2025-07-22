from flask import Flask, render_template, request
import mysql.connector
from datetime import datetime
import requests
import pytz
import logging

app = Flask(__name__)

# 配置日志，输出到控制台
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

@app.route('/')
def show_data():
    try:
        logging.debug("尝试连接本地数据库...")
        # 本地数据库查询
        conn_local = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="root123",
            database="my_heat_data"
        )
        cursor_local = conn_local.cursor()
        cursor_local.execute("SELECT SupplyTemp FROM dat_heatsourceoutletdata ORDER BY GetTime DESC LIMIT 1")
        result = cursor_local.fetchone()
        latest_local_temp = result[0] if result and result[0] is not None else 0.0
        logging.debug(f"本地数据库查询结果: {result}")
        logging.info(f"最新就地温度: {latest_local_temp}°C")
        conn_local.close()

        # 远程数据库查询
        logging.debug("尝试连接远程数据库...")
        conn_remote = mysql.connector.connect(
            host="36.134.92.118",
            port=13326,
            user="hs_hc_xhgr",
            password="L#xhgr@2025",
            database="hs_hc_rl_xhgr"
        )
        cursor_remote = conn_remote.cursor()
        cursor_remote.execute("""
            SELECT 
                HeatSourceExportId,  -- 热源出口 ID
                GetTime,             -- 数据采集时间
                CumulativeFlow,      -- 累计流量
                InstantaneousFlow,   -- 瞬时流量
                CumulativeHeat,      -- 累计热量
                InstantaneousHeat,   -- 瞬时热量
                SupplyTemp,          -- 供水温度
                BackTemp,            -- 回水温度
                SupplyPre,           -- 供水压力
                BackPre              -- 回水压力
            FROM dat_heatsourceoutletdata 
            ORDER BY GetTime DESC 
            LIMIT 10
        """)
        data = cursor_remote.fetchall()
        logging.info(f"查询到 {len(data)} 条记录")
        conn_remote.close()

        # 北京时间
        beijing_tz = pytz.timezone('Asia/Shanghai')
        beijing_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M')
        date_str, time_str = beijing_time.split()

        # 天气数据
        latitude, longitude = 40.811, 111.652
        api_key = "ff631380a35a418ca30101758250707"
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={latitude},{longitude}&aqi=no"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            weather_data = response.json()
            weather_temp = weather_data['current']['temp_c']
            weather_code = weather_data['current']['condition']['code']
            weather_status = {
                1000: "晴", 1006: "阴", 1009: "阴", 
                1063: "小雨", 1150: "小雨", 1153: "小雨",
                1183: "中雨", 1186: "中雨", 1198: "中雨",
                1189: "大雨", 1192: "大雨", 1240: "大雨",
                1195: "暴雨", 1243: "暴雨",
                1066: "小雪", 1114: "小雪", 1210: "小雪", 1213: "小雪",
                1216: "中雪", 1219: "中雪",
                1222: "大雪", 1225: "大雪",
                1072: "冻雨", 1168: "冻雨", 1171: "冻雨"
            }.get(weather_code, "未知")
            windspeed = weather_data['current']['wind_kph'] / 3.6
            wind_level = {
                (0.3, 1.6): "1级 微风", (1.6, 3.3): "2级 轻风", (3.3, 5.4): "3级 微风",
                (5.4, 7.9): "4级 和风", (7.9, 10.7): "5级 清风", (10.7, 13.8): "6级 强风",
                (13.8, 17.1): "7级 疾风", (17.1, 20.7): "8级 大风", (20.7, 24.4): "9级 烈风",
                (24.4, 28.4): "10级 狂风", (28.4, 32.6): "11级 暴风"
            }.get(next((r for r in [(0.3, 1.6), (1.6, 3.3), (3.3, 5.4), (5.4, 7.9), (7.9, 10.7), 
                                   (10.7, 13.8), (13.8, 17.1), (17.1, 20.7), (20.7, 24.4), 
                                   (24.4, 28.4), (28.4, 32.6)] if r[0] <= windspeed < r[1]), None), 
                  "12级 飓风" if windspeed > 32.6 else "无风")
            winddirection = weather_data['current']['wind_degree']
            wind_direction = {
                (0, 22.5): "北风", (22.5, 67.5): "东北风", (67.5, 112.5): "东风",
                (112.5, 157.5): "东南风", (157.5, 202.5): "南风", (202.5, 247.5): "西南风",
                (247.5, 292.5): "西风", (292.5, 337.5): "西北风", (337.5, 360): "北风"
            }.get(next((r for r in [(0, 22.5), (22.5, 67.5), (67.5, 112.5), (112.5, 157.5), 
                                   (157.5, 202.5), (202.5, 247.5), (247.5, 292.5), 
                                   (292.5, 337.5), (337.5, 360)] if r[0] <= winddirection < r[1]), None), 
                  "无风向")
            logging.info(f"天气数据: 温度={weather_temp}°C, 状况={weather_status}")

        except requests.RequestException as e:
            logging.error(f"天气 API 请求错误: {str(e)}")
            weather_temp = weather_status = wind_level = wind_direction = "未知"

        return render_template('index.html', data=data, date=date_str, time=time_str,
                              weather_temp=weather_temp, weather_status=weather_status,
                              wind_level=wind_level, wind_direction=wind_direction,
                              latest_local_temp=latest_local_temp)

    except Exception as e:
        logging.error(f"数据库错误: {str(e)}")
        return f"Error loading data: {str(e)}", 500

@app.route('/data', methods=['POST'])
def receive_data():
    try:
        logging.debug(f"Raw data: {request.data}")
        logging.debug(f"Form data: {request.form}")
        temp = request.form.get('TEMP', '0.0')
        logging.debug(f"解析温度: {temp}")
        temp_float = float(temp)
        if temp_float == 0.0:
            logging.warning("警告: 温度值为 0.0，可能未正确接收数据")
            return "Invalid temperature", 400
        conn = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="root123",
            database="my_heat_data"
        )
        cursor = conn.cursor()
        cursor.execute("INSERT INTO dat_heatsourceoutletdata (GetTime, SupplyTemp) VALUES (NOW(), %s)", (temp_float,))
        conn.commit()
        logging.info("数据插入成功")
        conn.close()
        return "Data received", 200
    except ValueError:
        logging.error(f"温度解析错误: {temp} 不是有效数字")
        return f"Error: Invalid temperature format", 400
    except Exception as e:
        logging.error(f"数据插入错误: {str(e)}")
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    logging.info("启动 Flask 应用...")
    app.run(debug=True, port=10000, host='0.0.0.0')