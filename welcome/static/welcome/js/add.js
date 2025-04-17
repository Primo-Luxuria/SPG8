/**
 * Switches between the tabs of a tabbed pane
 * Precondition: valid tab ID to switch to
 * Postcondition: switches to that tab in the correct tabbed pane, activates a different one
*/
function switchTab(event, tabID) {
    const parentContainer = event.target.closest('.tab-container');
    const tabs = parentContainer.querySelectorAll('.tab');
    const contents = parentContainer.querySelectorAll('.tab-content');

    tabs.forEach(tab => tab.classList.remove('active'));
    contents.forEach(content => content.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById(tabID).classList.add('active');
}

/**
* Opens the editor modal. This behaves differently depending on what is edited
* Currently the attachment, template, question, and test editors are implemented
* Precondition: valid course, edit button pushed
* Postcondition: opens up a modal over the webpage content that allows you to create new data
*/
function openEditor(type, courseID) {
const modal = document.getElementById('editModal');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');

modalTitle.innerText = `Add ${type}`;

let formContent = '';    

if (type != "Question"){
formContent += `
<label>${type} Name:</label><br/>
<input type="text" id="nameField"><br><br>
`;
}

if (type === "Question") {
formContent += `
    <label>Question:</label><br/>
    <textarea id="questionField" rows="5" placeholder="Enter question text here..."></textarea><br><br>
    
    <label>Question Type:</label><br/>
    <select id="typeField" onchange="updateQuestionForm()">
        <option value="" disabled selected>Select Question Type</option>
        <option value="tf">True/False</option>
        <option value="mc">Multiple Choice</option>
        <option value="sa">Short Answer</option>
        <option value="es">Essay</option>
        <option value="ma">Matching</option>
        <option value="ms">Multiple Selections</option>
        <option value="fb">Fill in the Blank</option>
    </select><br><br>

    <div id="questionSpecificFields"></div>

    <label>Point Value:</label><br/>
    <input type="number" id="pointValueField" min="1"><br><br>

    <label for="qChapter" >Chapter:</label><br/>    
    <input type="number" id="qChapter" min="1"><br><br>

    <label for="qSection" >Section:</label><br/> 
    <input type="number" id="qSection" min="1"><br><br>

    <label>Estimated Time to Solve (Minutes):</label><br/>
    <input type="number" id="qTimeField" min="1"><br><br>

    <label>Grading Instructions:</label><br/>
    <textarea id="instructionField" rows="6" placeholder="Grading instructions should be provided for partial credit, short or long answer questions, or questions where a rubric is necessary."></textarea><br><br>

    <label>Reference Text (Optional):</label><br/>
    <textarea id="refField" rows="3" placeholder="Reference text if needed..."></textarea><br><br>

    <label>Embedded Graphic (Optional):</label><br/>
    <select id="qGraphicField">
        <option value="" disabled selected>Select a graphic</option>
    </select><br><br>

    <label>Embedded Graphic for the Correct Answer (Optional):</label><br/>
    <select id="ansGraphicField">
        <option value="" disabled selected>Select a graphic</option>
    </select><br><br>

    <label>Instructor Comments (Optional):</label><br/>
    <textarea id="instructorCommentField" placeholder="Comments go here"></textarea><br><br>

    <button class="save-btn" onclick="addQuestion('${courseID}')">Submit Question</button>
`;
}

if (type === "Cover Page"){
//Needs: test instructions, course number, test number, date of test, filename of the test,
//  blank for student name, and grading instructions for the key
formContent+= `
<div style="background:#e0e0e0;padding:20px;" id="coverPageEditor">
    <p>Create your Cover Page!</p><br/>
    <label>Test Number</label>
    <input type="number" id="tNum" min="0"/><br/>

    <label>Test Date</label>
    <input type="date" id="tDate"/><br/>

    <label>Test Filename (no extension)</label>
    <input id="filename" type="text"/><br/>

    <label>Filename Present on CoverPage</label>
    <input id="filenameTF" type="checkbox"/><br/>

    <label>Student Name Location</label>
    <select id="nameBlankSelector">
        <option value="" disabled selected>Please select a location</option>
        <option value="TR">Top Right</option>
        <option value="TL">Top Left</option>
        <option value="BT">Below the Title</option>
    </select><br/><br/>

    <label>Grading Instructions for Key</label>
    <textarea id="instructions" name="instruct" rows="3" placeholder="Add your instructions for grading here. These will go into the test key."></textarea>
    <br/>
    <button class="save-btn" onclick="submitCoverPage('${courseID}')">Submit</button>
</div>
`;
}


if (type === "Test"){
formContent+= `
<div style="background:#e0e0e0;padding:20px;" id="testEditor">
    <p>Choose a Template!</p><br/>
    <div id=templateSelectorPane>
        <select id=templateSelector>
            <option value="" disabled selected>Please Select a Template</option>
        </select> <button id=templateSelection onclick="updateTestParts('${courseID}')">Select This One!</button>
        <div id="testParts"> </div>
    </div>
    <button class="add-btn" id="testDraftButton" onclick="saveTest('${courseID}', '${false}')">Save as Draft</button>
    <button class="add-btn" id="testPublishButton" onclick="saveTest('${courseID}', '${true}')">Publish Test</button>
</div>
`;
setTimeout(() => {
updateTemplateSelection(courseID);
}, 50);

}


if (type === "Template") {
formContent += `
    <div  style="background:#e0e0e0;padding:20px;" id="templateEditor"> 
<h1>Font Settings</h1>
  <label>Title Font and Font Size:</label><br/>
<select id="titleFont">
    <option value="" selected disabled>Please choose a font</option>
    <option value="Times New Roman">Times New Roman</option>
    <option value="Arial">Arial</option>
    <option value="Calibri">Calibri</option>
    <option value="Helvetica">Helvetica</option>
    <option value="Georgia">Georgia</option>
    <option value="Cambria">Cambria</option>
    <option value="Garamond">Garamond</option>
</select>
<input type="number" id="titleFontSize" min="1" value="36"><br/><br/>

<label>Subtitle Font and Font Size:</label><br/>
<select id="subtitleFont">
    <option value="" selected disabled>Please choose a font</option>
    <option value="Times New Roman">Times New Roman</option>
    <option value="Arial">Arial</option>
    <option value="Calibri">Calibri</option>
    <option value="Helvetica">Helvetica</option>
    <option value="Georgia">Georgia</option>
    <option value="Cambria">Cambria</option>
    <option value="Garamond">Garamond</option>
</select>
<input type="number" id="subtitleFontSize" min="1" value="24"><br/><br/>

<label>Body Font and Font Size:</label><br/>
<select id="bodyFont">
    <option value="" selected disabled>Please choose a font</option>
    <option value="Times New Roman">Times New Roman</option>
    <option value="Arial">Arial</option>
    <option value="Calibri">Calibri</option>
    <option value="Helvetica">Helvetica</option>
    <option value="Georgia">Georgia</option>
    <option value="Cambria">Cambria</option>
    <option value="Garamond">Garamond</option>
</select>
<input type="number" id="bodyFontSize" min="1" value="12"><br/><br/>


<h1>Tags Section (Optional)</h1>
<div class="form-container">
    <div class="form-group"><label>Test Name </label> <input type="text" id="tempTestName"></div>
    <div class="form-group"><label>Date </label> <input type="text" id="tempDate"></div>
    <div class="form-group"><label>Course Number </label> <input type="text" id="tempCourseNum"></div>
</div>

  <h1>Header and Footer Settings</h1>
<label>Location of Student Score Blank (On the second page of the test)</label>
<select id="studentScoreSelector">
    <option value="" disabled selected>Please Select a Location</option>
    <option value="TR"> Top Right</option>
    <option value="TL"> Top Left</option>
</select><br/><br/>
<label>Page Numbers in Header</label><br/>
<input type="checkbox" id="pageNumH"><br/>
<label>Page Numbers in Footer</label><br/>
<input type="checkbox" id="pageNumF"><br/><br/>
<textarea id="headerField" rows="3" placeholder="Enter any desired header text ..."></textarea>
<textarea id="footerField" rows="3" placeholder="Enter any desired footer text..."></textarea>

<h1>Cover Page Selection</h1><br/>
<select id="coverPageSelector">
    <option value="" disabled selected>Please Select a Cover Page</option>
</select><br/><br/>

<h1>Test Structure Settings</h1>
<label>Number of Parts:</label>
<input type="number" id="partCount" min="1" value="1">
<button onclick="updateParts()">Update</button>
<div style="background:#c0c0c0;padding:20px;" id="partsContainer"><p>No Parts Chosen</p></div>
    

<h1>Bonus Question Section Toggle</h1>
<select id="bonusToggle" onchange="toggleBonusQuestionSelection('${courseID}')">
<option value="True">Bonus Section</option>
<option value="False" selected>No Bonus Section</option>
</select><br/><br/>
<div id="selectedBonusQuestionsContainer"><p>"No bonus questions selected"</p></div>
<button class="add-btn" id="selectBonusQuestionsBtn" style="display:none;" onclick="openBonusQuestionModal('${courseID}')">Select Bonus Questions</button>
<button class="save-btn" onclick="addTemplate('${courseID}')">Submit Template</button></div>
`;

setTimeout(() => {
updatePageSelection(courseID);
}, 50);
}


if (type === "Attachment"){
formContent+=`
    <input type="file" id="newAttachment" name="attachment">
    <button class="save-btn" onclick="submitAttachment('${courseID}')">Submit Attachment</button>
`;
}

// Ensure the modal content is updated
modalBody.innerHTML = formContent;

// Show the modal
modal.style.display = "flex";
setTimeout(() => {
modal.style.opacity = "1";
}, 10);

if (type === "Question") {
updateGraphicSelectors(courseID);
}

}

function updateParts() {
const partCount = parseInt(document.getElementById("partCount").value);
const partsContainer = document.getElementById("partsContainer");
partsContainer.innerHTML = ""; // Clear existing content

for (let i = 1; i <= partCount; i++) {
 let sectionInputId = `sectionCount-${i}`;
 partsContainer.innerHTML += `
     <div id="part-${i}">
         <label>Sections in Part ${i}:</label>
         <input type="number" id="${sectionInputId}" min="1" value="1"> 
         <button onclick="updateSections(${i})">Update</button>
         <div style="background:#c0c0c0;padding:20px;" id="sectionsContainer-${i}"><p>No Sections Chosen...</p></div>
     </div><br>
 `;
}
}

function updateSections(partNumber) {
const sectionCount = parseInt(document.getElementById(`sectionCount-${partNumber}`).value);
const sectionsContainer = document.getElementById(`sectionsContainer-${partNumber}`);
sectionsContainer.innerHTML = ""; // Clear old sections

for (let j = 1; j <= sectionCount; j++) {
 sectionsContainer.innerHTML += `
     <label>Question Type for Section ${j}:</label>
     <select class="sectionTypeSelect">
         <option value="tf">True/False</option>
         <option value="mc">Multiple Choice</option>
         <option value="sa">Short Answer</option>
         <option value="es">Essay</option>
         <option value="ma">Matching</option>
         <option value="ms">Multiple Selections</option>
         <option value="fb">Fill in the Blank</option>
     </select><br>
 `;
}
}



/**
* Updates the different possible options for a question type in the question editor
* Precondition: valid question type
* Postcondition: question editor is updated with the correct fields for the question type
*/
function updateQuestionForm() {
const type = document.getElementById('typeField').value;
const questionSpecificFields = document.getElementById('questionSpecificFields');
questionSpecificFields.innerHTML = '';

if (type === 'tf') {
questionSpecificFields.innerHTML = `
    <label>Correct Answer:</label><br/>
    <select id="answerField">
        <option value="true">True</option>
        <option value="false">False</option>
    </select><br><br>
`;
} else if (type === 'sa' || type === 'es') {
questionSpecificFields.innerHTML = `
    <label>Correct Answer:</label><br/>
    <textarea id="answerField" rows="4" placeholder="Enter the correct answer here..."></textarea><br><br>
`;
} else if (type === 'mc') {
questionSpecificFields.innerHTML = `
    <label>Options:</label><br/>
    <input type="text" id="optionA" placeholder="Option A"><br>
    <input type="text" id="optionB" placeholder="Option B"><br>
    <input type="text" id="optionC" placeholder="Option C"><br>
    <input type="text" id="optionD" placeholder="Option D"><br><br>
    <label>Correct Answer:</label><br/>
    <select id="answerField">
        <option value="A">A</option>
        <option value="B">B</option>
        <option value="C">C</option>
        <option value="D">D</option>
    </select><br><br>
`;
} else if (type === 'ma') {
questionSpecificFields.innerHTML = `
    <label>Number of Pairs:</label><br/>
    <input type="number" id="numPairs" min="1" step="1" onchange="updateOptions('${type}')"><br>
    <label>Number of Distractions:</label><br/>
    <input type="number" id="numDistractions" min="0" step="1" onchange="updateOptions('${type}')"><br><br>
    <div id="optionsContainer"></div>
`;
} else if (type === 'ms') {
questionSpecificFields.innerHTML = `
    <label>Number of Options (Max 20):</label><br/>
    <input type="number" id="numOptions" min="1" max="20" onchange="updateOptions('${type}')"><br><br>
    <div id="optionsContainer"></div>
`;
} else if (type === 'fb') {
questionSpecificFields.innerHTML = `
    <label>Number of Blanks:</label><br/>
    <input type="number" id="numBlanks" min="1" onchange="updateOptions('${type}')"><br><br>
    <div id="optionsContainer"></div>
`;
}
}


/**
* Adding the cover page to the list of coverpages
* Precondition: all necessary data is in the coverpage editor
* Postcondition: cover page added to the list
*/
function submitCoverPage(courseID) {
const pageName = document.getElementById("nameField").value.trim();
const testNumber = document.getElementById("tNum").value.trim();
const testDate = document.getElementById("tDate").value.trim();
const filename = document.getElementById("filename").value.trim();
const filenameTF = document.getElementById("filenameTF").checked;
const nameBlankSelector = document.getElementById("nameBlankSelector").value.trim();
const gradingInstructions = document.getElementById("instructions").value.trim();

if (!pageName || !testNumber || !testDate || !filename || !nameBlankSelector || !gradingInstructions) {
alert("Cover page name, Test number, test date, filename, name blank selection, and grading instructions are required fields!");
return;
}

if (!masterCoverPageList[courseID]) {
masterCoverPageList[courseID] = {};
}

const coverPage = {
name: pageName,
testNum: testNumber,
date: testDate,
file: filename,
showFilename: filenameTF,
blank: nameBlankSelector,
instructions: gradingInstructions,
published: 0
};

saveData("coverPage", coverPage, courseID)
closeModal();
}

/**
* Submit attachments to the attachmentList
* Precondition: valid attachment
* Postcondition: attachment posted to attachmentList
*/
function submitAttachment(courseID) {
const attachment = document.getElementById("newAttachment").files[0];
const name = document.getElementById("nameField").value.trim();

if (!attachment || !name) {
alert("Attachment file and name are required.");
return;
}

if (!masterAttachmentList[courseID]) {
masterAttachmentList[courseID] = [];
}

let newattachment  = { name: name, file: attachment, url:name};
saveData("attachment", newattachment, courseID)
closeModal();
}

/**
* Updates the attachments for a given course
* Precondition: valid courseID, attachmentList
* Postcondition: the attachments dropdown will have interactible div containers for each attachment
*/
function updateAttachments(courseID) {
const attachmentList = masterAttachmentList[courseID];
const attachmentContainer = document.getElementById("attachments-" + courseID);
attachmentContainer.innerHTML = "";

if (attachmentList.length === 0) {
attachmentContainer.innerHTML = '<p>You have not uploaded any attachments yet...</p>';
return;
}
let index = 1;
for(const key in attachmentList){
    
    attachment = attachmentList[key];
    const attachmentDiv = document.createElement("div");
attachmentDiv.style.backgroundColor = "#d0d0d0";
attachmentDiv.style.padding = '5px';
attachmentDiv.style.marginBottom = '8px';
attachmentDiv.style.borderBottom = '1px solid #ccc';
attachmentDiv.classList.add('context-menu-target');
attachmentDiv.dataset.itemType = 'attachment';
attachmentDiv.dataset.itemID = attachment.id;
attachmentDiv.dataset.courseID = courseID;

const attachmentLabel = document.createElement("p");
attachmentLabel.innerHTML = `Attachment ${index}: ${attachment.name}`;
attachmentDiv.appendChild(attachmentLabel);
const imageElement = document.createElement("img");
imageElement.src = attachment.url; 
imageElement.alt = attachment.name;  
imageElement.style.maxWidth = "100%"; 
attachmentDiv.appendChild(imageElement);

attachmentContainer.appendChild(attachmentDiv);
index++;
}
}


/**
* Adds a template to the templateList
* Precondition: valid courseID and template info
* Postcondition: adds a new template to the list
*/
function addTemplate(courseID) {
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
if (bonusSection && (!masterTemplateList[courseID].bonusQuestions || masterTemplateList[courseID].bonusQuestions.length === 0)) {
alert("Error: You must select bonus questions if the bonus section is enabled.");
return;
}

const templateData = {
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
bonusQuestions: masterTemplateList[courseID].bonusQuestions || [],
published: 0
};

if (!masterTemplateList[courseID]) {
masterTemplateList[courseID] = [];
}
alert("coverpageID: " + coverPageID)
saveData("template", templateData, courseID);
updateTemplates(courseID);
closeModal();
}


/**
* This grabs the structure of the parts and sections inside of a template.
* It makes the structure of the test that is outlined by a template a lot easier
* to work with in other methods, since you can grab a template's partStructure instead of
* its sections and parts and questions invidually.
* Precondition: valid part and section count choices, valid question type choices
* Postcondition: outputs a structure of parts and sections for a template
*/
function collectPartStructure() {
const partCount = parseInt(document.getElementById('partCount').value);
const partStructure = [];

// Validate part count
if (isNaN(partCount) || partCount < 1) {
alert("Error: Please enter a valid number of parts.");
return null; // Return null instead of undefined to prevent further execution
}

for (let i = 1; i <= partCount; i++) {
const sectionCountInput = document.getElementById(`sectionCount-${i}`);

if (!sectionCountInput) {
    alert(`Error: Section count input is missing for Part ${i}.`);
    return null;
}

const sectionCount = parseInt(sectionCountInput.value);

// Validate section count
if (isNaN(sectionCount) || sectionCount < 1) {
    alert(`Error: Please enter a valid number of sections for Part ${i}.`);
    return null;
}

const part = {
    partNumber: i,
    sections: []
};

const sectionContainer = document.getElementById(`sectionsContainer-${i}`);
if (!sectionContainer) {
    alert(`Error: Sections container missing for Part ${i}.`);
    return null;
}

const sectionSelects = sectionContainer.querySelectorAll('select');

if (sectionSelects.length !== sectionCount) {
    alert(`Error: The number of section selectors does not match the section count for Part ${i}.`);
    return null;
}

sectionSelects.forEach((select, j) => {
    if (!select.value) {
        alert(`Error: Please select a question type for Section ${j + 1} in Part ${i}.`);
        return null;
    }
    
    part.sections.push({
        sectionNumber: j + 1,
        questionType: select.value
    });
});

partStructure.push(part);
}

return partStructure;
}


/**
* Updates the potential options for cover pages when you open the template editor
* Precondition: Valid courseID
* Postcondition: populated selector in template editor (editmodal)
*/
function updatePageSelection(courseID) {
const selection = document.getElementById("coverPageSelector");

// Clear existing options
selection.innerHTML = '<option value="" disabled selected>Please Select a Cover Page</option>';

if (!masterCoverPageList[courseID] || Object.keys(masterCoverPageList[courseID]).length === 0) {
alert("No cover pages available for this course!");
return;
}

for(const key in masterCoverPageList[courseID]){
    page = masterCoverPageList[courseID][key];
    const newOption = document.createElement("option");
newOption.value = page.id; 
newOption.textContent = page.name;
selection.appendChild(newOption);   
}
}


/**
* Updates the potential options for templates when you open the test editor
* Precondition: valid courseID
* Postcondition: populated selector in test editor (editmodal)
*/
function updateTemplateSelection(courseID){
if(!masterTemplateList[courseID]){
    masterTemplateList[courseID] = {};
}else if(Object.keys(masterTemplateList[courseID]).length==0){
    console.log("No templates available for this course!");
}else{
const templateList = masterTemplateList[courseID];
for(const key in templateList){
    template = templateList[key];
    const selection = document.getElementById("templateSelector");
    const newoption = document.createElement("option");
    newoption.value = template.id;
    newoption.textContent= template.name;
    selection.appendChild(newoption);
}
}
}



/**
* Adding the question from the currently open editModal in question mode.
* Preconditions: expects a valid courseID, and for all of the required fields to be present
* Postconditions: adds the question to the appropriate array for its type in the course questionList
*/
function addQuestion(courseID) {
const text = document.getElementById("questionField").value.trim();
const type = document.getElementById("typeField").value;
const points = document.getElementById("pointValueField").value.trim();
const instructions = document.getElementById("instructionField").value.trim();
const refText = document.getElementById("refField").value.trim();
const time = document.getElementById("qTimeField").value.trim();
const graphic = document.getElementById("qGraphicField").value;
const ansgraphic = document.getElementById("ansGraphicField").value;
const instcomm = document.getElementById("instructorCommentField").value;
const chapter = document.getElementById("qChapter").value.trim();
const section = document.getElementById("qSection").value.trim();

if (!text || !type || !points || !instructions || !time || !chapter || !section) {
alert("Some fields (Question, Question Type, Default Point Value, and Grading Instructions) are required. For chapter or section, put 0 if not applicable.");
return;
}

let answer = {};
let options = {};

if (type === 'tf') {
answer.value = document.getElementById("answerField").value.trim();
} else if (type === 'sa' || type === 'es') {
answer.value = document.getElementById("answerField").value.trim();
} else if (type === 'mc') {
options.A =  {text:document.getElementById("optionA").value.trim(), order:1},
options.B =  {text:document.getElementById("optionB").value.trim(), order:2},
options.C =  {text:document.getElementById("optionC").value.trim(), order:3},
options.D =  {text:document.getElementById("optionD").value.trim(), order:4}
answer.value = document.getElementById("answerField").value.trim();
} else if (type === 'ma') {
const numPairs = parseInt(document.getElementById("numPairs").value);
const numDistractions = parseInt(document.getElementById("numDistractions").value);
options.numPairs = numPairs;
options.numDistractions = numDistractions;
for (let i = 1; i <= numPairs*2; i+=2) {
    let pairNum = (i-1)/2 + 1;
    let pair = {
        "left": document.getElementById(`option${i}`).value.trim(),
        "right": document.getElementById(`option${i+1}`).value.trim(),
        "pairNum": pairNum
    };
    options[`pair${pairNum}`] = pair;
}
for(let i = 1;i<=numDistractions;i++){
    let distraction = {
        text: document.getElementById(`distraction${i}`).value.trim(),
        order: i
    };
    options[`distraction${i}`] = distraction;
}
for(let i = 1; i <= numPairs*2; i+=2){
    pairNum = (i-1)/2 + 1;
    pair = options[`pair${pairNum}`];
    answer[`pair-${pairNum}`] = {text:`{${pair.left}, ${pair.right}}`};
}
} else if (type === 'ms') {
const numOptions = parseInt(document.getElementById("numOptions").value);
for (let i = 1; i <= numOptions; i++) {
    let option  = {
        text: document.getElementById(`option${i}`).value.trim(),
        order: i
    }
    options[`option${i}`]=option;
    if (document.getElementById(`correct${i}`).checked) {
        answer[`option${i}`] = { value: option.text };
    }
}
} else if (type === 'fb') {
const numBlanks = parseInt(document.getElementById("numBlanks").value);
for (let i = 1; i <= numBlanks; i++) {
    answer[`answer${i}`] = {
        value: document.getElementById(`blank${i}`).value.trim()
    };
}
}

const question = {
text: text,
answer: answer,
qtype: type,
score: points,
directions: instructions,
reference: refText,
eta: time,
img: graphic,
ansimg: ansgraphic,
comments: instcomm,
options: options,
feedback: [],
tests: [],
chapter: chapter,
section: section,
published: 0
};

saveData("question", question, courseID);
closeModal();
}

/**
* Updates the test editor to have the appropriate parts and section options
* Preconditions: A valid template with part and sections defined correctly, a valid course ID
* Postconditions: Populated testeditor with all of the appropriate parts and sections
*/
function updateTestParts(courseID) {  
const templateID = document.getElementById("templateSelector").value;
if (!templateID) {
    alert("You need to choose a template!");
return;
}

const template = masterTemplateList[courseID][templateID];
const partStructure = template.partStructure;

let test = document.getElementById("testParts");
test.innerHTML = ""; // Clear existing content

// Loop through each part in the template structure
for (let i = 0; i < partStructure.length; i++) {
let partContainer = document.createElement("div");
partContainer.style.padding = '5px';
partContainer.style.marginBottom = '8px';
partContainer.style.borderBottom = '1px solid #ccc';
partContainer.id = `part-${i}-container`;



let partNum = i + 1;
partContainer.innerHTML = `<h2>Part ${partNum}</h2>`;

// Loop through each section in this part
const sections = partStructure[i].sections;
for (let j = 0; j < sections.length; j++) {
    let sectionContainer = document.createElement('div');
    sectionContainer.style.padding = '5px';
    sectionContainer.style.marginBottom = '8px';
    sectionContainer.style.borderBottom = '1px solid #ccc';
    sectionContainer.style.backgroundColor = '#d3d3d3';
    sectionContainer.id = `part-${i}-section-${j}-container`;

    let sectionNum = j + 1;
    const questionType = sections[j].questionType.toLowerCase();

    sectionContainer.innerHTML = `
        <h3>Section ${sectionNum}: ${questionType.toUpperCase()} Questions</h3>
        <button class="add-btn" onclick="openQuestionModal('${courseID}', ${i}, ${j}, '${questionType}')">Choose Questions</button>
        <div class="selected-questions"></div>
    `;

    partContainer.appendChild(sectionContainer);
}

test.appendChild(partContainer);
}

// Add bonus part if it exists
if (template && template.bonusSection && template.bonusQuestions && template.bonusQuestions.length > 0) {
    const testPartsContainer = document.getElementById("testParts");
    if (!testPartsContainer) {
        console.error("Test parts container not found");
        return;
    }

    const bonusPartContainer = document.createElement("div");
    bonusPartContainer.style.padding = '5px';
    bonusPartContainer.style.marginBottom = '8px';
    bonusPartContainer.style.borderBottom = '1px solid #ccc';
    bonusPartContainer.id = `part-bonus-container`;

    bonusPartContainer.innerHTML = `<h2>Bonus Part</h2>`;

    const bonusSectionContainer = document.createElement('div');
    bonusSectionContainer.style.padding = '5px';
    bonusSectionContainer.style.marginBottom = '8px';
    bonusSectionContainer.style.borderBottom = '1px solid #ccc';
    bonusSectionContainer.style.backgroundColor = '#d3d3d3';
    bonusSectionContainer.id = `bonus-container`;

    bonusSectionContainer.innerHTML = `
        <h3>Bonus Section: Bonus Questions</h3>
    `;

    const selectedQuestionsDiv = document.createElement('div');
    selectedQuestionsDiv.className = 'selected-questions';
    
    template.bonusQuestions.forEach((questionID) => {
        
        id = questionID;
        const types = ['tf', 'ma', 'mc', 'ms', 'es', 'sa', 'fb'];
        let question = {};
        for (const t of types) {
            if (masterQuestionList[courseID][t] && masterQuestionList[courseID][t][id]) {
                question = masterQuestionList[courseID][t][id];
            }
        }            
        if (!question) {
            console.error(`Bonus question not found: ${questionID}`);
            return;
        }
        
        const questionElement = document.createElement("div");
        questionElement.style.padding = "8px";
        questionElement.style.margin = "5px 0";
        questionElement.style.backgroundColor = "#f0f0f0";
        questionElement.style.borderRadius = "4px";
        questionElement.dataset.questionID = question.id; 

        questionElement.innerHTML = `
            <p>${question.text || 'Question text not available'}</p>
            <label>Points: </label>
            <input type="number" class="question-points" min="1" value="${question.score || 1}" style="width: 60px;" disabled>
        `;

        selectedQuestionsDiv.appendChild(questionElement);
    });

    bonusSectionContainer.appendChild(selectedQuestionsDiv);
    bonusPartContainer.appendChild(bonusSectionContainer);
    testPartsContainer.appendChild(bonusPartContainer);
}
}

/**
* This rather involved function saves the test based on all the info in the test editor.
* Preconditions: a valid courseID, one of two save buttons pressed, a test name, a valid template
* Postconditions: saves the test as either a draft or published test.
*/
function saveTest(courseID, isPublished, testIndex = null) {
const testName = document.getElementById("nameField").value.trim();
if (!testName) {
alert("Test Name is required.");
return;
}

const templateID = document.getElementById("templateSelector").value;
if (!templateID) {
return;
}

const template = masterTemplateList[courseID][templateID];

let usedQuestions = [];

const testData = {
name: testName,
template: template,
templateName: template.name,
templateID: templateID,
parts: [],
attachments: [],
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
        noquestions = true;
    }
    partData.sections.push(sectionData);
});

