function exportTestToHTML(testData, mode) {
    // mode: 'published' for student version; 'key' for answer key.
    // Build a complete HTML file with inline styles for Word
    let html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="generator" content="QuizTest Management System">
  <title>${testData.name} - ${mode === 'key' ? 'Test Key' : 'Test'}</title>
  <style type="text/css">
    body { font-family: "Calibri", sans-serif; margin: 20px; }
    h1, h2, h3 { text-align: center; }
    .header { margin-bottom: 30px; }
    .question { margin-bottom: 30px; }
    .question-number { font-weight: bold; }
    .answer-choice { margin-left: 20px; }
    .student-response { border-bottom: 1px solid #000; margin-top: 10px; height: 2em; }
    .answer { color: red; font-weight: bold; }
    .grading-instructions { color: blue; font-style: italic; }
    .page-break { page-break-after: always; }
  </style>
</head>
<body>
  <div class="header">
    <h1>${testData.name} - ${mode === 'key' ? 'Test Key' : 'Test'}</h1>
    <h2>Template: ${testData.templateName}</h2>
    <p>Date: ${new Date().toLocaleDateString()}</p>
    <p>Student Name: ___________________________</p>
    <hr>
  </div>
`;
    let questionCounter = 1;
    testData.parts.forEach(part => {
        html += `<section><h2>Part ${part.partNumber}</h2>`;
        part.sections.forEach(section => {
            html += `<h3>Section ${section.sectionNumber} (${section.questionType.toUpperCase()} Questions)</h3>`;
            section.questions.forEach(question => {
                html += `<div class="question">`;
                html += `<p class="question-number">Question ${questionCounter} (${question.score} pts)</p>`;
                html += `<p>${question.text}</p>`;
                // For multiple-choice questions, render an ordered list of options.
                if (question.qtype && question.qtype.toLowerCase() === 'mc' && question.options && question.options.length > 0) {
                    html += `<ol type="A">`;
                    question.options.forEach(option => {
                        if (mode === 'key' && question.answer === option) {
                            html += `<li class="answer">${option}</li>`;
                        } else {
                            html += `<li class="answer-choice">${option}</li>`;
                        }
                    });
                    html += `</ol>`;
                } else {
                    // For other types, simply include a blank response area for the student version.
                    html += `<div class="student-response"></div>`;
                }
                // In key mode, add grading instructions if provided.
                if (mode === 'key' && question.directions) {
                    html += `<p class="grading-instructions">Grading Instructions: ${question.directions}</p>`;
                }
                html += `</div>`;
                questionCounter++;
            });
        });
        html += `</section><div class="page-break"></div>`;
    });
    html += `</body></html>`;
    return html;
}

function downloadTestHTML(testData, mode) {
    // mode: 'published' for the student test; 'key' for the answer key version.
    const htmlContent = exportTestToHTML(testData, mode);
    const blob = new Blob([htmlContent], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${testData.name}_${mode}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}
