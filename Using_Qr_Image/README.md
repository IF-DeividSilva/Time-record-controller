
# Controle de Atividades via QR Code + Google Sheets

Sistema simples e eficiente de controle de entrada e saída de atividades utilizando QR Codes e integração com Google Sheets.

## Visão Geral

Este projeto permite:
- Captura de QR Code via imagem
- Registro automático de entrada e saída
- Cálculo de tempo total
- Envio dos dados para uma planilha do Google em tempo real

Ideal para controle de tempo de uso de laboratório, eventos, coworkings, entre outros.

---

## Estrutura do Projeto

```
.
├── Server_Decoder.py       # Servidor Flask que processa imagens com QR Code
├── Code_Using_Image.ino    # (Opcional) Código Arduino para capturar e enviar imagem
├── exemplo_qr.jpg          # Exemplo de imagem com QR Code
├── AppsScript.gs           # Código Google Apps Script vinculado à planilha
└── README.md               # Documentação do projeto
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
- **(Opcional)** Arduino com câmera

---

## 🚀 Como Usar

### 1. Configurar a Planilha

Crie uma planilha no Google Drive com uma aba chamada `Registros`. O script adicionará automaticamente o cabeçalho:

```
["Data (Entrada)", "Hora (Entrada)", "Atividade", "Data (Saída)", "Hora (Saída)", "Tempo Total"]
```

### 2. Código do Google Apps Script

Acesse `Extensões > Apps Script` na planilha e cole o conteúdo abaixo:

```javascript
function doGet(e) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("Registros");
    if (!sheet) {
      sheet = ss.getSheets()[0];
      if (sheet.getLastRow() === 0) {
        sheet.appendRow(["Data (Entrada)", "Hora (Entrada)", "Atividade", "Data (Saída)", "Hora (Saída)", "Tempo Total"]);
      }
    } else {
      if (sheet.getLastRow() === 0) {
        sheet.appendRow(["Data (Entrada)", "Hora (Entrada)", "Atividade", "Data (Saída)", "Hora (Saída)", "Tempo Total"]);
      }
    }

    var dataEntrada = e.parameter.dataEntrada || "";
    var horaEntrada = e.parameter.horaEntrada || "";
    var atividade   = e.parameter.atividade   || "";
    var dataSaida   = e.parameter.dataSaida   || "";
    var horaSaida   = e.parameter.horaSaida   || "";
    var tempoTotal  = e.parameter.tempoTotal  || "";

    sheet.appendRow([dataEntrada, horaEntrada, atividade, dataSaida, horaSaida, tempoTotal]);

    return ContentService.createTextOutput("SUCESSO: Dados para atividade '" + atividade + "' adicionados à planilha.").setMimeType(ContentService.MimeType.TEXT);

  } catch (error) {
    return ContentService.createTextOutput("ERRO no Apps Script: " + error.toString()).setMimeType(ContentService.MimeType.TEXT);
  }
}
```

>  Publique como "Aplicativo da Web" e copie a URL para configurar no script Python.

---

### 3. Executar o Servidor Python

Instale as dependências:

```bash
pip install flask requests pyzbar pillow pytz
```

Execute o servidor:

```bash
python Server_Decoder.py
```

---

### 4. Enviar QR Code para o servidor

Você pode enviar uma imagem com QR Code para o endpoint `/upload_qr_bytes` via:

```bash
curl -X POST --data-binary "@exemplo_qr.jpg" http://localhost:5000/upload_qr_bytes
```

---

## Lógica do Funcionamento

1. **Primeira leitura do QR Code** → Registra *entrada*
2. **Segunda leitura do mesmo QR Code** → Registra *saída* e envia dados para o Google Sheets
3. Se tentar registrar outra entrada antes de registrar a saída → erro de atividade em andamento.

---

## Exemplo de Uso com Arduino (Opcional)

No arquivo `Code_Using_Image.ino` você encontrará um exemplo básico de como capturar imagem com ESP32-CAM e enviá-la para o servidor.

---

## Timezone

Certifique-se de ajustar o fuso horário no `Server_Decoder.py`:

```python
LOCAL_TIMEZONE = pytz.timezone('America/Sao_Paulo')
```

---

## Resultado Esperado na Planilha

| Data (Entrada) | Hora (Entrada) | Atividade     | Data (Saída) | Hora (Saída) | Tempo Total |
|----------------|----------------|----------------|--------------|--------------|--------------|
| 09/06/2025     | 14:02:31       | Aula de Python | 09/06/2025   | 15:10:05     | 01:07:34     |

---

##  Testes

- ✅ QR code legível
- ✅ Registro de entrada
- ✅ Registro de saída
- ✅ Conflito de atividades detectado
- ✅ Comunicação com Google Apps Script

---

## Autor

Este projeto foi desenvolvido para fins educacionais e pode ser adaptado para ambientes reais de controle de tempo e presença.

---

##  Licença

MIT License © 2025
