var GITHUB_REPO = 'gaulerie/schedule-tweet';  // Remplacez par votre dépôt GitHub
var GITHUB_TOKEN = '...';  // Remplacez par votre token d'accès personnel GitHub
var GITHUB_BRANCH = 'main';  // Remplacez par la branche de votre dépôt GitHub

function updateSheetFromDoc() {
  var docId = '1GoLqa45kjE_LbHKDWrPgDEvSiNpyS0PrpZ2NlVti_P0';  // Remplacez par l'ID de votre Google Docs
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Threads');  // Remplacez 'Threads' par le nom de votre feuille Google Sheets
  var doc = DocumentApp.openById(docId);
  var body = doc.getBody();
  var paragraphs = body.getParagraphs();

  var threadData = [];
  var currentThread = null;
  var currentThreadData = null;
  var tweetCount = 0;
  var processThread = false;

  for (var i = 0; i < paragraphs.length; i++) {
    var paragraph = paragraphs[i];
    var paragraphText = paragraph.getText();
    var heading = paragraph.getHeading();

    if (heading == DocumentApp.ParagraphHeading.HEADING1 && paragraphText.startsWith('Thread')) {
      if (currentThreadData && processThread) {
        threadData.push(currentThreadData);
      }
      currentThread = paragraphText;
      currentThreadData = {
        date: '',
        tweets: [],
        images: []
      };
      tweetCount = 0;
      processThread = false;  // Reset processThread for new thread
    } else if (currentThread && paragraphText.startsWith('Statut :')) {
      if (paragraphText.includes('Oui')) {
        processThread = true;
      }
    } else if (processThread && paragraphText.startsWith('Date :')) {
      var dateText = paragraphText.replace('Date : ', '').replace(',', '');
      Logger.log('Date text to parse: ' + dateText);
      currentThreadData.date = parseDate(dateText);
      Logger.log('Parsed date: ' + currentThreadData.date);
    } else if (processThread && paragraphText == 'Prêt à l’envoi ?' && i < paragraphs.length - 1 && paragraphs[i + 1].getText().toLowerCase() == 'true') {
      // Rien à faire ici pour l'instant
    } else if (processThread && paragraphText.startsWith('Tweet ')) {
      tweetCount++;
      if (tweetCount <= 10) {
        for (var j = i + 1; j < paragraphs.length; j++) {
          if (paragraphs[j].getText().startsWith('Tweet ') || paragraphs[j].getText().startsWith('Date :')) {
            break;
          }
          if (paragraphs[j].getText().startsWith('Texte : ')) {
            var tweetText = paragraphs[j].getText().replace('Texte : ', '');
            currentThreadData.tweets.push(tweetText);
            break;
          }
        }

        var images = [];
        for (var j = i + 2; j < paragraphs.length; j++) {
          if (paragraphs[j].getText().startsWith('Tweet ')) {
            break;
          }
          try {
            var elements = paragraphs[j].getNumChildren();
            for (var k = 0; k < elements; k++) {
              var element = paragraphs[j].getChild(k);
              if (element.getType() == DocumentApp.ElementType.INLINE_IMAGE) {
                var blob = element.asInlineImage().getBlob();
                var fileName = 'Tweet_' + tweetCount + '_Image_' + (k + 1) + '.jpg';
                var url = uploadImageToGithub(blob, fileName);
                if (url) {
                  images.push(url);
                } else {
                  Logger.log('Failed to upload image to GitHub.');
                }
              }
            }
          } catch (e) {
            Logger.log('Error processing paragraph: ' + e.toString());
          }
        }
        currentThreadData.images.push(images.join(','));
      }
    }
  }
  if (currentThreadData && processThread) {
    threadData.push(currentThreadData);
  }

  for (var row = 3; row < threadData.length + 3; row++) {  // Commencez à la ligne 3
    var thread = threadData[row - 3];
    var rowData = [formatDate(thread.date)];
    Logger.log('Formatted date: ' + rowData[0]);
    for (var t = 0; t < 10; t++) {
      rowData.push(thread.tweets[t] || '');
      rowData.push(thread.images[t] || '');
    }
    sheet.getRange(row, 1, 1, rowData.length).setValues([rowData]);
  }
}

function uploadImageToGithub(blob, fileName) {
  Logger.log('Uploading image: ' + fileName);
  var base64Data = Utilities.base64Encode(blob.getBytes());
  
  var sha = getFileShaFromGithub(fileName);
  var payload = {
    message: 'Upload image ' + fileName,
    content: base64Data,
    branch: GITHUB_BRANCH
  };

  if (sha) {
    payload.sha = sha;
  }

  var options = {
    method: 'put',
    contentType: 'application/json',
    headers: {
      'Authorization': 'token ' + GITHUB_TOKEN
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  var url = 'https://api.github.com/repos/' + GITHUB_REPO + '/contents/threads-images/' + fileName;
  var response = UrlFetchApp.fetch(url, options);
  Logger.log('GitHub API response code: ' + response.getResponseCode());
  Logger.log('GitHub API response: ' + response.getContentText());
  var result = JSON.parse(response.getContentText());

  if (result.content && result.content.download_url) {
    Logger.log('Image uploaded to GitHub: ' + result.content.download_url);
    return result.content.download_url;
  } else {
    Logger.log('GitHub API error: ' + response.getContentText());
    return null;
  }
}

function getFileShaFromGithub(fileName) {
  var url = 'https://api.github.com/repos/' + GITHUB_REPO + '/contents/threads-images/' + fileName;
  var options = {
    method: 'get',
    headers: {
      'Authorization': 'token ' + GITHUB_TOKEN
    },
    muteHttpExceptions: true
  };

  var response = UrlFetchApp.fetch(url, options);
  if (response.getResponseCode() == 200) {
    var result = JSON.parse(response.getContentText());
    return result.sha;
  } else {
    Logger.log('No existing file found: ' + response.getContentText());
    return null;
  }
}

function parseDate(dateString) {
  var parts = dateString.split(' ');
  var dateParts = parts[0].split('/');
  var timeParts = parts[1].split('h');
  var date = new Date(dateParts[2], dateParts[1] - 1, dateParts[0], timeParts[0], timeParts[1]);
  Logger.log('Parsed date object: ' + date);
  return date;
}

function formatDate(date) {
  if (!date) return '';
  var options = { year: 'numeric', month: 'long', day: 'numeric' };
  var formattedDate = date.toLocaleDateString('fr-FR', options);
  var time = Utilities.formatDate(date, Session.getScriptTimeZone(), 'HH:mm:ss');
  Logger.log('Formatted date before returning: ' + formattedDate + ',' + time);
  return formattedDate + ',' + time;
}