testData.parts.push(partData);
});

if (isPublished === 'true'){
testData.published = 1;
}else{
testData.published = 0;
}


confirm(JSON.stringify(testData));

saveData("test", testData, courseID);

updateTestTabs(courseID);
closeModal();
}

/**
* Opens up the questionModal and populates it with questions of the appropriate type. 
* If such questions exist, creates checkboxes next to each one to be used for selecting questions.
* Preconditions: openQuestionModal expects a valid courseID, part number, section number, and question type
* Postconditions: opens up the question modal with questions of the appropriate type for the correct course
*/
function openQuestionModal(courseID, partNum, sectionNum, type) {
const modal = document.getElementById("questionModal");
const modalTitle = document.getElementById("questionModalTitle");
const modalBody = document.getElementById("questionModalBody");

// Check if we have questions of this type
if (!masterQuestionList[courseID][type] || Object.keys(masterQuestionList[courseID][type]).length === 0) {
alert("No questions available of this type!");
return;
}

const questions = masterQuestionList[courseID][type];
modalBody.innerHTML = ""; // Clear existing content

// Store the part/section info in the modal for later use
modalBody.dataset.courseID = courseID;
modalBody.dataset.partNum = partNum;
modalBody.dataset.sectionNum = sectionNum;
modalBody.dataset.questionType = type;

const filterContainer = document.createElement('div');
filterContainer.style.padding = '5px';
filterContainer.style.marginBottom = '8px';
filterContainer.style.borderBottom = '1px solid #ccc';


// Filter by Test
const testFilterLabel = document.createElement('label');
testFilterLabel.textContent = 'Filter by Test:';
filterContainer.appendChild(testFilterLabel);

const testFilterSelect = document.createElement('select');
testFilterSelect.id = 'testFilterSelect';
testFilterSelect.innerHTML = '<option value="" selected>All Tests</option>';
const testList = {...masterTestList[courseID]['drafts'],...masterTestList[courseID]['published']};
for(const key in testList) {
    let test = testList[key];
const option = document.createElement('option');
option.value = test.id;
option.textContent = test.name;
testFilterSelect.appendChild(option);
};
filterContainer.appendChild(testFilterSelect);
filterContainer.appendChild(document.createElement('br'));

// Chapter Filter
const chapterFilterLabel = document.createElement('label');
chapterFilterLabel.textContent = 'Filter by Chapter:';
filterContainer.appendChild(chapterFilterLabel);

const chapterFilterSelect = document.createElement('select');
chapterFilterSelect.id = 'chapterFilterSelect';

// Add "All Chapters" option
const allChaptersOption = document.createElement('option');
allChaptersOption.value = "all";
allChaptersOption.textContent = "All Chapters";
chapterFilterSelect.appendChild(allChaptersOption);

// Get unique chapters from questions

const chapters = [...new Set(Object.values(questions).map(q => q.chapter))].sort((a, b) => a - b);
chapters.forEach(chapter => {
const option = document.createElement('option');
option.value = chapter;
option.textContent = `Chapter ${chapter}`;
chapterFilterSelect.appendChild(option);
});
filterContainer.appendChild(chapterFilterSelect);
filterContainer.appendChild(document.createElement('br'));

// Section Filter (initially hidden)
const sectionFilterContainer = document.createElement('div');
sectionFilterContainer.id = 'sectionFilterContainer';
sectionFilterContainer.style.display = 'none';
sectionFilterContainer.style.marginTop = '5px';

const sectionFilterLabel = document.createElement('label');
sectionFilterLabel.textContent = 'Filter by Section:';
sectionFilterContainer.appendChild(sectionFilterLabel);

const sectionFilterSelect = document.createElement('select');
sectionFilterSelect.id = 'sectionFilterSelect';
sectionFilterContainer.appendChild(sectionFilterSelect);

filterContainer.appendChild(sectionFilterContainer);
modalBody.appendChild(filterContainer);

const questionContainer = document.createElement('div');
questionContainer.id = 'questionContainer';
questionContainer.style.padding = '5px';
questionContainer.style.marginBottom = '8px';
questionContainer.style.borderBottom = '1px solid #ccc';

// Display all questions initially
renderQuestions(questions, questionContainer);

const submitButton = document.createElement('button');
submitButton.className = 'add-btn';
submitButton.textContent = 'Add Selected Questions';
submitButton.onclick = function() {
addSelectedQuestions();
};

modalBody.appendChild(questionContainer);
modalBody.appendChild(submitButton);

modalTitle.innerText = `Select ${type.toUpperCase()} Questions`;

modal.style.display = "flex";
setTimeout(() => {
modal.style.opacity = "1";
}, 10);

// Add event listeners for filters
testFilterSelect.addEventListener('change', () => filterQuestions(courseID, type));

// Chapter filter change event
chapterFilterSelect.addEventListener('change', function() {
const selectedChapter = this.value;
const sectionContainer = document.getElementById('sectionFilterContainer');
const sectionSelect = document.getElementById('sectionFilterSelect');

// Clear and hide section filter if "All Chapters" is selected
if (selectedChapter === "all") {
    sectionContainer.style.display = 'none';
    sectionSelect.innerHTML = '';
} else {
    // Show section filter and populate with sections from selected chapter
    sectionContainer.style.display = 'block';
    
    // Clear existing options
    sectionSelect.innerHTML = '';
    
    // Add "All Sections" option
    const allSectionsOption = document.createElement('option');
    allSectionsOption.value = "all";
    allSectionsOption.textContent = "All Sections";
    sectionSelect.appendChild(allSectionsOption);
    
    // Get unique sections for the selected chapter
    const sectionsInChapter = [...new Set(
        Object.values(questions)
        .filter(q => q.chapter == selectedChapter)
        .map(q => q.section)
    )].sort((a, b) => a - b);
    
    sectionsInChapter.forEach(section => {
        const option = document.createElement('option');
        option.value = section;
        option.textContent = `Section ${section}`;
        sectionSelect.appendChild(option);
    });
}

// Apply filters
filterQuestions(courseID, type);
});

// Section filter change event
document.getElementById('sectionFilterSelect').addEventListener('change', () => {
filterQuestions(courseID, type);
});
}

