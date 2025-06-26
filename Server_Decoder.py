# Servidor Flask para decodificação de QR Code e registro de eventos IoT
from flask import Flask, request, jsonify
import requests
import logging
from pyzbar.pyzbar import decode as decode_pyzbar
from PIL import Image
import io
from datetime import datetime
import pytz

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')

app = Flask(__name__)

# --- Configurações ---
GOOGLE_SCRIPT_URL = "SUA_URL_DO_GOOGLE_APPS_SCRIPT_AQUI" 
LOCAL_TIMEZONE = pytz.timezone('America/Sao_Paulo')

# Variável global para armazenar o estado do evento ativo.
evento_ativo = None

@app.route('/registrar-evento', methods=['POST'])
def registrar_evento():
    global evento_ativo
    logging.info(f"Requisição recebida. Estado atual: {evento_ativo}")

    if not request.data:
        return jsonify({"status": "erro", "mensagem": "Nenhum dado de imagem recebido."}), 400
    
    try:
        identificador_qr = decode_pyzbar(Image.open(io.BytesIO(request.data)))[0].data.decode('utf-8').strip()
        logging.info(f"QR Code decodificado. ID: '{identificador_qr}'")

        now_local = datetime.now(LOCAL_TIMEZONE)
        data_str = now_local.strftime('%d/%m/%Y')
        hora_str = now_local.strftime('%H:%M:%S')

        if evento_ativo is None:
            evento_ativo = { 'id': identificador_qr, 'dt_entrada': now_local, 'data_str': data_str, 'hora_str': hora_str }
            logging.info(f"ENTRADA registrada para ID '{identificador_qr}'")
            return jsonify({ "status": "entrada_registrada", "identificador": identificador_qr }), 200
        else:
            if identificador_qr == evento_ativo['id']:
                duracao = now_local - evento_ativo['dt_entrada']
                total_seconds = int(duracao.total_seconds())
                h, rem = divmod(total_seconds, 3600)
                m, s = divmod(rem, 60)
                duracao_str = f"{h:02d}:{m:02d}:{s:02d}"

                params = {
                    'identificador': evento_ativo['id'],
                    'dataEntrada': evento_ativo['data_str'],
                    'horaEntrada': evento_ativo['hora_str'],
                    'dataSaida': data_str,
                    'horaSaida': hora_str,
                    'tempoDecorrido': duracao_str
                }
                
                logging.info(f"SAÍDA registrada para ID '{evento_ativo['id']}'. Enviando para planilha: {params}")
                enviar_para_google_sheets(params)
                
                evento_ativo = None
                return jsonify({ "status": "saida_registrada", "dados_enviados": params }), 200
            else:
                msg_erro = f"Conflito: Evento '{evento_ativo['id']}' já está ativo."
                logging.warning(msg_erro)
                return jsonify({ "status": "erro_conflito", "mensagem": msg_erro }), 409
    except Exception as e:
        logging.error(f"Erro no processamento: {e}", exc_info=True)
        return jsonify({"status": "erro_interno", "mensagem": str(e)}), 500

def enviar_para_google_sheets(params):
    if not GOOGLE_SCRIPT_URL or "SUA_URL" in GOOGLE_SCRIPT_URL:
        logging.error("URL do Google Apps Script não configurada!")
        return
    try:
        response = requests.get(GOOGLE_SCRIPT_URL, params=params, timeout=15)
        response.raise_for_status()
        logging.info(f"Resposta do Google Script: {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Falha ao enviar dados para Google Sheets: {e}")

if __name__ == '__main__':
    logging.info("Iniciando Servidor Flask para Registro de Eventos IoT.")
    app.run(host='0.0.0.0', port=5000)