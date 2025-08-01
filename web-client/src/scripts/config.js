const SERVER = 'wt.rtsys-lab.de'
const WS_PORT = 8000
const QUIC_PORT = 4437
const MQTT_WS_PORT = 8084
const SERVER_URL = `https://${SERVER}:${WS_PORT}`
const WS_URL = `wss://${SERVER}:${WS_PORT}`
const QUIC_URL = `https://${SERVER}:${QUIC_PORT}`
const MQTT_BROKER_URL = `wss://${SERVER}:${MQTT_WS_PORT}/mqtt`
export { SERVER_URL, WS_URL, QUIC_URL, MQTT_BROKER_URL }