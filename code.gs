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

    // Custom date parsing function for French date format
    function parseFrenchDate(dateStr) {
      dateStr = dateStr.toString().trim(); // Ensure dateStr is a string and trim whitespace
      Logger.log('Parsing date string: ' + dateStr);
      
      if (dateStr.match(/[a-zA-Z]{3} [a-zA-Z]{3} \d{2} \d{4} \d{2}:\d{2}:\d{2} GMT\+\d{4} \([a-zA-Z ]+\)/)) {
        // If the date is in standard JavaScript format, directly parse it
        return new Date(dateStr);
      } else {
        // Parse the French date format
        var months = {
          "janvier": 0, "février": 1, "mars": 2, "avril": 3, "mai": 4, "juin": 5,
          "juillet": 6, "août": 7, "septembre": 8, "octobre": 9, "novembre": 10, "décembre": 11
        };
        var parts = dateStr.split(/[ ,:]+/);
        Logger.log('Date parts: ' + JSON.stringify(parts));
        if (parts.length !== 6) {
          throw new Error('Invalid date format');
        }
        var day = parseInt(parts[0]);
        var month = months[parts[1].toLowerCase()];
        if (month === undefined) {
          throw new Error('Invalid month value');
        }
        var year = parseInt(parts[2]);
        var hour = parseInt(parts[3]);
        var minute = parseInt(parts[4]);
        var second = parseInt(parts[5]);
        return new Date(year, month, day, hour, minute, second);
      }
    }

    // Process threads
    for (var i = 1; i < dataThreads.length; i++) {
      var row = dataThreads[i];
      try {
        var date = parseFrenchDate(row[0]);
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
        Logger.log('Error processing thread row ' + i + ': ' + e.message);
      }
    }

    // Log threads data
    Logger.log("Threads data: " + JSON.stringify(jsonThreads));

    // Process anecdotes
    for (var j = 1; j < dataAnecdotes.length; j++) {
      var rowA = dataAnecdotes[j];
      try {
        var dateA = parseFrenchDate(rowA[0]);
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
        Logger.log('Error processing anecdote row ' + j + ': ' + e.message);
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

function getColumnIndex(sheet, columnName) {
  var data = sheet.getDataRange().getValues();
  var headerRow = data[0];
  for (var i = 0; i < headerRow.length; i++) {
    if (headerRow[i].toString().toLowerCase() === columnName.toLowerCase()) {
      Logger.log("Column '" + columnName + "' found at index " + i);
      return i;
    }
  }
  throw new Error("Column '" + columnName + "' not found");
}

function markAsTweeted(sheet, rowIndex, columnIndex) {
  Logger.log("Marking row " + (rowIndex + 1) + ", column " + (columnIndex + 1) + " as TRUE");
  sheet.getRange(rowIndex + 1, columnIndex + 1).setValue(true); // Set 'tweeté' to TRUE
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
    
    var tweetColumnIndexThreads = getColumnIndex(sheetThreads, 'tweeté');
    var tweetColumnIndexAnecdotes = getColumnIndex(sheetAnecdotes, 'tweeté');

    // Update threads
    for (var i = 0; i < threadUpdates.length; i++) {
      var thread = threadUpdates[i];
      var rowIndex = thread.rowIndex;
      Logger.log("Updating thread at row index " + rowIndex);
      markAsTweeted(sheetThreads, rowIndex, tweetColumnIndexThreads);
    }

    // Update anecdotes
    for (var j = 0; j < anecdoteUpdates.length; j++) {
      var anecdote = anecdoteUpdates[j];
      var rowIndex = anecdote.rowIndex;
      Logger.log("Updating anecdote at row index " + rowIndex);
      markAsTweeted(sheetAnecdotes, rowIndex, tweetColumnIndexAnecdotes);
    }

    return ContentService.createTextOutput("Success").setMimeType(ContentService.MimeType.TEXT);

  } catch (error) {
    Logger.log("Error: " + error.message);
    return ContentService.createTextOutput("Error: " + error.message).setMimeType(ContentService.MimeType.TEXT);
  }
}