function renderQuestions(questions, container) {
container.innerHTML = '';

if (Object.keys(questions).length === 0) {
const noQuestionsMsg = document.createElement('p');
noQuestionsMsg.textContent = 'No questions match the selected filters.';
container.appendChild(noQuestionsMsg);
return;
}

for(const key in questions){
    let question = questions[key];
    const element = document.createElement("div");
    element.style.padding = '8px';
    element.style.margin = '5px 0';
    element.style.backgroundColor = '#f0f0f0';
    element.style.borderRadius = '4px';
    element.innerHTML = `
    <input type="checkbox" id="q-${question.id}" value="${question.id}">
    <label for="q-${question.id}">${question.text} (${question.score} Points) - Ch.${question.chapter}, Sec.${question.section}</label>
`;   
container.appendChild(element);
}
}



/**
* Filters the type of questions that are selectable in the menu for the test editor
* Preconditions: valid courseID, type
* Postconditions: filters the questions by test and/or chapter/section
* TODO: Complete textbook support
*/
function filterQuestions(courseID, type) {
const questions = masterQuestionList[courseID][type];
const testFilterValue = document.getElementById('testFilterSelect').value;
const chapterFilterValue = document.getElementById('chapterFilterSelect').value;
const sectionFilterSelect = document.getElementById('sectionFilterSelect');
const sectionFilterValue = sectionFilterSelect && sectionFilterSelect.style.display !== 'none' ? 
                       sectionFilterSelect.value : "all";

// Create a filtered index map to maintain original ids
const filteredIDs = [];
const filteredQuestions = [];

for(const key in questions){
let includeQuestion = true;
let question = questions[key];
// Apply test filter if selected
if (testFilterValue !== "") {
    const testID = parseInt(testFilterValue);
    let idMatch =false;
    for(let i=0;i<question.tests.length;i++){
        if(question.tests[i]==testID){
            idMatch = true;
        }
    }
    if(!idMatch){
        includeQuestion = false;
    }
}

// Apply chapter filter if selected
if (chapterFilterValue !== "all" && question.chapter != chapterFilterValue) {
    includeQuestion = false;
}

// Apply section filter if visible and selected
if (chapterFilterValue !== "all" && sectionFilterValue !== "all" && 
    question.section != sectionFilterValue) {
    includeQuestion = false;
}

if (includeQuestion) {
    filteredIDs.push(question.id);
    filteredQuestions.push(question);
}
}


// Render filtered questions while preserving original indices
const questionContainer = document.getElementById('questionContainer');
questionContainer.innerHTML = '';

if (filteredQuestions.length === 0) {
const noQuestionsMsg = document.createElement('p');
noQuestionsMsg.textContent = 'No questions match the selected filters.';
questionContainer.appendChild(noQuestionsMsg);
return;
}

filteredQuestions.forEach((question, i) => {
const originalID = filteredIDs[i];
const element = document.createElement("div");
element.style.padding = '8px';
element.style.margin = '5px 0';
element.style.backgroundColor = '#f0f0f0';
element.style.borderRadius = '4px';
element.innerHTML = `
    <input type="checkbox" id="q-${originalID}" value="${originalID}">
    <label for="q-${originalID}">${question.text} (${question.score} Points) - Ch.${question.chapter}, Sec.${question.section}</label>
`;   
questionContainer.appendChild(element);
});
}


