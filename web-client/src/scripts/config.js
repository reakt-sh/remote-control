const SERVER = 'wt.rtsys-lab.de'
const WS_PORT = 8000
const QUIC_PORT = 4437
const SERVER_URL = `https://${SERVER}:${WS_PORT}`
const WS_URL = `wss://${SERVER}:${WS_PORT}`
const QUIC_URL = `https://${SERVER}:${QUIC_PORT}`
export { SERVER_URL, WS_URL, QUIC_URL }