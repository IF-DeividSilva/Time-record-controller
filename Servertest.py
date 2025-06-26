from flask import Flask, request, jsonify
import requests # Biblioteca para fazer requisições HTTP (para o Google Apps Script)
import logging # Para registrar informações e erros

# Configura o logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# --- Configurações IMPORTANTES ---
# Substitua pela URL de implantação /exec do seu Google Apps Script
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyoU1CqpEOz8bE05-ex9G7SdHDiDVxEpRBjE2EHrPQOMemYMR78AUsqTTEfmjB1dmKo/exec"


API_KEY_PARA_GOOGLE_SCRIPT = ""  # Ou API_KEY_PARA_GOOGLE_SCRIPT = None

@app.route('/registrar_ponto', methods=['GET']) # Aceita requisições GET neste endpoint
def registrar_ponto():
    logging.debug("Função 'registrar_ponto' foi chamada.")
    
    # Pega o ID da estação do parâmetro 'id_estacao' da URL
    # Ex: http://localhost:5000/registrar_ponto?id_estacao=ESTACAO_XYZ
    id_estacao_recebido = request.args.get('id_estacao')

    if not id_estacao_recebido:
        logging.warning("Parâmetro 'id_estacao' não foi fornecido na requisição.")
        return jsonify({"status": "erro", "mensagem": "Parâmetro 'id_estacao' não fornecido na requisição."}), 400

    logging.info(f"Servidor Python recebeu ID da Estação: '{id_estacao_recebido}'")

    # Verificação crítica: A URL do Google Script FOI substituída?
    if not GOOGLE_SCRIPT_URL or GOOGLE_SCRIPT_URL == "SUA_URL_COMPLETA_DO_GOOGLE_APPS_SCRIPT_AQUI":
        logging.error("ERRO DE CONFIGURAÇÃO: A variável GOOGLE_SCRIPT_URL não foi alterada do valor placeholder.")
        return jsonify({"status": "erro_configuracao_servidor", "mensagem": "A URL do Google Apps Script não está configurada corretamente no servidor Python."}), 500

    try:
        # Monta os parâmetros para enviar ao Google Apps Script.
        # O Google Apps Script que ajustamos espera o ID da estação no parâmetro 'data1'.
        params_para_google = {
            'data1': id_estacao_recebido
        }

        # Adiciona a chave de API aos parâmetros SOMENTE SE ela tiver um valor útil
        # (não for None, não for string vazia, e não for o placeholder da chave)
        if API_KEY_PARA_GOOGLE_SCRIPT and API_KEY_PARA_GOOGLE_SCRIPT != "SUA_CHAVE_SECRETA_AQUI_SE_USAR": # Este placeholder é só para o caso de esquecerem de limpar
            params_para_google['apiKey'] = API_KEY_PARA_GOOGLE_SCRIPT
            logging.debug("Chave de API será incluída nos parâmetros para o Google.")
        else:
            logging.debug("Chave de API não será incluída (API_KEY_PARA_GOOGLE_SCRIPT está vazia, None ou é o placeholder).")
        
        logging.info(f"Enviando dados para Google Apps Script. URL: {GOOGLE_SCRIPT_URL}, Parâmetros: {params_para_google}")
        
        # Faz a requisição GET para o Google Apps Script
        response_google = requests.get(GOOGLE_SCRIPT_URL, params=params_para_google, timeout=15) # Timeout aumentado para 15 segundos
        
        logging.debug(f"Resposta do Google Apps Script - Status HTTP: {response_google.status_code}")
        
        # Levanta uma exceção para erros HTTP (4xx ou 5xx) para serem pegos pelos blocos 'except'
        response_google.raise_for_status() 
        
        logging.info(f"Resposta do Google Apps Script - Conteúdo: {response_google.text}")
        
        # Retorna uma resposta de sucesso para o cliente original (ESP8266)
        return jsonify({
            "status": "sucesso",
            "mensagem": "Dados processados pelo servidor Python e tentativa de envio para a planilha Google realizada.",
            "id_estacao_processado": id_estacao_recebido,
            "resposta_google_status": response_google.status_code,
            "resposta_google_texto": response_google.text # Inclui o que o Google Script respondeu
        }), 200

    except requests.exceptions.Timeout:
        logging.error("Timeout (tempo esgotado) ao tentar conectar com o Google Apps Script.")
        return jsonify({"status": "erro_timeout_google", "mensagem": "Timeout (tempo esgotado) ao conectar com o Google Apps Script."}), 504 # Gateway Timeout
    except requests.exceptions.MissingSchema as e_schema:
        logging.error(f"Erro de URL Inválida (MissingSchema) ao tentar contatar Google Apps Script: {e_schema}. Verifique a formatação da GOOGLE_SCRIPT_URL (precisa de http:// ou https://).")
        return jsonify({"status": "erro_url_invalida_google", "mensagem": f"A URL configurada para o Google Script é inválida: {str(e_schema)}"}), 500
    except requests.exceptions.RequestException as e_req: # Pega outras exceções da biblioteca 'requests'
        logging.error(f"Erro na requisição para o Google Apps Script (RequestException): {e_req}", exc_info=True) # exc_info=True mostra o traceback
        return jsonify({"status": "erro_requisicao_google", "mensagem": f"Erro na comunicação com o Google Apps Script: {str(e_req)}"}), 502 # Bad Gateway
    except Exception as e_geral: # Pega qualquer outra exceção inesperada
        logging.error(f"Ocorreu um erro inesperado no servidor Python durante o processamento da requisição: {e_geral}", exc_info=True)
        return jsonify({"status": "erro_interno_servidor", "mensagem": f"Erro interno inesperado no servidor Python: {str(e_geral)}"}), 500
    
    # Este ponto não deveria ser alcançado se a lógica try/except estiver correta.
    # Adicionado como uma salvaguarda final para o erro de "no response".
    logging.critical("FALHA CRÍTICA NA LÓGICA: A função 'registrar_ponto' terminou sem retornar uma resposta através dos caminhos esperados!")
    return jsonify({"status": "erro_logica_inesperada_servidor", "mensagem": "Erro crítico no servidor: fluxo de execução inesperado."}), 500

if __name__ == '__main__':
    # '0.0.0.0' faz o servidor Flask ser acessível por outros dispositivos na sua rede local
    # usando o IP do computador onde o script Python está rodando.
    logging.info("Iniciando servidor Flask. Escutando na porta 5000. Acessível na rede local.")
    app.run(host='0.0.0.0', port=5000, debug=True) # debug=True é bom para desenvolvimento