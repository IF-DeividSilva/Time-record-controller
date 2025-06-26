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