/**
* This adds the questions selected in the questionModal to the test editor.
* It uses data included in the modalBody using the dataset property from HTMLElement
* Preconditions: all data requested from dataset is entered in the modalBody
* Postcondition: returns to test editor with all of the questions added
*/
function addSelectedQuestions() {
const modalBody = document.getElementById("questionModalBody");
const courseID = modalBody.dataset.courseID;
const partNum = parseInt(modalBody.dataset.partNum);
const sectionNum = parseInt(modalBody.dataset.sectionNum);
const type = modalBody.dataset.questionType;

//find all of the checkbox type inputs in the questionModalBody element and selected by the user
const checkboxes = document.querySelectorAll('#questionModalBody input[type="checkbox"]:checked');
//returns an array of selected question IDs

if (checkboxes.length === 0) {
alert("Please select at least one question.");
return;
}

const selectedIDs = Array.from(checkboxes).map(cb => parseInt(cb.value));
const questions = {};
for (let i = 0; i < selectedIDs.length; i++) {
    const id = selectedIDs[i];
    const questionData = masterQuestionList[courseID]?.[type]?.[id];
    if (questionData) {
        questions[id] = questionData;
    } else {
        console.warn(`Question with ID ${id} not found for type ${type} in course ${courseID}`);
    }
}

// Update the test part on screen
const sectionContainer = document.getElementById(`part-${partNum}-section-${sectionNum}-container`);
const selectedQuestionsDiv = sectionContainer.querySelector('.selected-questions');
selectedQuestionsDiv.innerHTML = '';

// Create a section-wide point value input
const sectionPointsDiv = document.createElement("div");
sectionPointsDiv.innerHTML = `
<label>Set All Points for This Section: </label>
<input type="number" id="section-${partNum}-${sectionNum}-points" min="1" value="1" style="width: 60px;">
<button onclick="updateSectionPoints(${partNum}, ${sectionNum})">Apply</button>
<hr>
`;
selectedQuestionsDiv.appendChild(sectionPointsDiv);

for (const key in questions){
question = questions[key];
const questionElement = document.createElement("div");
questionElement.style.padding = "8px";
questionElement.style.margin = "5px 0";
questionElement.style.backgroundColor = "#f0f0f0";
questionElement.style.borderRadius = "4px";
questionElement.dataset.questionID = question.id; 

questionElement.innerHTML = `
    <p>${question.text}</p>
    <label>Points: </label>
    <input type="number" class="question-points" min="1" value="${question.score}" style="width: 60px;">
`;

selectedQuestionsDiv.appendChild(questionElement);
}

const randomizer = document.createElement("button");
randomizer.className = "add-btn";
randomizer.textContent = "Randomize Question Order";
randomizer.onclick = function() {
const questionElements = Array.from(selectedQuestionsDiv.children).slice(1); // Skip the first child
ShuffleArray(questionElements);
selectedQuestionsDiv.innerHTML = ''; 
selectedQuestionsDiv.appendChild(sectionPointsDiv);
questionElements.forEach((element, index) => {
    selectedQuestionsDiv.appendChild(element);
});
};
selectedQuestionsDiv.appendChild(randomizer);


closeQuestionModal();
}


