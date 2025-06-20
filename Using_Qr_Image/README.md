# Plataforma de Registro de Eventos via QR Code + Google Sheets

Sistema base, simples e eficiente, para controle de entrada e saída de eventos ou atividades, utilizando QR Codes e integração em tempo real com Google Sheets.

## Visão Geral

Este projeto é uma plataforma flexível que permite:
- Processar um QR Code a partir de uma imagem para obter um identificador único.
- Registrar automaticamente a **entrada** (início) e **saída** (fim) de um evento.
- Calcular o tempo total de duração do evento.
- Enviar todos os dados para uma planilha do Google em tempo real para fácil visualização e análise.

É ideal para ser adaptado em cenários como controle de tempo de uso de máquinas, registro de horas de estudo (Pomodoro), controle de empréstimo de ferramentas, entre outros.

---

## Estrutura do Projeto

```
.
├── Server_Decoder.py          # Servidor Flask que processa os eventos
├── Code_Using_Image.ino       #  Código Arduino para enviar o gatilho do evento
├── exemplo_qr.png             # Exemplo de imagem com QR Code (ID: "ID-MAQUINA-01")
├── Code.gs                    # Código Google Apps Script vinculado à planilha
└── README.md                  # Documentação do projeto
```

---

## Tecnologias Utilizadas

- **Python 3**
  - Flask
  - requests
  - pyzbar
  - Pillow
  - pytz
- **Google Apps Script**
- **Google Sheets**
-  Arduino/ESP8266

---

## Como Usar

### 1. Configurar a Planilha

Crie uma planilha no Google Drive com uma aba chamada `Registros`. O script adicionará automaticamente o cabeçalho na primeira vez que for executado:

`["Identificador", "Data (Entrada)", "Hora (Entrada)", "Data (Saída)", "Hora (Saída)", "Tempo Decorrido"]`

### 2. Código do Google Apps Script

Acesse `Extensões > Apps Script` na sua planilha e cole o conteúdo abaixo:

```javascript
function doGet(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Registros");
    
    // Cria o cabeçalho se a planilha estiver vazia
    if (sheet.getLastRow() === 0) {
      sheet.appendRow([
        "Identificador", 
        "Data (Entrada)", 
        "Hora (Entrada)", 
        "Data (Saída)", 
        "Hora (Saída)", 
        "Tempo Decorrido"
      ]);
    }

    // Pega os parâmetros da URL
    var id = e.parameter.identificador   || "";
    var dataEntrada = e.parameter.dataEntrada    || "";
    var horaEntrada = e.parameter.horaEntrada    || "";
    var dataSaida   = e.parameter.dataSaida      || "";
    var horaSaida   = e.parameter.horaSaida      || "";
    var tempoTotal  = e.parameter.tempoDecorrido || "";

    // Adiciona a linha na planilha
    sheet.appendRow([id, dataEntrada, horaEntrada, dataSaida, horaSaida, tempoTotal]);

    return ContentService
      .createTextOutput("SUCESSO: Dados para o ID '" + id + "' adicionados.")
      .setMimeType(ContentService.MimeType.TEXT);

  } catch (error) {
    return ContentService
      .createTextOutput("ERRO: " + error.toString())
      .setMimeType(ContentService.MimeType.TEXT);
  }
}
```

> **Importante:** Clique em **Implantar > Nova implantação**. Configure como **App da Web**, em "Quem pode acessar" selecione **Qualquer pessoa** e clique em "Implantar". Copie a **URL do app da Web** gerada e cole na variável `GOOGLE_SCRIPT_URL` do arquivo `Server_Decoder.py`.

### 3. Executar o Servidor Python

Instale as dependências necessárias:

```bash
pip install flask requests pyzbar pillow pytz
```

Execute o servidor (lembre-se de preencher a URL do Google Script em `Server_Decoder.py`):

```bash
python Server_Decoder.py
```

### 4. Enviar QR Code para o Servidor

Você pode simular o envio de um evento usando a imagem de exemplo (`exemplo_qr.png`) com o seguinte comando:

```bash
# Envie uma primeira vez para registrar a ENTRADA
curl -X POST --data-binary "@exemplo_qr.png" http://localhost:5000/registrar-evento

# Envie uma segunda vez para registrar a SAÍDA
curl -X POST --data-binary "@exemplo_qr.png" http://localhost:5000/registrar-evento
```

---

## Lógica do Funcionamento

1.  **Primeira leitura do QR Code** → O servidor registra uma *entrada* para o ID contido no QR Code e armazena o timestamp.
2.  **Segunda leitura do mesmo QR Code** → O servidor identifica que já há uma entrada para aquele ID, registra a *saída*, calcula a duração, envia todos os dados para o Google Sheets e limpa o estado.
3.  **Leitura de um QR Code diferente** → Se um evento já estiver ativo, o servidor retornará um erro de conflito, garantindo que apenas um evento seja cronometrado por vez.

---

## Exemplo de Uso com ESP8266 (Opcional)

No arquivo `Code_Using_Image.ino.ino` você encontrará um código base para um ESP8266. Ele não captura uma imagem, mas envia uma imagem de QR Code **pré-gravada em sua memória**, atuando como um "botão de evento" físico.

---

## Timezone

O servidor utiliza um fuso horário para registrar a data e hora corretamente. Certifique-se de que ele está ajustado para sua localidade no arquivo `Server_Decoder.py`:

```python
LOCAL_TIMEZONE = pytz.timezone('America/Sao_Paulo')
```

---

## Resultado Esperado na Planilha

| Identificador  | Data (Entrada) | Hora (Entrada) | Data (Saída) | Hora (Saída) | Tempo Decorrido |
| :------------- | :------------- | :------------- | :----------- | :----------- | :-------------- |
| ID-MAQUINA-01  | 20/06/2025     | 17:15:30       | 20/06/2025   | 18:05:45     | 00:50:15        |
| Estudo-Python  | 20/06/2025     | 19:00:05       | 20/06/2025   | 19:55:10     | 00:55:05        |

---

## Testes

  - ✅ Decodificação de QR Code a partir de imagem.
  - ✅ Registro correto de **entrada**.
  - ✅ Registro correto de **saída** com cálculo de duração.
  - ✅ Detecção de **conflito** de eventos.
  - ✅ Comunicação e registro de dados no **Google Sheets**.

---

## Autor
- Nome: Deivid da Silva Galvão
- E-mail: deivid.2002@alunos.utfpr.edu.br

Este projeto foi desenvolvido como um boilerplate flexível para demonstrar a integração de tecnologias IoT, backend e serviços em nuvem. Ele pode ser livremente utilizado e adaptado.

---

## Licença

MIT License © 2025
