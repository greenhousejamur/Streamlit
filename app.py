import streamlit as st
import paho.mqtt.client as mqtt
import plotly.graph_objects as go
import time

# --- SETUP HALAMAN ---
st.set_page_config(page_title="Greenhouse Jamur", page_icon="🍄", layout="wide")
st.title("🍄 Greenhouse Jamur")

# --- KONFIGURASI MQTT ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "elins/landslide/suhu"

# 1. MEMBUAT PENYIMPANAN GLOBAL (Bebas dari blokir Streamlit)
@st.cache_resource
def get_sensor_data():
    return {"suhu_dht22": 0.0, "kelembapan": 0.0, "lux": 0.0}

sensor_data = get_sensor_data()

# Callback saat pesan MQTT diterima
# Format payload dari ESP32: suhu,suhuBlynk,kelembapan,lux
def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")
    print(f"📥 Data masuk dari MQTT: {payload}")
    try:
        data = payload.split(",")
        if len(data) >= 1:
            # 2. UPDATE KE DICTIONARY GLOBAL, BUKAN KE SESSION_STATE
            # Pakai suhu MENTAH (indeks 0), bukan suhuBlynk (indeks 1)
            sensor_data["suhu_dht22"] = float(data[0])
        if len(data) >= 3:
            sensor_data["kelembapan"] = float(data[2])
        if len(data) >= 4:
            sensor_data["lux"] = float(data[3])
    except Exception as e:
        print("❌ Gagal parsing data:", e)

# 3. SETUP MQTT CLIENT LEBIH AMAN DENGAN CACHE
@st.cache_resource
def init_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(MQTT_TOPIC)
    client.loop_start()
    return client

# Jalankan MQTT
client = init_mqtt()

# --- KALIBRASI SUHU ---
# Y = 30 + (10/7) * (X - 30)
def kalibrasi_suhu(x):
    return 30 + (10 / 7) * (x - 30)

# --- UI KONDISI SENSOR ---
st.markdown("### 🌱 Kondisi Sensor")

def create_gauge(value, title, max_val, color, suffix=""):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 18, 'color': 'white'}},
        number={'valueformat': '.2f', 'suffix': suffix, 'font': {'size': 36, 'color': 'white'}},
        gauge={
            'axis': {'range': [0, max_val], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "#0e1117",
            'borderwidth': 0,
            'steps': [
                {'range': [0, max_val / 2], 'color': "#262730"},
                {'range': [max_val / 2, max_val], 'color': "#31333F"}
            ],
        }
    ))
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

col1, col2, col3 = st.columns(3)

# 4. BACA DATA DARI DICTIONARY GLOBAL
with col1:
    st.plotly_chart(
        create_gauge(sensor_data["lux"], "Intensitas Cahaya (TSL2561)", 1000, "#ffa15a", " lx"),
        width="stretch"
    )

with col2:
    st.plotly_chart(
        create_gauge(kalibrasi_suhu(sensor_data["suhu_dht22"]), "Suhu Udara (DHT22)", 50, "#00cc96", " °C"),
        width="stretch"
    )

with col3:
    st.plotly_chart(
        create_gauge(sensor_data["kelembapan"], "Kelembapan Udara (DHT22)", 100, "#636efa", " %"),
        width="stretch"
    )

st.divider()

time.sleep(2)
st.rerun()