function ShuffleArray(questionElements){
for (let i = questionElements.length - 2; i > 0; i--) {
const j = Math.floor(Math.random() * (i + 1));
[questionElements[i], questionElements[j]] = [questionElements[j], questionElements[i]];
}
}



/**
 * The bonus question modal is opened when the user wants to add bonus questions to a template or test
 * Precondition: valid courseID
 * Postcondition: bonus question modal is opened
*/
function openBonusQuestionModal(courseID) {
    const modal = document.getElementById("questionModal");
    const modalTitle = document.getElementById("questionModalTitle");
    const modalBody = document.getElementById("questionModalBody");

    modalBody.innerHTML = ""; // Clear existing content
    
    // Store the relevant data in the modal for later use
    modalBody.dataset.courseID = courseID;
    modalBody.dataset.questionType = 'bonus';

    const questionContainer = document.createElement('div');
    questionContainer.style.padding = '5px';
    questionContainer.style.marginBottom = '8px';
    questionContainer.style.borderBottom = '1px solid #ccc';

    Object.keys(masterQuestionList[courseID]).forEach(type => {
        const questions = masterQuestionList[courseID][type];
        for(const key in questions){
            let question = questions[key];
            const element = document.createElement("div");
            element.style.padding = '8px';
            element.style.margin = '5px 0';
            element.style.backgroundColor = '#f0f0f0';
            element.style.borderRadius = '4px';
            element.innerHTML = `
                <input type="checkbox" id="q-${type}-${question.id}" value="${type}-${question.id}">
                <label for="q-${type}-${question.id}">${question.text} (${question.score} Points)</label>
            `;   
            questionContainer.appendChild(element);
        }
    });

    const submitButton = document.createElement('button');
    submitButton.className = 'add-btn';
    submitButton.textContent = 'Add Selected Questions';
    submitButton.onclick = function() {
        addSelectedBonusQuestions(courseID);
    };
    questionContainer.appendChild(submitButton);

    modalTitle.innerText = `Select Bonus Questions`;
    modalBody.appendChild(questionContainer);

    modal.style.display = "flex";
    setTimeout(() => {
        modal.style.opacity = "1";
    }, 10);
}


