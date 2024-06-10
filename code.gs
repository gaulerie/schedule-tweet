# This is the code to put on Google Apps Script, then deploy and put the Web App link on main.py

function doGet() {
  try {
    var sheetThreads = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Threads");
    var sheetAnecdotes = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Anecdotes");

    if (!sheetThreads) {
      throw new Error("Threads sheet not found");
    }

    if (!sheetAnecdotes) {
      throw new Error("Anecdotes sheet not found");
    }

    var dataThreads = sheetThreads.getDataRange().getValues();
    var dataAnecdotes = sheetAnecdotes.getDataRange().getValues();

    var jsonThreads = {};
    var jsonAnecdotes = {};

    // Process threads
    for (var i = 1; i < dataThreads.length; i++) {
      var row = dataThreads[i];
      try {
        var date = new Date(row[0]);
        Logger.log('Thread date processed: ' + date.toISOString());
        Logger.log('Thread tweeté column value: ' + row[21]); // Adjusted column index to 21 for zero-based index

        // Check for the correct column index and the "tweeté" status
        if (row[21] !== undefined && row[21].toString().toLowerCase() !== 'true') {
          var thread = {};
          for (var j = 1; j <= 20; j += 2) {
            if (row[j]) {
              var tweetKey = "Tweet" + Math.ceil(j / 2);
              var imageKey = "Image" + Math.ceil(j / 2);
              thread[tweetKey] = row[j];
              thread[imageKey] = row[j + 1] ? row[j + 1].split(",") : [];
            }
          }
          jsonThreads[date.toISOString()] = thread;
        }
      } catch (e) {
        Logger.log(e.message);
      }
    }

    // Log threads data
    Logger.log("Threads data: " + JSON.stringify(jsonThreads));

    // Process anecdotes
    for (var j = 1; j < dataAnecdotes.length; j++) {
      var rowA = dataAnecdotes[j];
      try {
        var dateA = new Date(rowA[0]);
        Logger.log('Anecdote date processed: ' + dateA.toISOString());
        Logger.log('Anecdote tweeté column value: ' + rowA[8]);
        if (rowA[8] !== undefined && rowA[8].toString().toLowerCase() !== 'true') {  // Vérifie si la colonne "tweeté" n'est pas true (index 8)
          var anecdote = {
            "text": rowA[1],
            "imageUrls": rowA[2] ? rowA[2].split(",") : [],
            "choices": [
              rowA[3],
              rowA[4],
              rowA[5],
              rowA[6]
            ],
            "duration": rowA[7]
          };
          jsonAnecdotes[dateA.toISOString()] = anecdote;
        }
      } catch (e) {
        Logger.log(e.message);
      }
    }

    // Log anecdotes data
    Logger.log("Anecdotes data: " + JSON.stringify(jsonAnecdotes));

    var jsonResponse = {
      "threads": jsonThreads,
      "anecdotes": jsonAnecdotes
    };

    var jsonString = JSON.stringify(jsonResponse);
    Logger.log("JSON response: " + jsonString);

    return ContentService.createTextOutput(jsonString).setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    Logger.log("Error: " + error.message);
    return ContentService.createTextOutput("Error: " + error.message).setMimeType(ContentService.MimeType.TEXT);
  }
}

function markAsTweeted(sheet, rowIndex) {
  sheet.getRange(rowIndex + 1, sheet.getLastColumn()).setValue(true); // Assumes 'tweeté' is the last column
}

function doPost(e) {
  try {
    var params = JSON.parse(e.postData.contents);
    var sheetThreads = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Threads");
    var sheetAnecdotes = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Anecdotes");

    if (!sheetThreads) {
      throw new Error("Threads sheet not found");
    }

    if (!sheetAnecdotes) {
      throw new Error("Anecdotes sheet not found");
    }

    var threadUpdates = params.threads;
    var anecdoteUpdates = params.anecdotes;

    // Update threads
    for (var i = 0; i < threadUpdates.length; i++) {
      var thread = threadUpdates[i];
      var rowIndex = thread.rowIndex;
      markAsTweeted(sheetThreads, rowIndex);
    }

    // Update anecdotes
    for (var j = 0; j < anecdoteUpdates.length; j++) {
      var anecdote = anecdoteUpdates[j];
      var rowIndex = anecdote.rowIndex;
      markAsTweeted(sheetAnecdotes, rowIndex);
    }

    return ContentService.createTextOutput("Success").setMimeType(ContentService.MimeType.TEXT);

  } catch (error) {
    Logger.log("Error: " + error.message);
    return ContentService.createTextOutput("Error: " + error.message).setMimeType(ContentService.MimeType.TEXT);
  }
}
