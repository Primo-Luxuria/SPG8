/**
 * This function is called when the user clicks the edit button in the context menu.
 * It determines the type of item being edited and calls the appropriate edit function.
 * Precondition: context menu is open, edit button is clicked
 * Postcondition: edit modal is opened with the appropriate item data
*/
function editItem() {
    const contextMenu = document.getElementById('contextMenu');
    const itemType = contextMenu.dataset.itemType;
    const itemID = contextMenu.dataset.itemID;
    const courseID = contextMenu.dataset.courseID;
    const questionType = contextMenu.dataset.questionType;
    switch (itemType) {
        case 'question':
            editQuestion(courseID, questionType, itemID);
            break;
        case 'coverPage':
            editCoverPage(courseID, itemID);
            break;
        case 'template':
            editTemplate(courseID, itemID);
            break;
        case 'test':
            editTest(courseID, itemID);
            break;
        case 'attachment':
            editAttachment(courseID, itemID);
            break;
        default:
            console.error('Unknown item type:', itemType);
    }
}

/**
 * This function is called when the user clicks the edit button for a question in the context menu.
 * It will allow the editing of published questions, but only after a confirmation dialog.
 * Precondition: context menu is open, edit button is clicked
 * Postcondition: edit modal is opened with the appropriate question data
*/
function editQuestion(courseID, questionType, questionID) {
    console.log(masterQuestionList[courseID][questionType][questionID]);
    if(masterQuestionList[courseID][questionType][questionID].published === 1){
        if(!confirm("This question is published. Are you sure you want to edit it?")){
           return;
        }
    }
    const question = masterQuestionList[courseID][questionType][questionID];

    // Open the edit modal and populate it with the question data
    const modal = document.getElementById('editModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    modalTitle.innerText = 'Edit Question';

    let formContent = `
        <label>Question:</label><br/>
        <textarea id="editQuestionField" rows="5">${question.text}</textarea><br><br>
    `;

    if (questionType === 'tf') {
        formContent += `
            <label>Correct Answer:</label><br/>
            <select id="editAnswerField">
                <option value="true" ${question.answer.value === 'true' ? 'selected' : ''}>True</option>
                <option value="false" ${question.answer.value === 'false' ? 'selected' : ''}>False</option>
            </select><br><br>
        `;
    } else if (questionType === 'sa' || questionType === 'es') {
        formContent += `
            <label>Correct Answer:</label><br/>
            <textarea id="editAnswerField" rows="4">${question.answer.value}</textarea><br><br>
        `;
    } else if (questionType === 'mc') {
        formContent += `
            <label>Options:</label><br/>
            <input type="text" id="editOptionA" value="${question.options.A?.text || ''}" placeholder="Option A"><br>
            <input type="text" id="editOptionB" value="${question.options.B?.text || ''}" placeholder="Option B"><br>
            <input type="text" id="editOptionC" value="${question.options.C?.text || ''}" placeholder="Option C"><br>
            <input type="text" id="editOptionD" value="${question.options.D?.text || ''}" placeholder="Option D"><br><br>
            <label>Correct Answer:</label><br/>
            <select id="editAnswerField">
                <option value="A" ${question.answer.value === 'A' ? 'selected' : ''}>A</option>
                <option value="B" ${question.answer.value === 'B' ? 'selected' : ''}>B</option>
                <option value="C" ${question.answer.value === 'C' ? 'selected' : ''}>C</option>
                <option value="D" ${question.answer.value === 'D' ? 'selected' : ''}>D</option>
            </select><br><br>
        `;
    } else if (questionType === 'ma') {
        formContent += `
            <label>Number of Pairs:</label><br/>
            <input type="number" id="numPairs" min="1" step="1" value="${question.options.numPairs}" onchange="updateEditOptions('${questionType}')"><br>
            <label>Number of Distractions:</label><br/>
            <input type="number" id="numDistractions" min="0" step="1" value="${question.options.numDistractions}" onchange="updateEditOptions('${questionType}')"><br><br>
            <div id="editOptionsContainer"></div>
        `;
        setTimeout(() => updateEditOptions(questionType, question.options), 50);
    } else if (questionType === 'ms') {
        formContent += `
            <label>Number of Options:</label><br/>
            <input type="number" id="editNumOptions" value="${Object.keys(question.options).length}" min="1" max="20" onchange="updateEditOptions('${questionType}')"><br><br>
            <div id="editOptionsContainer"></div>
        `;
        setTimeout(() => updateEditOptions(questionType, question.options, question.answer), 50);
    } else if (questionType === 'fb') {
        formContent += `
            <label>Number of Blanks:</label><br/>
            <input type="number" id="editNumBlanks" value="${Object.keys(question.answer).length}" min="1" onchange="updateEditOptions('${questionType}')"><br><br>
            <div id="editOptionsContainer"></div>
        `;
        setTimeout(() => updateEditOptions(questionType, {}, question.answer), 50);
    }

    formContent += `
        <label>Point Value:</label><br/>
        <input type="number" id="editPointValueField" min="1" value="${question.score}"><br><br>
        <label>Chapter: </label><br/>  
        <input type="number" id="editChapterField" min="1" value="${question.chapter}"><br><br>
        <label>Section: </label><br/>
        <input type="number" id="editSectionField" min="1" value="${question.section}"><br><br>
        <label>Estimated Time:</label><br/>
        <input type="number" id="editTimeField" min="1" value="${question.eta}"><br><br>
        <label>Reference Text:</label><br/>
        <textarea id="editRefField" rows="4">${question.reference}</textarea><br><br>
        <label>Question Image:</label><br/>
        <select id="qGraphicField">
            <option value="" disabled selected>Select a graphic</option>
        </select><br><br>
        <label>Answer Image:</label><br/>
        <select id="ansGraphicField">
            <option value="" disabled selected>Select a graphic</option>
        </select><br><br>
        <label>Instructor Comment:</label><br/>
        <textarea id="editInstructorCommentField" rows="4">${question.comments}</textarea><br><br>
        <label>Grading Instructions:</label><br/>
        <textarea id="editInstructionField" rows="6">${question.directions}</textarea><br><br>
        <button class="save-btn" onclick="submitEditQuestion('${courseID}', '${questionType}', ${questionID})">Submit Edit</button>
    `;

    modalBody.innerHTML = formContent;
    modal.style.display = 'flex';
    setTimeout(() => {
        modal.style.opacity = '1';
    }, 10);

    // Populate the graphic selectors
    updateGraphicSelectors(courseID, question);
}



/**
 * This function is used to update the possible options for a question in the editor modal during question editing. 
 * It updates the possible options and answers for a question based on question type, similar to the options during question creation.
 * Precondition: valid question type, options, and answers  
 * Postcondition: options and answers are updated in the editor modal
*/
function updateEditOptions(type, options = {}, answers = {}) {
    const optionsContainer = document.getElementById('editOptionsContainer');
    optionsContainer.innerHTML = '';

    if (type === 'ma') {
        const numPairs = parseInt(document.getElementById('numPairs').value);
        const numDistractions = parseInt(document.getElementById('numDistractions').value);
        for (let i = 1; i <= numPairs*2; i+=2) {
            pairNum = (i-1)/2 + 1;
            optionsContainer.innerHTML += `
                <label>Pair ${pairNum}:</label><br/>
                <input type="text" id="option${i}" value="${options[`pair${pairNum}`]?.left || ''}">
                <input type="text" id="option${i+1}" value="${options[`pair${pairNum}`]?.right || ''}"><br><br>
            `;
        }
        for (let i = 1; i <= numDistractions; i++) {
            optionsContainer.innerHTML += `
                <label>Distraction ${i}:</label><br/>
                <input type="text" id="distraction${i}" value="${options[`distraction${i}`]?.text || ''}"><br><br>
            `;
        }
    } else if (type === 'ms') {
        const numOptions = parseInt(document.getElementById('editNumOptions').value);
        for (let i = 1; i <= numOptions; i++) {
            optionsContainer.innerHTML += `
                <label>Option ${i}:</label><br/>
                <input type="text" id="editOption${i}" value="${options[`option${i}`]?.text || ''}" placeholder="Option ${i}"><br>
                <label>Correct Answer:</label>
                <input type="checkbox" id="editCorrect${i}" ${answers[`option${i}`]?.value ? 'checked' : ''}><br><br>
            `;
        }
    } else if (type === 'fb') {
        const numBlanks = parseInt(document.getElementById('editNumBlanks').value);
        for (let i = 1; i <= numBlanks; i++) {
            const key = `blank${i}`;
            optionsContainer.innerHTML += `
            <label>Answer for Blank ${i}:</label><br/>
            <input type="text" id="editBlank${i}" value="${answers[key]?.value || ''}" placeholder="Answer for Blank ${i}"><br><br>
            `;
        }
    }
}


/**
 * This function is called when the user submits an edited question in the editor modal.
 * It updates the question in the master question list with the new data.
 * Precondition: valid courseID, question type, and question index
 * Postcondition: question is updated in the master question list or a clone is created
 * 
*/function submitEditQuestion(courseID, questionType, questionID) {
    const text = document.getElementById('editQuestionField').value.trim();
    const points = document.getElementById('editPointValueField').value.trim();
    const instructions = document.getElementById('editInstructionField').value.trim();
    const refText = document.getElementById('editRefField').value.trim();
    const time = document.getElementById('editTimeField').value.trim();
    const graphic = document.getElementById('qGraphicField').value;
    const ansGraphic = document.getElementById('ansGraphicField').value;
    const instcomm = document.getElementById('editInstructorCommentField').value.trim();
    const chapter = document.getElementById('editChapterField').value.trim();
    const section = document.getElementById('editSectionField').value.trim();

    if (!text || !questionType || !points || !instructions || !time || !chapter || !section) {
        alert("Some fields (Question, Question Type, Default Point Value, and Grading Instructions) are required. For chapter or section, put 0 if not applicable.");
        return;
    }

    let answer = {};
    let options = {};

    if (questionType === 'tf') {
        answer.value = document.getElementById("editAnswerField").value.trim();
    } else if (questionType === 'sa' || questionType === 'es') {
        answer.value = document.getElementById("editAnswerField").value.trim();
    } else if (questionType === 'mc') {
        options.A = { text: document.getElementById("editOptionA").value.trim(), order: 1 };
        options.B = { text: document.getElementById("editOptionB").value.trim(), order: 2 };
        options.C = { text: document.getElementById("editOptionC").value.trim(), order: 3 };
        options.D = { text: document.getElementById("editOptionD").value.trim(), order: 4 };
        answer.value = document.getElementById("editAnswerField").value.trim();
    } else if (questionType === 'ma') {
        const numPairs = parseInt(document.getElementById("numPairs").value);
        const numDistractions = parseInt(document.getElementById("numDistractions").value);
        options.numPairs = numPairs;
        options.numDistractions = numDistractions;

        for (let i = 1; i <= numPairs * 2; i += 2) {
            let pairNum = (i - 1) / 2 + 1;
            let pair = {
                "left": document.getElementById(`option${i}`).value.trim(),
                "right": document.getElementById(`option${i + 1}`).value.trim(),
                "pairNum": pairNum
            };
            options[`pair${pairNum}`] = pair;
        }

        for (let i = 1; i <= numDistractions; i++) {
            let distraction = {
                text: document.getElementById(`distraction${i}`).value.trim(),
                order: i
            };
            options[`distraction${i}`] = distraction;
        }

        for (let i = 1; i <= numPairs * 2; i += 2) {
            let pairNum = (i - 1) / 2 + 1;
            let pair = options[`pair${pairNum}`];
            answer[`pair-${pairNum}-left`] = pair.left;
            answer[`pair-${pairNum}-right`] = pair.right;
        }
    } else if (questionType === 'ms') {
        const numOptions = parseInt(document.getElementById("editNumOptions").value);
        for (let i = 1; i <= numOptions; i++) {
            let option = {
                text: document.getElementById(`editOption${i}`).value.trim(),
                order: i
            };
            options[`option${i}`] = option;
            if (document.getElementById(`editCorrect${i}`).checked) {
                answer[`option${i}`] = { value: option.text };
            }
        }
    } else if (questionType === 'fb') {
        const numBlanks = parseInt(document.getElementById("editNumBlanks").value);
        for (let i = 1; i <= numBlanks; i++) {
            answer[`answer${i}`] = {
                value: document.getElementById(`editBlank${i}`).value.trim()
            };
        }
    }

    const question = masterQuestionList[courseID][questionType][questionID];

    // Handle published logic
    if (question.published === 1) {
        if (confirm("This question is published. Would you like to clone it instead of editing? Click OK to clone.")) {
            const clone = {
                text: text,
                answer: answer,
                qtype: questionType,
                score: points,
                directions: instructions,
                reference: refText,
                eta: time,
                img: graphic,
                ansimg: ansGraphic,
                comments: instcomm,
                options: options,
                feedback: [],
                tests: [],
                chapter: chapter,
                section: section,
                published: 0
            };

            masterQuestionList[courseID][questionType].push(clone);
            updateQuestionTabs(questionType, courseID);
            closeModal();
            return;
        } else if (!confirm("Are you sure you want to edit this published question directly?")) {
            alert("Edit canceled.");
            return;
        }
    }

    // Update the original question
    question.text = text;
    question.answer = answer;
    question.qtype = questionType;
    question.score = points;
    question.directions = instructions;
    question.reference = refText;
    question.eta = time;
    question.img = graphic;
    question.ansimg = ansGraphic;
    question.comments = instcomm;
    question.options = options;
    question.chapter = chapter;
    question.section = section;

    updateQuestionTabs(questionType, courseID);
    saveData("question", question, courseID);
    closeModal();
}




/**
 * This function edits the cover page that was previously saved. 
 * Precondition: valid courseID, pageIndex
 * Postcondition: cover page is edited and republished in the master list
*/
function editCoverPage(courseID, pageID) {
    const coverPage = masterCoverPageList[courseID][pageID];

    // Open the edit modal and populate it with the cover page data
    const modal = document.getElementById('editModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    if(coverPage.published==1){
        alert("This page is published. You cannot edit it.");
        return;
    }
    modalTitle.innerText = 'Edit Cover Page';

    const formContent = `
        <label>Cover Page Name:</label><br/>
        <input type="text" id="editCoverPageName" value="${coverPage.name}"><br><br>
        <label>Test Number:</label><br/>
        <input type="number" id="editTestNumber" value="${coverPage.testNum}"><br><br>
        <label>Test Date:</label><br/>
        <input type="date" id="editTestDate" value="${coverPage.date}"><br><br>
        <label>Filename:</label><br/>
        <input type="text" id="editFilename" value="${coverPage.file}"><br><br>
        <label>Show Filename:</label><br/>
        <input type="checkbox" id="editShowFilename" ${coverPage.showFilename ? 'checked' : ''}><br><br>
        <label>Student Name Location:</label><br/>
        <select id="editNameBlankSelector">
            <option value="TR" ${coverPage.blank === 'TR' ? 'selected' : ''}>Top Right</option>
            <option value="TL" ${coverPage.blank === 'TL' ? 'selected' : ''}>Top Left</option>
            <option value="BT" ${coverPage.blank === 'BT' ? 'selected' : ''}>Below the Title</option>
        </select><br><br>
        <label>Grading Instructions:</label><br/>
        <textarea id="editInstructions" rows="6">${coverPage.instructions}</textarea><br><br>
        <button class="add-btn" onclick="submitEditCoverPage('${courseID}', ${pageID})">Submit Edit</button>
    `;

    modalBody.innerHTML = formContent;
    modal.style.display = 'flex';
    setTimeout(() => {
        modal.style.opacity = '1';
    }, 10);
}

function submitEditCoverPage(courseID, pageID) {
    const pageName = document.getElementById("editCoverPageName").value.trim();
    const testNumber = document.getElementById("editTestNumber").value.trim();
    const testDate = document.getElementById("editTestDate").value.trim();
    const filename = document.getElementById("editFilename").value.trim();
    const filenameTF = document.getElementById("editShowFilename").checked;
    const nameBlankSelector = document.getElementById("editNameBlankSelector").value.trim();
    const gradingInstructions = document.getElementById("editInstructions").value.trim();
  
    if (!pageName || !testNumber || !testDate || !filename || !nameBlankSelector || !gradingInstructions) {
      alert("Cover page name, Test number, test date, filename, name blank selection, and grading instructions are required fields!");
      return;
    }
  
    if (!masterCoverPageList[courseID]) {
      masterCoverPageList[courseID] = {};
    }
  
    const coverPage = {
      id: pageID,
      name: pageName,
      testNum: testNumber,
      date: testDate,
      file: filename,
      showFilename: filenameTF,
      blank: nameBlankSelector,
      instructions: gradingInstructions,
      published: masterCoverPageList[courseID][pageID].published  
    };
  
    // Save to database/storage using the existing saveData function
    saveData("coverPage", coverPage, courseID, null);
    
    closeModal();
    alert("Cover page updated successfully");
  }


/**
 * This function is called from the context menu to edit an existing template from the course UI
 * Precondition: valid courseID, not published
 * Postcondition: template is edited and saved in the master list
*/
function editTemplate(courseID, templateID) {
    const template = masterTemplateList[courseID][templateID];

    // Open the edit modal and populate it with the template data
    const modal = document.getElementById('editModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    alert(JSON.stringify(template));
    modalTitle.innerText = 'Edit Template';
    if(template.published === 1){
        alert("This template is published. You cannot edit it.");
        return;
    }

    
    let coverPageID = template.coverPageID;    

    const formContent = `
        <label>Template Name:</label><br/>
        <input type="text" id="nameField" value="${template.name}"><br><br>
        <div style="background:#e0e0e0;padding:20px;" id="templateEditor"> 
            <h1>Font Settings</h1>
            <label>Title Font and Font Size:</label><br/>
            <select id="titleFont">
                <option value="Times New Roman" ${template.titleFont === 'Times New Roman' ? 'selected' : ''}>Times New Roman</option>
                <option value="Arial" ${template.titleFont === 'Arial' ? 'selected' : ''}>Arial</option>
                <option value="Calibri" ${template.titleFont === 'Calibri' ? 'selected' : ''}>Calibri</option>
                <option value="Helvetica" ${template.titleFont === 'Helvetica' ? 'selected' : ''}>Helvetica</option>
                <option value="Georgia" ${template.titleFont === 'Georgia' ? 'selected' : ''}>Georgia</option>
                <option value="Cambria" ${template.titleFont === 'Cambria' ? 'selected' : ''}>Cambria</option>
                <option value="Garamond" ${template.titleFont === 'Garamond' ? 'selected' : ''}>Garamond</option>
            </select>
            <input type="number" id="titleFontSize" min="1" value="${template.titleFontSize}"><br/><br/>

            <label>Subtitle Font and Font Size:</label><br/>
            <select id="subtitleFont">
                <option value="Times New Roman" ${template.subtitleFont === 'Times New Roman' ? 'selected' : ''}>Times New Roman</option>
                <option value="Arial" ${template.subtitleFont === 'Arial' ? 'selected' : ''}>Arial</option>
                <option value="Calibri" ${template.subtitleFont === 'Calibri' ? 'selected' : ''}>Calibri</option>
                <option value="Helvetica" ${template.subtitleFont === 'Helvetica' ? 'selected' : ''}>Helvetica</option>
                <option value="Georgia" ${template.subtitleFont === 'Georgia' ? 'selected' : ''}>Georgia</option>
                <option value="Cambria" ${template.subtitleFont === 'Cambria' ? 'selected' : ''}>Cambria</option>
                <option value="Garamond" ${template.subtitleFont === 'Garamond' ? 'selected' : ''}>Garamond</option>
            </select>
            <input type="number" id="subtitleFontSize" min="1" value="${template.subtitleFontSize}"><br/><br/>

            <label>Body Font and Font Size:</label><br/>
            <select id="bodyFont">
                <option value="Times New Roman" ${template.bodyFont === 'Times New Roman' ? 'selected' : ''}>Times New Roman</option>
                <option value="Arial" ${template.bodyFont === 'Arial' ? 'selected' : ''}>Arial</option>
                <option value="Calibri" ${template.bodyFont === 'Calibri' ? 'selected' : ''}>Calibri</option>
                <option value="Helvetica" ${template.bodyFont === 'Helvetica' ? 'selected' : ''}>Helvetica</option>
                <option value="Georgia" ${template.bodyFont === 'Georgia' ? 'selected' : ''}>Georgia</option>
                <option value="Cambria" ${template.bodyFont === 'Cambria' ? 'selected' : ''}>Cambria</option>
                <option value="Garamond" ${template.bodyFont === 'Garamond' ? 'selected' : ''}>Garamond</option>
            </select>
            <input type="number" id="bodyFontSize" min="1" value="${template.bodyFontSize}"><br/><br/>

            <h1>Tags Section (Optional)</h1>
            <div class="form-container">
                <div class="form-group"><label>Test Name </label> <input type="text" id="tempTestName" value="${template.nameTag}"></div>
                <div class="form-group"><label>Date </label> <input type="text" id="tempDate" value="${template.dateTag}"></div>
                <div class="form-group"><label>Course Number </label> <input type="text" id="tempCourseNum" value="${template.courseTag}"></div>
            </div>

            <h1>Header and Footer Settings</h1>
            <label>Location of Student Score Blank (On the second page of the test)</label>
            <select id="studentScoreSelector">
                <option value="TR" ${template.studentScoreLocation === 'TR' ? 'selected' : ''}>Top Right</option>
                <option value="TL" ${template.studentScoreLocation === 'TL' ? 'selected' : ''}>Top Left</option>
            </select><br/><br/>
            <label>Page Numbers in Header</label><br/>
            <input type="checkbox" id="pageNumH" ${template.pageNumbersInHeader ? 'checked' : ''}><br/>
            <label>Page Numbers in Footer</label><br/>
            <input type="checkbox" id="pageNumF" ${template.pageNumbersInFooter ? 'checked' : ''}><br/><br/>
            <textarea id="headerField" rows="3" placeholder="Enter any desired header text ...">${template.headerText}</textarea>
            <textarea id="footerField" rows="3" placeholder="Enter any desired footer text...">${template.footerText}</textarea>

            <h1>Cover Page Selection</h1><br/>
            <select id="coverPageSelector">
                <option value="" disabled>Please Select a Cover Page</option>
            </select><br/><br/>

            <h1>Test Structure Settings</h1>
            <label>Number of Parts:</label>
            <input type="number" id="partCount" min="1" value="${template.partStructure.length}">
            <button onclick="updateParts()">Update</button>
            <div style="background:#d0d0d0;padding:20px" id="partsContainer"></div>

            <h1>Bonus Question Section Toggle</h1>
            <select id="bonusToggle" onchange="toggleBonusQuestionSelection('${courseID}')">
                <option value="True" ${template.bonusSection ? 'selected' : ''}>Bonus Section</option>
                <option value="False" ${!template.bonusSection ? 'selected' : ''}>No Bonus Section</option>
            </select><br/><br/>
            <button class="add-btn" id="selectBonusQuestionsBtn" style="display:${template.bonusSection ? 'block' : 'none'};" onclick="openBonusQuestionModal('${courseID}')">Select Bonus Questions</button>
            <div id="selectedBonusQuestionsContainer"><p>"No bonus questions selected"</p></div>
            <button class="save-btn" onclick="submitEditTemplate('${courseID}', ${templateID})">Submit Template</button>
        </div>
    `;

    modalBody.innerHTML = formContent;
    const selectedQuestionsDiv = document.createElement('div');
    selectedQuestionsDiv.className = "bonus-questions-container";
    // Populate the cover page selector
    updatePageSelection(courseID);
    pageSelector = document.getElementById('coverPageSelector');
    pageSelector.value = coverPageID;
    for(let i=0;i<template.bonusQuestions.length;i++){
        id = template.bonusQuestions[i];
        const types = ['tf', 'ma', 'mc', 'ms', 'es', 'sa', 'fb'];
        for (const t of types) {
        if (masterQuestionList[courseID][t] && masterQuestionList[courseID][t][id]) {
            question = masterQuestionList[courseID][t][id];
            foundType = t;
            break;
        }
        }

        if (!question) {
            console.warn(`Question ID ${id} not found in any type.`);
            continue;
        }

        console.log(`Processing question: ${question.text.substring(0, 20)}...`);
        const questionElement = document.createElement("div");
        questionElement.style.padding = "8px";
        questionElement.style.margin = "5px 0";
        questionElement.style.backgroundColor = "#f0f0f0";
        questionElement.style.borderRadius = "4px";

        questionElement.innerHTML = `
            <p>${question.text}</p>
            <p>Points: ${question.score}</p>
            `;
        selectedQuestionsDiv.appendChild(questionElement);
    }
    let container = document.getElementById("selectedBonusQuestionsContainer");
    if (container) {
        container.innerHTML = "";
        container.appendChild(selectedQuestionsDiv);
        console.log("Container updated successfully");
    }
    updateParts();
    template.partStructure.forEach((part, partIndex) => {
        const sectionCountInput = document.getElementById(`sectionCount-${partIndex + 1}`);
        sectionCountInput.value = part.sections.length;
        updateSections(partIndex + 1);
        part.sections.forEach((section, sectionIndex) => {
            const sectionSelects = document.querySelectorAll(`#sectionsContainer-${partIndex + 1} select.sectionTypeSelect`);
            const sectionSelect = sectionSelects[sectionIndex];
            if (sectionSelect) {
                sectionSelect.value = section.questionType;
            }
        });
        
    });



    modal.style.display = 'flex';
    setTimeout(() => {
        modal.style.opacity = '1';
    }, 10);
}

/**
 * This function is used to submit an edited template when the user is finished editing the template from the context menu
 * Precondition: valid courseID
 * Postcondition: template is edited and saved in the master list
*/
function submitEditTemplate(courseID, templateID) {
    const templateName = document.getElementById('nameField').value.trim();
    const coverPageID = document.getElementById('coverPageSelector').value;

    const titleFont = document.getElementById('titleFont').value.trim();
    const titleFontSize = parseInt(document.getElementById('titleFontSize').value, 10);
    const subtitleFont = document.getElementById('subtitleFont').value.trim();
    const subtitleFontSize = parseInt(document.getElementById('subtitleFontSize').value, 10);
    const bodyFont = document.getElementById('bodyFont').value.trim();
    const bodyFontSize = parseInt(document.getElementById('bodyFontSize').value, 10);


    const nameTag = document.getElementById('tempTestName').value.trim();
    const dateTag = document.getElementById('tempDate').value.trim();
    const courseTag = document.getElementById('tempCourseNum').value.trim();
    const pageNumbersInHeader = document.getElementById('pageNumH').checked;
    const pageNumbersInFooter = document.getElementById('pageNumF').checked;

    const headerText = document.getElementById('headerField').value.trim();
    const footerText = document.getElementById('footerField').value.trim();

    const bonusSection = document.getElementById('bonusToggle').value === 'True';

    if (!templateName) {
        alert("Error: Template Name is required.");
        return;
    }
    if (!titleFont || !subtitleFont || !bodyFont) {
        alert("Error: All font fields must be filled.");
        return;
    }
    if (isNaN(titleFontSize) || isNaN(subtitleFontSize) || isNaN(bodyFontSize)) {
        alert("Error: Font sizes must be valid numbers.");
        return;
    }
    if (!coverPageID) {
        alert("Error: You must choose a cover page type.");
        return;
    }
    const partStructure = collectPartStructure();
    if (!partStructure) {
        alert("Error: Template must include a valid part structure.");
        return;
    }
    
    if(bonusSection){
        if(masterTemplateList[courseID].bonusQuestions && masterTemplateList[courseID].bonusQuestions.length>0){
            masterTemplateList[courseID][templateID].bonusQuestions = masterTemplateList[courseID].bonusQuestions;   
        } else if (masterTemplateList[courseID][templateID].bonusQuestions.length>0){
            masterTemplateList[courseID][templateID].bonusQuestions = masterTemplateList[courseID][templateID].bonusQuestions;
        } else {
            alert("No bonus questions selected!");
            return;
        }
        console.log("Bonus Questions:", masterTemplateList[courseID][templateID].bonusQuestions);
    }else{
        alert("no bonus questions!");
        masterTemplateList[courseID][templateID].bonusQuestions = [];
        console.log("Bonus Questions:", masterTemplateList[courseID][templateID].bonusQuestions);
    }
    if(bonusSection && (masterTemplateList[courseID][templateID].bonusQuestions.length === 0)){
        alert("Bonus questions failed to add to template");
        return;
    }

    const templateData = {
        id: templateID,
        name: templateName,
        titleFont: titleFont,
        titleFontSize: titleFontSize,
        subtitleFont: subtitleFont,
        subtitleFontSize: subtitleFontSize,
        bodyFont: bodyFont,
        bodyFontSize: bodyFontSize,
        pageNumbersInHeader: pageNumbersInHeader,
        pageNumbersInFooter: pageNumbersInFooter,
        headerText: headerText,
        footerText: footerText,
        coverPageID: coverPageID,
        nameTag: nameTag,
        dateTag: dateTag,
        courseTag: courseTag,
        coverPage: masterCoverPageList[courseID][coverPageID],
        partStructure: partStructure,
        bonusSection: bonusSection,
        published: 0,
        bonusQuestions: masterTemplateList[courseID][templateID].bonusQuestions || [],
        feedback: []
    };

    masterTemplateList[courseID][templateID] = templateData;
    masterTemplateList[courseID].bonusQuestions = [];

    console.log("Edited Template:", templateData);

    updateTemplates(courseID);
    saveData("template", masterTemplateList[courseID][templateID], courseID)
    closeModal();
}

/**
 * This function is used to edit a draft test after it has been saved in the master list
 * Precondition: valid courseID, testIndex, not published
 * Postcondition: test is edited and saved in the master list
*/
function editTest(courseID, testID) {
    const test = masterTestList[courseID]['drafts'][testID];
    if(masterTestList[courseID]['published'][testID]){
        alert("You cannot edit published tests.");
        return;
    }
    // Open the edit modal and populate it with the test data
    const modal = document.getElementById('editModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    modalTitle.innerText = 'Edit Test';

    const formContent = `
        <div style="background:#e0e0e0;padding:20px;" id="testEditor">
            <label>Test Name:</label><br/>
            <input type="text" id="nameField" value="${test.name}"><br><br>
            <p>Choose a Template!</p><br/>
            <div id="templateSelectorPane">
                <select id="templateSelector">
                    <option value="" disabled>Please Select a Template</option>
                </select> 
                <button id="templateSelection" onclick="updateTestParts('${courseID}')">Select This One!</button>
                <div id="testParts"></div>
            </div>
            <button class="save-btn" id="testDraftButton" onclick="submitEditedTest('${courseID}', '${false}', ${testID})">Save as Draft</button>
            <button class="save-btn" id="testPublishButton" onclick="submitEditedTest('${courseID}', '${true}', ${testID})">Publish Test</button>
        </div>
    `;

    modalBody.innerHTML = formContent;

    // Populate the template selector
    updateTemplateSelection(courseID);

    // Set the selected template
    const templateSelector = document.getElementById('templateSelector');
    templateSelector.value = test.templateID;
    test.template = masterTemplateList[courseID][test.templateID];
    // Populate the test parts
    updateTestParts(courseID);
    
    // After test parts are populated, load existing questions
    setTimeout(() => {
        populateExistingQuestions(courseID, test);
    }, 500); // Give time for updateTestParts to complete
    
    modal.style.display = 'flex';
    setTimeout(() => {
        modal.style.opacity = '1';
    }, 10);
}

// New helper function to populate existing questions -Help from Claude here (AW)
function populateExistingQuestions(courseID, test) {
    test.parts.forEach((part, partIndex) => {
        part.sections.forEach((section, sectionIndex) => {
            const sectionContainer = document.getElementById(`part-${partIndex}-section-${sectionIndex}-container`);
            
            if (!sectionContainer) {
                console.error(`Section container not found: part-${partIndex}-section-${sectionIndex}-container`);
                return;
            }

            // Find the selected-questions div within the section container
            const selectedQuestionsDiv = sectionContainer.querySelector('.selected-questions');
            if (!selectedQuestionsDiv) {
                console.error(`Selected questions container not found in section ${partIndex}-${sectionIndex+1}`);
                return;
            }

            // Clear any existing content
            selectedQuestionsDiv.innerHTML = '';
            
            // Create a section-wide point value input
            const sectionPointsDiv = document.createElement("div");
            sectionPointsDiv.innerHTML = `
                <label>Set All Points for This Section: </label>
                <input type="number" id="section-${partIndex}-${sectionIndex}-points" min="1" value="1" style="width: 60px;">
                <button onclick="updateSectionPoints(${partIndex}, ${sectionIndex})">Apply</button>
                <hr>
            `;
            selectedQuestionsDiv.appendChild(sectionPointsDiv);

            // Add each question to the section
            const questionType = section.questionType.toLowerCase();
            section.questions.forEach((question) => {
                // Get full question data from master list
                const questionData = masterQuestionList[courseID][questionType][question.id];
                if (!questionData) {
                    console.error(`Question data not found for ID: ${question.id}, type: ${questionType}`);
                    return;
                }
                
                const questionElement = document.createElement("div");
                questionElement.style.padding = "8px";
                questionElement.style.margin = "5px 0";
                questionElement.style.backgroundColor = "#f0f0f0";
                questionElement.style.borderRadius = "4px";
                questionElement.dataset.questionID = question.id;

                questionElement.innerHTML = `
                    <p>${questionData.text || 'Question text not available'}</p>
                    <label>Points: </label>
                    <input type="number" class="question-points" min="1" value="${question.assigned_points || 1}" style="width: 60px;">
                `;

                selectedQuestionsDiv.appendChild(questionElement);
            });
            
            // Add randomize button
            const randomizer = document.createElement("button");
            randomizer.className = "add-btn";
            randomizer.textContent = "Randomize Question Order";
            randomizer.onclick = function() {
                const questionElements = Array.from(selectedQuestionsDiv.children).slice(1); // Skip the first child
                ShuffleArray(questionElements);
                selectedQuestionsDiv.innerHTML = ''; 
                selectedQuestionsDiv.appendChild(sectionPointsDiv);
                questionElements.forEach((element) => {
                    selectedQuestionsDiv.appendChild(element);
                });
            };
            selectedQuestionsDiv.appendChild(randomizer);
        });
    });
    
}

/**
 * This renames attachments, not much else to it, it is an editor to facilitate renaming them
 * Precondition: valid attachmentIndex and courseID
 * Postcondition: the attachment editer is opened
*/
function editAttachment(courseID, attachmentIndex) {
    const attachment = masterAttachmentList[courseID][attachmentIndex];

    // Open the edit modal and populate it with the attachment data
    const modal = document.getElementById('editModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    modalTitle.innerText = 'Edit Attachment';

    const formContent = `
        <label>Attachment Name:</label><br/>
        <input type="text" id="editAttachmentName" value="${attachment.name}"><br><br>
        <button class="save-btn" onclick="submitEditAttachment('${courseID}', ${attachmentIndex})">Submit Edit</button>
    `;

    modalBody.innerHTML = formContent;
    modal.style.display = 'flex';
    setTimeout(() => {
        modal.style.opacity = '1';
    }, 10);
}



/**
 * This publishes the changes to the attachment name made in the editAttachment function
 * Precondition: valid courseID, attachmentIndex
 * Postcondition: attachment is renamed
*/
function submitEditAttachment(courseID, attachmentID) {
    const newName = document.getElementById('editAttachmentName').value.trim();

    if (!newName) {
        alert("Attachment name is required.");
        return;
    }

    masterAttachmentList[courseID][attachmentID].name = newName;
    updateAttachments(courseID);
    saveData("attachment", masterAttachmentList[courseID][attachmentID], courseID);
    closeModal();
}



/**
 * This function is called to submit an edited test
 * Precondition: valid courseID, isPublished, testIndex
 * Postcondition: test is edited and saved in the master list
*/
function submitEditedTest(courseID, isPublished, testID) {
    const testName = document.getElementById("nameField").value.trim();
    if (!testName) {
        alert("Test Name is required.");
        return;
    }

    const templateID = document.getElementById("templateSelector").value;
    if (!templateID) {
        alert("Please select a template first");
        return;
    }

    const template = masterTemplateList[courseID][templateID];
    
    let usedQuestions = [];

    const testData = {
        id: testID,
        name: testName,
        template: template,
        templateName: template.name,
        templateID: templateID,
        attachments: [],
        parts: [],
        feedback: []
    };

    // Loop through all parts and sections rendered in the UI
    const testParts = document.getElementById("testParts");
    const partContainers = testParts.querySelectorAll('[id^="part-"][id$="-container"]:not([id*="-section-"])');
    let noquestions = true;
    partContainers.forEach((partContainer, partIndex) => {
        const partData = {
            partNumber: partIndex + 1,
            sections: []
        };

        // Find all section containers within this part
        const sectionContainers = partContainer.querySelectorAll('[id^="part-' + partIndex + '-section-"]');

        sectionContainers.forEach((sectionContainer, sectionIndex) => {
            const questionType = template.partStructure[partIndex].sections[sectionIndex].questionType;
            const selectedQuestionsDiv = sectionContainer.querySelector('.selected-questions');

            // Skip sections with no questions
            if (!selectedQuestionsDiv || !selectedQuestionsDiv.children.length) {
                return;
            }

            const sectionData = {
                sectionNumber: sectionIndex + 1,
                questionType: questionType,
                questions: []
            };

            // Get all question divs (skip the first child which is the section points setter)
            const questionDivs = selectedQuestionsDiv.querySelectorAll('div[style*="border-radius"]');

            questionDivs.forEach((questionDiv) => {
                const questionID = questionDiv.dataset.questionID;
                const pointsInput = questionDiv.querySelector('.question-points');
                const points = pointsInput ? parseInt(pointsInput.value) : 1; 
        
                let question = {
                    "id": questionID,
                    "assigned_points": points
                }
                usedQuestions.push(masterQuestionList[courseID][questionType.toLowerCase()][questionID]);
                // Add to the questions for this section
                sectionData.questions.push(question);
                noquestions=false;
            });
            if(noquestions){
                alert("Please select questions for each section");
                return;
            }else{
                noquestions=true;
            }
            partData.sections.push(sectionData);
        });

        testData.parts.push(partData);
    });

    if (template.bonusSection) {
        const bonusPart = {
            partNumber: testData.parts.length + 1,
            sections: [{
                sectionNumber: 1,
                questionType: 'bonus',
                questions: template.bonusQuestions.map(q => {
                    id = q;
                    const types = ['tf', 'ma', 'mc', 'ms', 'es', 'sa', 'fb'];
                    for (const t of types) {
                        if (masterQuestionList[courseID][t] && masterQuestionList[courseID][t][id]) {
                            question = masterQuestionList[courseID][t][id];
                        }
                    }
                    if (isPublished === 'true') {
                        question.published = 1;
                    }
                    return question;
                })
            }]
        };
        testData.parts.push(bonusPart);
    }


    if (isPublished === 'true') {
        testData.published = 1;
    } 

    saveData("test", testData, courseID);

    updateTestTabs(courseID);
    closeModal();
}