/**
 * This function is called to add selected bonus questions to a template or test, depending on the bonus question modal being open
 * Precondition: valid courseID, bonus questions selected
 * Postcondition: bonus questions are added to the template or test
*/
function addSelectedBonusQuestions(courseID) {
    console.log("Starting addSelectedBonusQuestions function");
    
    const modalBody = document.getElementById("questionModalBody");
    if (!modalBody) {
        console.error("Question modal body not found!");
        alert("Error: Question modal body not found");
        return;
    }
    
    const checkboxes = modalBody.querySelectorAll('input[type="checkbox"]:checked');
    const selectedQuestions = Array.from(checkboxes).map(cb => cb.value);

    if (selectedQuestions.length === 0) {
        alert("Please select at least one question.");
        return;
    }

    console.log(`Selected ${selectedQuestions.length} questions for bonus`);
    
    // Save to master list
    masterTemplateList[courseID].bonusQuestions = [];
    
    // Create a container for the selected questions
    const selectedQuestionsDiv = document.createElement('div');
    selectedQuestionsDiv.className = "bonus-questions-container";

    // Add each question to the container
    selectedQuestions.forEach((q, questionIndex) => {
        const [type, id] = q.split('-');
        const question = masterQuestionList[courseID][type][id];
        console.log(`Processing question: ${question.text.substring(0, 20)}...`);
        masterTemplateList[courseID].bonusQuestions.push(id);
        const questionElement = document.createElement("div");
        questionElement.style.padding = "8px";
        questionElement.style.margin = "5px 0";
        questionElement.style.backgroundColor = "#f0f0f0";
        questionElement.style.borderRadius = "4px";
        questionElement.dataset.questionIndex = questionIndex; 
        questionElement.dataset.questionID = question.id; 

        questionElement.innerHTML = `
            <p>${question.text}</p>
            <p>Points: ${question.score}</p>
            `;
        selectedQuestionsDiv.appendChild(questionElement);
    });
    
    console.log("Created questions div, now looking for container");
    
    // APPROACH 1: Try to find the element directly
    let container = document.getElementById("selectedBonusQuestionsContainer");
    console.log("Direct lookup result:", container ? "Found" : "Not found");
    
    // APPROACH 2: Look in the template editor
    if (!container) {
        const templateEditor = document.getElementById("templateEditor");
        console.log("Template editor found:", templateEditor ? "Yes" : "No");
        
        if (templateEditor) {
            container = templateEditor.querySelector("#selectedBonusQuestionsContainer");
            console.log("Container in template editor:", container ? "Found" : "Not found");
        }
    }
    
    // APPROACH 3: Search the entire document
    if (!container) {
        console.log("Searching all divs in document...");
        const allDivs = document.querySelectorAll("div");
        console.log(`Found ${allDivs.length} divs in document`);
        
        for (let div of allDivs) {
            if (div.id === "selectedBonusQuestionsContainer") {
                container = div;
                console.log("Found container by searching all divs");
                break;
            }
        }
    }
    
    // APPROACH 4: Create the container if it doesn't exist
    if (!container) {
        console.log("Container not found, creating new one");
        
        // Find the bonus toggle to insert after
        const bonusToggle = document.querySelector("#bonusToggle");
        if (bonusToggle) {
            console.log("Found bonus toggle, adding container after it");
            
            container = document.createElement("div");
            container.id = "selectedBonusQuestionsContainer";
            container.style.marginTop = "10px";
            container.style.marginBottom = "10px";
            
            // Try to insert after the bonus toggle's parent
            const toggleParent = bonusToggle.closest("select, div");
            if (toggleParent && toggleParent.parentNode) {
                // Find the next <br> after the toggle
                let nextBr = toggleParent.nextSibling;
                while (nextBr && nextBr.nodeName !== "BR") {
                    nextBr = nextBr.nextSibling;
                }
                
                // Insert after the BR if found, otherwise after the toggle parent
                if (nextBr && nextBr.nextSibling) {
                    toggleParent.parentNode.insertBefore(container, nextBr.nextSibling);
                } else {
                    toggleParent.parentNode.insertBefore(container, toggleParent.nextSibling);
                }
                
                console.log("Container created and inserted");
            } else {
                console.log("Could not locate proper insertion point");
            }
        } else {
            console.log("Bonus toggle not found");
        }
    }
    
    // Final check and update
    if (container) {
        console.log("Found/created container, updating content");
        container.innerHTML = "";
        container.appendChild(selectedQuestionsDiv);
        console.log("Container updated successfully");
    } else {
        console.error("CRITICAL: Could not find or create container!");
        alert("Error: Could not display selected bonus questions. Please try refreshing the page.");
    }
    
    closeQuestionModal();
    console.log("Modal closed, function complete");
}


