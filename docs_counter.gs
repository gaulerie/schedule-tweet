function updateCharacterCounters() {
  var doc = DocumentApp.getActiveDocument();
  var body = doc.getBody();
  var paragraphs = body.getParagraphs();
  var skipSection = false;

  for (var i = 0; i < paragraphs.length; i++) {
    var paragraph = paragraphs[i];
    var paragraphText = paragraph.getText();

    // Vérifier si un titre "Thread ..." est trouvé
    if (paragraph.getHeading() === DocumentApp.ParagraphHeading.HEADING1 && paragraphText.startsWith('Thread')) {
      Logger.log('Checking Thread: ' + paragraphText);
      skipSection = false; // Assumer que la section est ouverte par défaut
    } else if (paragraph.getHeading() === DocumentApp.ParagraphHeading.HEADING1 && !paragraphText.startsWith('Thread')) {
      Logger.log('Found new Heading 1: ' + paragraphText);
      skipSection = false; // Arrêter de sauter les sections
    }

    if (skipSection) {
      Logger.log('Skipping section: ' + paragraphText);
      continue;
    }

    if (paragraphText.startsWith('Tweet ')) {
      Logger.log('Processing Tweet: ' + paragraphText);
      try {
        var contentParagraph = paragraphs[i + 1];
        if (contentParagraph && !contentParagraph.getText().startsWith('Tweet ')) {
          var contentText = contentParagraph.getText();
          var charCount = contentText.length - 8; // Retirer 8 caractères pour "Texte : "

          // Mettre à jour le nombre de caractères sans changer le numéro de paragraphe
          var updatedText = paragraphText.replace(/: \d+\/280 caractères/, `: ${charCount}/280 caractères`);
          if (!updatedText.includes(paragraphText)) {
            paragraph.setText(updatedText);
          }

          var textElement = contentParagraph.editAsText();

          if (charCount > 0) { // Assurez-vous que le nombre de caractères est positif
            // Appliquer la couleur rouge si le nombre de caractères dépasse 280
            if (charCount > 280) {
              textElement.setForegroundColor(280, charCount - 1, '#FF0000');
            } else {
              textElement.setForegroundColor(0, charCount - 1, '#000000');
            }
          }
          Logger.log('Updated Tweet: ' + updatedText);
        }
      } catch (e) {
        // Ignorer les erreurs causées par les paragraphes masqués ou inaccessibles
        Logger.log("Erreur lors du traitement du paragraphe " + (i + 1) + ": " + e.message);
      }
    }
  }
}

function onOpen() {
  var ui = DocumentApp.getUi();
  ui.createMenu('Custom Tools')
    .addItem('Update Character Counters', 'updateCharacterCounters')
    .addItem('Start Auto Update', 'createTimeTrigger')
    .addToUi();
}
