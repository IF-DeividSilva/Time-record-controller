from flask import Flask, request, jsonify
import requests
import logging
from pyzbar.pyzbar import decode as decode_pyzbar
from PIL import Image
import io
from datetime import datetime, timezone
import pytz # Para lidar com fuso horário corretamente

# Configura o logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')

app = Flask(__name__)

# --- Configurações IMPORTANTES ---
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyoU1CqpEOz8bE05-ex9G7SdHDiDVxEpRBjE2EHrPQOMemYMR78AUsqTTEfmjB1dmKo/exec" 
API_KEY_PARA_GOOGLE_SCRIPT = ""  # Defina como "" ou None se não estiver usando chave no Apps Script

# Variável global para armazenar o estado da entrada ativa
# Estrutura: {'qr_data': 'conteudo_do_qr', 'entry_datetime_obj': objeto_datetime_da_entrada}
active_entry_data = None

# Define o fuso horário de Londrina (ou o seu fuso local)
# Para encontrar seu fuso: import pytz; print(pytz.all_timezones) e procure o mais adequado
# Exemplo: 'America/Sao_Paulo' para o horário de Brasília que geralmente cobre Londrina.
LOCAL_TIMEZONE = pytz.timezone('America/Sao_Paulo') 

@app.route('/upload_qr_bytes', methods=['POST'])
def handle_qr_scan():
    global active_entry_data
    logging.debug(f"Recebida requisição. Estado atual de active_entry_data: {active_entry_data}")

    if not request.data:
        logging.warning("Nenhum dado (bytes da imagem) recebido.")
        return jsonify({"status": "erro", "mensagem": "Nenhum dado (bytes da imagem) recebido."}), 400
    
    image_bytes = request.data
    logging.info(f"Recebido {len(image_bytes)} bytes de dados da imagem.")

    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
        decoded_objects = decode_pyzbar(pil_image)

        if not decoded_objects:
            logging.warning("Não foi possível decodificar nenhum QR Code da imagem (bytes) recebida.")
            return jsonify({"status": "erro_decodificacao", "mensagem": "Não foi possível decodificar o QR Code dos bytes da imagem."}), 400
        
        qr_data_decodificada = decoded_objects[0].data.decode('utf-8').strip()
        logging.info(f"QR Code decodificado: '{qr_data_decodificada}'")

        # Obtém data e hora atuais no fuso horário local
        now_local = datetime.now(LOCAL_TIMEZONE)
        data_atual_str = now_local.strftime('%d/%m/%Y')
        hora_atual_str = now_local.strftime('%H:%M:%S')

        if active_entry_data is None:
            # Nenhuma entrada ativa, então esta é uma NOVA ENTRADA
            active_entry_data = {
                'qr_data': qr_data_decodificada,
                'entry_datetime_obj': now_local, # Armazena o objeto datetime completo
                'entry_data_str': data_atual_str,
                'entry_hora_str': hora_atual_str
            }
            logging.info(f"ENTRADA registrada para Atividade: '{qr_data_decodificada}' em {data_atual_str} {hora_atual_str}")
            return jsonify({
                "status": "entrada_registrada", 
                "atividade": qr_data_decodificada,
                "data_entrada": data_atual_str,
                "hora_entrada": hora_atual_str
            }), 200
        else:
            # Já existe uma entrada ativa
            if qr_data_decodificada == active_entry_data['qr_data']:
                # QR Code é o MESMO da entrada ativa: Esta é uma SAÍDA
                
                entry_dt = active_entry_data['entry_datetime_obj']
                exit_dt = now_local

                time_difference = exit_dt - entry_dt
                total_seconds = int(time_difference.total_seconds())

                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                tempo_total_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                # Dados para enviar à planilha
                dados_planilha = {
                    'dataEntrada': active_entry_data['entry_data_str'],
                    'horaEntrada': active_entry_data['entry_hora_str'],
                    'atividade': active_entry_data['qr_data'],
                    'dataSaida': data_atual_str,
                    'horaSaida': hora_atual_str,
                    'tempoTotal': tempo_total_str
                }
                
                logging.info(f"SAÍDA registrada para Atividade: '{active_entry_data['qr_data']}'. Dados para planilha: {dados_planilha}")

                try:
                    if not GOOGLE_SCRIPT_URL or GOOGLE_SCRIPT_URL == "SUA_URL_COMPLETA_DO_GOOGLE_APPS_SCRIPT_AQUI":
                        logging.error("ERRO DE CONFIGURAÇÃO: GOOGLE_SCRIPT_URL não foi definida.")
                        # Limpa a entrada mesmo se o Google Script falhar para permitir nova entrada
                        active_entry_data = None 
                        return jsonify({"status": "erro_configuracao_servidor_google", "mensagem": "URL do Google Script não configurada no servidor Python."}), 500

                    response_google = requests.get(GOOGLE_SCRIPT_URL, params=dados_planilha, timeout=20)
                    response_google.raise_for_status()
                    logging.info(f"Resposta do Google Apps Script: Status {response_google.status_code} - Texto: {response_google.text}")
                    
                    # Limpa a entrada ativa após o registro bem-sucedido da saída
                    mensagem_sucesso = f"Saída registrada para Atividade '{active_entry_data['qr_data']}'. Tempo Total: {tempo_total_str}. Dados enviados para planilha."
                    active_entry_data = None 
                    return jsonify({
                        "status": "saida_registrada",
                        "mensagem": mensagem_sucesso,
                        "dados_enviados": dados_planilha
                    }), 200

                except requests.exceptions.RequestException as e_req:
                    logging.error(f"Erro de requisição ao contatar Google Apps Script: {e_req}", exc_info=True)
                    # Considerar se deve limpar active_entry_data aqui ou permitir nova tentativa de saída
                    # Por segurança, não vamos limpar para que os dados de entrada não sejam perdidos facilmente.
                    return jsonify({"status": "erro_google_script", "mensagem": f"Erro ao contatar Google Script: {str(e_req)}"}), 503
                except Exception as e_google:
                    logging.error(f"Erro inesperado ao enviar para Google Script: {e_google}", exc_info=True)
                    return jsonify({"status": "erro_interno_google", "mensagem": f"Erro interno ao enviar para Google Script: {str(e_google)}"}), 500
            
            else:
                # QR Code é DIFERENTE da entrada ativa: ERRO
                logging.warning(f"Erro: Tentativa de iniciar nova atividade '{qr_data_decodificada}' enquanto a atividade '{active_entry_data['qr_data']}' está em andamento.")
                return jsonify({
                    "status": "erro_atividade_em_andamento",
                    "mensagem": f"Erro: Atividade '{active_entry_data['qr_data']}' (Entrada: {active_entry_data['entry_data_str']} {active_entry_data['entry_hora_str']}) precisa ser finalizada antes de iniciar a atividade '{qr_data_decodificada}'."
                }), 409 # Código 409 Conflict é apropriado aqui

    except Exception as e:
        logging.error(f"Erro geral ao processar imagem ou na lógica do endpoint: {e}", exc_info=True)
        return jsonify({"status": "erro_processamento_geral", "mensagem": f"Erro interno no servidor Python: {str(e)}"}), 500

if __name__ == '__main__':
    logging.info("Iniciando servidor Flask para controle de entrada/saída.")
    logging.info("Endpoint: /upload_qr_bytes (POST)")
    logging.info(f"Usando fuso horário: {LOCAL_TIMEZONE}")
    app.run(host='0.0.0.0', port=5000, debug=True)