/**
 * This function determines whether or not bonus questions are available inside the template
 * Precondition: valid courseID
 * Postcondition: bonus questions are toggled on or off in the template editor
*/
function toggleBonusQuestionSelection(courseID) {
    const bonusToggle = document.getElementById('bonusToggle').value;
    const selectBonusQuestionsBtn = document.getElementById('selectBonusQuestionsBtn');
    if (bonusToggle === 'True') {
        selectBonusQuestionsBtn.style.display = 'block';
    } else {
        selectBonusQuestionsBtn.style.display = 'none';
    }
}



/**
 * This function is called to update the options inside of the question editor when first creating a question
 * Precondition: valid question type
 * Postcondition: options are updated in the question editor
*/
function updateOptions(type) {
    const optionsContainer = document.getElementById('optionsContainer');
    optionsContainer.innerHTML = '';

    if (type === 'ma') {
        const numPairs = parseInt(document.getElementById('numPairs').value);
        const numDistractions = parseInt(document.getElementById('numDistractions').value);
        for (let i = 1; i <= numPairs*2; i+=2) {
            pairNum = (i-1)/2 + 1;
            optionsContainer.innerHTML += `
                <label>Pair ${pairNum}:</label><br/>
                <input type="text" id="option${i}" placeholder="Option ${i}">
                <input type="text" id="option${i+1}" placeholder="Option ${i+1}"><br><br>
            `;
        }
        for (let i = 1; i <= numDistractions; i++) {
            optionsContainer.innerHTML += `
                <label>Distraction ${i}:</label><br/>
                <input type="text" id="distraction${i}" placeholder="Distraction ${i}"><br><br>
            `;
        }
    } else if (type === 'ms') {
        let numOptions = parseInt(document.getElementById('numOptions').value);
        if(numOptions > 20){
            numOptions = 20;
        }
        for (let i = 1; i <= numOptions; i++) {
            optionsContainer.innerHTML += `
                <label>Option ${i}:</label><br/>
                <input type="text" id="option${i}" placeholder="Option ${i}"><br>
                <label>Correct Answer:</label>
                <input type="checkbox" id="correct${i}"><br><br>
            `;
        }
    } else if (type === 'fb') {
        const numBlanks = parseInt(document.getElementById('numBlanks').value);
        for (let i = 1; i <= numBlanks; i++) {
            optionsContainer.innerHTML += `
                <label>Answer for Blank ${i}:</label><br/>
                <input type="text" id="blank${i}" placeholder="Answer for Blank ${i}"><br><br>
            `;
        }
    }
}


/**
 * This code is for the test editor. It updates the points for every question inside a section,
 * when the button is pressed for that section. This function grabs the section-X-Y-points value
 * where X is the part number and Y is the section number. This points to a numeric field that allows selection
 * of different point values per section. 
 * It takes the value from that selection and applies it to all of the elements whose IDs include question-points
 * Precondition: valid part and section number, test editor open and functional
 * Postcondition: All question point values in the section will be updated to the new value
*/
function updateSectionPoints(partNum, sectionNum) {
    const newPointValue = document.getElementById(`section-${partNum}-${sectionNum}-points`).value;

    if (!newPointValue || newPointValue < 1) {
        alert("Please enter a valid point value.");
        return;
    }

    // Select all question inputs in this section
    const sectionContainer = document.getElementById(`part-${partNum}-section-${sectionNum}-container`);
    const pointInputs = sectionContainer.querySelectorAll('.question-points');

    pointInputs.forEach(input => {
        input.value = newPointValue;
    });

    alert(`Updated all questions in Part ${partNum + 1}, Section ${sectionNum + 1} to ${newPointValue} points each.`);
}



function closeModal() {
    document.getElementById("editModal").style.display = "none";
    document.getElementById("editModal").style.opacity = "0";
}


function closeQuestionModal(){
    document.getElementById("questionModal").style.display = "none";
    document.getElementById("questionModal").style.opacity = "0";
}