//Can be used for session-level storage and testing
var masterQuestionList = {};
var masterTestList = {};
var masterTemplateList = {};
var masterAttachmentList = {};
var courseList = {};
var textbookList = {};
var masterCoverPageList = {};
var masterTextbookList = {};
var DBCourseList = {};
var DBTextbookList = {}; 

function populateExistingSelectors() {
    const existingCourse = document.getElementById("existingCourse");
    const courseTargets = document.getElementById("courseTargets");
    const existingTextbook = document.getElementById("existingTextbook");

    existingCourse.innerHTML = `<option value="" disabled selected>Choose a Course</option>`;
    courseTargets.innerHTML = `<option value="" disabled selected>Choose a Course for the Textbooks:</option>`;
    existingTextbook.innerHTML = ``; // clear first

    for (const [id, course_name] of Object.entries(DBCourseList)) {
        const option = `<option value="${id}">${course_name}</option>`;
        existingCourse.innerHTML += option;
        courseTargets.innerHTML += option;
    }

    for (const [id, isbn] of Object.entries(DBTextbookList)) {
        const option = `<option value="${id}">ISBN:${isbn}</option>`;
        existingTextbook.innerHTML += option;
    }
}


// Used AI for speed
function addExistingCourse() {
    const courseSelect = document.getElementById("existingCourse");
    const selectedCourseID = courseSelect.value;

    if (!selectedCourseID) {
        alert("Please select a course to add.");
        return;
    }

    requestData = {id: selectedCourseID};
    fetch('/api/join_course/', {
      method: 'POST',
       headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
        body: JSON.stringify(requestData)
   });

    reloadData();
}



function assignTextbooksToCourse() {
    const textbookSelect = document.getElementById("existingTextbook");
    const courseSelect = document.getElementById("courseTargets");

    const selectedTextbooks = Array.from(textbookSelect.selectedOptions).map(opt => opt.value);
    const selectedCourse = courseSelect.value;

    if (!selectedCourse) {
        alert("Please select a course to assign the textbooks to.");
        return;
    }

    if (selectedTextbooks.length === 0) {
        alert("Please select at least one textbook.");
        return;
    }

    requestData = {id: selectedCourse, textbook_ids:selectedTextbooks};
    fetch('/api/assign_books/', {
      method: 'POST',
       headers: {'Content-Type': 'application/json','X-CSRFToken': getCSRFToken()},
        body: JSON.stringify(requestData)
   });

    reloadData();

}



/**
 * getUserIdentity to determine identity based on user role
*/
function getUserIdentity(courseID, isbn) {
  const ownerRole = window.userRole;
  if (ownerRole === 'teacher' || ownerRole === 'webmaster') {
    return courseID;
  } else if (ownerRole === 'publisher') {
    return isbn;
  }
  // fallback to whichever is defined
  return courseID || isbn;
}




function updateQuestionTabs(questionType, identity) {
    const tabContent = document.getElementById(`${questionType}-${identity}`);
    tabContent.innerHTML = ''; // Clear existing content

    const questions = masterQuestionList[identity][questionType];
    
    if (!questions || Object.keys(questions).length === 0) {
        tabContent.innerHTML = `<p>No ${questionType.toUpperCase()} questions available...</p>`;
        return;
    }
    
    // Create filter container
    const filterContainer = document.createElement('div');
    filterContainer.className = 'filter-container';
    filterContainer.style.padding = '10px';
    filterContainer.style.marginBottom = '15px';
    filterContainer.style.backgroundColor = '#f5f5f5';
    filterContainer.style.borderRadius = '4px';
    
    // Test filter
    const testFilterLabel = document.createElement('label');
    testFilterLabel.textContent = 'Filter by Test: ';
    testFilterLabel.style.marginRight = '5px';
    
    const testFilterSelect = document.createElement('select');
    testFilterSelect.id = `${questionType}-${identity}-test-filter`;
    testFilterSelect.innerHTML = '<option value="" selected>All Tests</option>';
    
    const testList = {...masterTestList[identity]['drafts'], ...masterTestList[identity]['published']};
    for (const key in testList) {
        const test = testList[key];
        const option = document.createElement('option');
        option.value = test.id;
        option.textContent = test.name;
        testFilterSelect.appendChild(option);
    }
    
    // Chapter filter
    const chapterFilterLabel = document.createElement('label');
    chapterFilterLabel.textContent = 'Chapter: ';
    chapterFilterLabel.style.marginLeft = '15px';
    chapterFilterLabel.style.marginRight = '5px';
    
    const chapterFilterSelect = document.createElement('select');
    chapterFilterSelect.id = `${questionType}-${identity}-chapter-filter`;
    
    // Add "All Chapters" option
    const allChaptersOption = document.createElement('option');
    allChaptersOption.value = "all";
    allChaptersOption.textContent = "All Chapters";
    chapterFilterSelect.appendChild(allChaptersOption);
    
    // Get unique chapters
    const chapters = [...new Set(Object.values(questions).map(q => q.chapter))].sort((a, b) => a - b);
    chapters.forEach(chapter => {
        const option = document.createElement('option');
        option.value = chapter;
        option.textContent = `Chapter ${chapter}`;
        chapterFilterSelect.appendChild(option);
    });

        // ——— Author filter ————————————————
        const authorFilterLabel = document.createElement('label');
        authorFilterLabel.textContent = 'Author: ';
        authorFilterLabel.style.marginLeft = '15px';
        authorFilterLabel.style.marginRight = '5px';
    
        const authorFilterSelect = document.createElement('select');
        authorFilterSelect.id = `${questionType}-${identity}-author-filter`;
        authorFilterSelect.innerHTML = '<option value="" selected>All Authors</option>';
    
        // collect unique authors from this questionType
        const authors = [...new Set(Object.values(questions).map(q => q.author))];
        authors.sort().forEach(authorName => {
          const opt = document.createElement('option');
          opt.value = authorName;
          opt.textContent = authorName;
          authorFilterSelect.appendChild(opt);
        });
    
        filterContainer.appendChild(authorFilterLabel);
        filterContainer.appendChild(authorFilterSelect);
    
        // re-run filtering whenever the author changes
        authorFilterSelect.addEventListener('change', () => renderFilteredQuestions(questionType, identity));
        // ——————————————————————————————————————————
    
    
    // Section filter (initially hidden)
    const sectionFilterContainer = document.createElement('div');
    sectionFilterContainer.id = `${questionType}-${identity}-section-container`;
    sectionFilterContainer.style.display = 'none';
    sectionFilterContainer.style.marginTop = '10px';
    
    const sectionFilterLabel = document.createElement('label');
    sectionFilterLabel.textContent = 'Section: ';
    sectionFilterLabel.style.marginRight = '5px';
    
    const sectionFilterSelect = document.createElement('select');
    sectionFilterSelect.id = `${questionType}-${identity}-section-filter`;
    
    // Assemble filter components
    filterContainer.appendChild(testFilterLabel);
    filterContainer.appendChild(testFilterSelect);
    filterContainer.appendChild(chapterFilterLabel);
    filterContainer.appendChild(chapterFilterSelect);
    
    sectionFilterContainer.appendChild(sectionFilterLabel);
    sectionFilterContainer.appendChild(sectionFilterSelect);
    filterContainer.appendChild(sectionFilterContainer);
    
    // Add the filter container to the tab content
    tabContent.appendChild(filterContainer);
    
    // Create question container to hold the filtered questions
    const questionContainer = document.createElement('div');
    questionContainer.id = `${questionType}-${identity}-question-container`;
    tabContent.appendChild(questionContainer);
    
    // Initial render of all questions
    renderFilteredQuestions(questionType, identity);
    
    // Add event listeners for filters
    testFilterSelect.addEventListener('change', () => renderFilteredQuestions(questionType, identity));
    
    chapterFilterSelect.addEventListener('change', function() {
        const selectedChapter = this.value;
        const sectionContainer = document.getElementById(`${questionType}-${identity}-section-container`);
        const sectionSelect = document.getElementById(`${questionType}-${identity}-section-filter`);
        
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
                .filter(q => q.chapter == parseInt(selectedChapter))
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
        renderFilteredQuestions(questionType, identity);
    });
    
    // Section filter change event
    sectionFilterSelect.addEventListener('change', () => renderFilteredQuestions(questionType, identity));
}

function renderFilteredQuestions(questionType, identity) {
    const questions = masterQuestionList[identity][questionType];
    const questionContainer = document.getElementById(`${questionType}-${identity}-question-container`);
    questionContainer.innerHTML = '';
    
    // Get filter values
    const testFilterValue = document.getElementById(`${questionType}-${identity}-test-filter`).value;
    const chapterFilterValue = document.getElementById(`${questionType}-${identity}-chapter-filter`).value;
    const sectionFilterSelect = document.getElementById(`${questionType}-${identity}-section-filter`);
    const sectionFilterValue = sectionFilterSelect && sectionFilterSelect.style.display !== 'none' ? 
                               sectionFilterSelect.value : "all";
    const authorFilterElem    = document.getElementById(`${questionType}-${identity}-author-filter`);
    const authorFilterValue   = authorFilterElem ? authorFilterElem.value : "";
                           
    
    // Filter questions
    const filteredQuestions = {};
    
    for (const key in questions) {
        let includeQuestion = true;
        let question = questions[key];
        
        // Apply test filter if selected
        if (testFilterValue !== "") {
            const testID = parseInt(testFilterValue);
            let idMatch = false;
            for (let i = 0; i < question.tests.length; i++) {
                if (question.tests[i] == testID) {
                    idMatch = true;
                    break;
                }
            }
            if (!idMatch) {
                includeQuestion = false;
            }
        }
        
        // Apply chapter filter if selected
        if (chapterFilterValue !== "all" && question.chapter != parseInt(chapterFilterValue)) {
            includeQuestion = false;
        }
        
        // Apply section filter if visible and selected
        if (chapterFilterValue !== "all" && sectionFilterValue !== "all" && 
            question.section != parseInt(sectionFilterValue)) {
            includeQuestion = false;
        }
        
        if (authorFilterValue && question.author !== authorFilterValue) {
            includeQuestion = false;
          }

        if (includeQuestion) {
            filteredQuestions[key] = question;
        }
    }
    
    // Display filtered questions
    if (Object.keys(filteredQuestions).length === 0) {
        questionContainer.innerHTML = '<p>No questions match the selected filters.</p>';
    } else {
        for (const key in filteredQuestions) {
            let question = filteredQuestions[key];
            const questionDiv = document.createElement('div');
            questionDiv.style.backgroundColor = '#d0d0d0';
            questionDiv.style.padding = '5px';
            questionDiv.style.marginBottom = '8px';
            questionDiv.style.borderBottom = '1px solid #ccc';
            questionDiv.classList.add('context-menu-target');
            questionDiv.dataset.itemType = 'question';
            questionDiv.dataset.itemID = question.id;
            questionDiv.dataset.identity = identity;
            questionDiv.dataset.questionType = questionType;
            
            questionDiv.innerHTML = `
                <p><strong>${question.text}</strong></p>
                <p>Points: ${question.score}</p>
                <p>Estimated Time: ${question.eta} minutes</p>
                <p>Chapter: ${question.chapter}, Section: ${question.section}</p>
            `;
            
            questionContainer.appendChild(questionDiv);
        }
    }
}



async function addContent() {
    
    let courseID, courseName, courseCRN, courseSemester;
    let title, author, version, isbn, link;

    if (window.userRole === "teacher") {
        courseID = document.getElementById('courseID').value.trim();
        courseName = document.getElementById('courseName').value.trim();
        courseCRN = document.getElementById('courseCRN').value.trim();
        courseSemester = document.getElementById('courseSemester').value;

        if (!courseID || !courseName || !courseCRN || !courseSemester) {
            alert("All fields (Course ID, Name, CRN, Semester, and Textbook Title/Author/Version/ISBN/Link) are required.");
            return;
        }
    } else {
        title = document.getElementById('title').value.trim();
        author = document.getElementById('author').value.trim();
        version = document.getElementById('version').value.trim();
        isbn = document.getElementById('isbn').value.trim();
        link = document.getElementById('link').value.trim();
        courseID = courseName = courseCRN = courseSemester = null;
        if (!title || !author || !version || !isbn || !link) {
            alert("All fields (Title, Author, Version, ISBN, and Link) are required.");
            return;
        }
        if (textbookList[isbn]) {
            alert("Error: A testbook with that isbn already exists.");
            return;
        }
    }  

    
    const identity = getUserIdentity(courseID, isbn);

    let formdata = `
        <details>`
        if(window.userRole=='teacher'){
            formdata +=`<summary><strong>${courseName}</strong> (CourseID: ${identity}, CRN: ${courseCRN}, SEM: ${courseSemester})</summary>
            <details>`;
        }else{
            formdata +=`<summary><strong>${title}</strong> (ISBN: ${identity}, Version: ${version})</summary>
            <details>`;
        }
        formdata +=`
                <summary>Questions</summary>
            <button class="add-btn" onclick="openEditor('Question', '${identity}')">Add Question</button>
            <div class="tab-container">
                <div class="tabs">
                    <div class="tab active" onclick="switchTab(event, 'tf-${identity}')">True/False</div>
                    <div class="tab" onclick="switchTab(event, 'mc-${identity}')">Multiple Choice</div>
                    <div class="tab" onclick="switchTab(event, 'sa-${identity}')">Short Answer</div>
                    <div class="tab" onclick="switchTab(event, 'es-${identity}')">Essay</div>
                    <div class="tab" onclick="switchTab(event, 'ma-${identity}')">Matching</div>
                    <div class="tab" onclick="switchTab(event, 'ms-${identity}')">Multiple Selection</div>
                    <div class="tab" onclick="switchTab(event, 'fb-${identity}')">Fill in the Blank</div>
                </div>
                <div class="tab-content active" id="tf-${identity}"><p>True/False questions go here...</p></div>
                <div class="tab-content" id="es-${identity}"><p>Essay questions go here...</p></div>
                <div class="tab-content" id="mc-${identity}"><p>Multiple Choice questions go here...</p></div>
                <div class="tab-content" id="sa-${identity}"><p>Short Answer questions go here...</p></div>
                <div class="tab-content" id="ma-${identity}"><p>Matching questions go here...</p></div>
                <div class="tab-content" id="ms-${identity}"><p>Multiple Selection questions go here...</p></div>
                <div class="tab-content" id="fb-${identity}"><p>Fill in the Blank questions go here...</p></div>
            </div>
            </details>

            <details>
                <summary>Cover Pages</summary>
                    <button class="add-btn" onclick="openEditor('Cover Page', '${identity}')">Add Cover Page</button>
                    <div id="coverpages-${identity}"><p>You have not added any cover pages yet...</div>
            </details>

            <details>
                <summary>Templates</summary>
                    <button class="add-btn" onclick="openEditor('Template', '${identity}')">Add Template</button>
                    <div id="templates-${identity}"><p>You have not added any templates yet...</p></div>
            </details>

            <details>
                <summary>Tests</summary>
                <button class="add-btn" onclick="openEditor('Test', '${identity}')">Add Test</button>`;
                if(window.userRole=="teacher"){
                    formdata += `<button class="add-btn" onclick="openImporter('${identity}', '${courseName}', '${courseCRN}', '${courseSemester}')">Import Test</button>
                    <input type="file" id="fileInput-${identity}">`;
                }
                formdata += `
                <div class="tab-container">
                <div class="tabs">
                    <div class="tab active" onclick="switchTab(event, 'drafts-${identity}')">Drafts</div>
                    <div class="tab" onclick="switchTab(event, 'published-${identity}')">Published Tests</div>
                </div>
                <div class="tab-content active" id="drafts-${identity}"><p>Saved drafts go here...</p></div>
                <div class="tab-content" id="published-${identity}"><p>Published tests go here...</p></div>
            </div>
            </details>

            <details>
                <summary>Attachments</summary>
                <button class="add-btn" onclick="openEditor('Attachment', '${identity}')">Add Attachment</button>
                <div id="attachments-${identity}"><p>You have not uploaded any attachments yet...</p></div>
            </details>`;
            if(window.userRole=="teacher"){
                formdata += `<button class="remove-btn" onclick="confirmRemoveContent('${identity}')">Leave Course</button>`;
            }else{  
                formdata += `<button class="remove-btn" onclick="confirmRemoveContent('${identity}')">Delete Textbook</button>`;
            }
        formdata += `</details>`;

    if(window.userRole=="teacher"){
        document.getElementById('courseID').value = "";
        document.getElementById('courseName').value = "";
        document.getElementById('courseCRN').value = "";
        document.getElementById('courseSemester').value = "";
    }else{  
        document.getElementById('title').value = "";
        document.getElementById('author').value = "";
        document.getElementById('version').value = "";
        document.getElementById('isbn').value = "";
        document.getElementById('link').value = ""; 
    }
    

    let today = new Date();
    let year = today.getFullYear();
    let month = today.getMonth() + 1;
    let date = today.getDate();

    if(month<10){ //ensuring that the values are valid for HTML date YYYY-MM-DD
        month = '0' + month;
    }
    if(date<10){
        date = '0' + date;
    }   
    masterCoverPageList[identity] = {};
    masterTemplateList[identity] = {};
    masterTemplateList[identity].bonusQuestions = [];

    const templateDefault = {
        name: "System Default",
        titleFont: "Times New Roman",
        titleFontSize: 36,
        subtitleFont: "Times New Roman",
        subtitleFontSize: 24,
        bodyFont: "Times New Roman",
        bodyFontSize: 12,
        pageNumbersInFooter: true,
        pageNumbersInHeader: false,
        headerText: "",
        footerText: "Please read all questions carefully",
        coverPageID:8,
        coverPage: masterCoverPageList[identity][0],
        bonusSection: false,
        bonusQuestions: [],
        partStructure: [
            {
                partNumber: 1,
                sections: [
                    { sectionNumber: 1, questionType: "tf" }
                ]
            }
        ],
        published: 1
    };

    let thisCourse = {};
    let textbook = {};
    const contentContainer = document.createElement('div');
    contentContainer.classList.add('course-container');
    contentContainer.dataset.identity = identity;
    

   if(window.userRole=="teacher"){
        thisCourse = {
        course_id: courseID,
        name: courseName,
        crn: courseCRN,
        sem: courseSemester
        }; 
        contentContainer.classList.add('course-container');
   }else{
        textbook = {
        'title': title,
        'author': author,
        'version': version,
        'isbn': isbn,
        'link': link
        }
        contentContainer.classList.add('textbook-container');
   }

   contentContainer.dataset.courseID = courseID || null;
   contentContainer.dataset.isbn = isbn || null;
   contentContainer.innerHTML = formdata;

    try {
        if(window.userRole =="teacher"){
            await saveData("course", thisCourse, identity);
        }else{
            await saveData("textbook", textbook,{}, identity);
        }
    } catch (error) {
        console.error("Error saving course data:", error);
        alert("There was an error saving your content. Please try again.");
    }
} // RED TASK: UPDATE TO ADD OPTION FOR LOADING IN COURSES FROM SELECTOR, CHOOSE TEXTBOOK FROM SELECTOR


async function confirmRemoveContent(identity) {
    if (confirm("Are you sure you want to leave this course / delete this textbok?")) {
        try {
        let username = window.username;
        let itemToDelete={};
        let type = '';
        if(window.userRole == "teacher"){
            type = "Course";
            itemToDelete=courseList[identity];
        }else{
            type = "Textbook";
            itemToDelete=textbookList[identity];
        }
        
        const response = await fetch('/api/delete_item/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                model_type: type,
                id: itemToDelete.id,
                username: username,
                identity: identity
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(data.message || `${type} successfully deleted.`);
            if(document.getElementById("courseList")){
                document.getElementById("courseList").innerHTML='';
            }else if(document.getElementById("textbookList")){
                document.getElementById("textbookList").innerHTML='';
            }
            
            reloadData();
            
        } else {
            reloadData();
            alert(data.message || 'An error occurred while deleting the item.');
        }
    } catch (error) {
        reloadData();
        console.error('Error:', error);
        alert('An error occurred while connecting to the server.');
    }
        
    }
}



function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) { // if you find the cookie that starts with csrftoken=
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;

}

async function reloadData() {
        console.log('reloadData:', typeof reloadData);
        const searchType = "UN";
        const searchValue = window.username;
        
        const requestData = {
            type: searchType,
            value: searchValue
        };

        try {
            const response = await fetch('/api/fetch_user_data/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(requestData)
            });
            const data = await response.json();

            if (response.ok) {
                console.log(data);
                renderUserData(data);
            } else {
                document.getElementById('errorText').innerText = data.message || 'An error occurred. Are you sure you have content to load?';
            }
        } catch (error) {
            console.error('Error:', error);
            document.getElementById('errorText').innerText = 'An error occurred while fetching data.';
        }
}

async function saveData(type, entry, courseID = null, isbn = null) {
    if (!entry) {
        showErrorMessage("Invalid data: Entry is null or undefined");
        return Promise.reject(new Error("Invalid data"));
    }

   

    let api_call = "";
    let requestData = {};
    let headers = {
        'X-CSRFToken': getCSRFToken()
    };
    const identity = getUserIdentity(courseID, isbn);
    
    const ownerRole = window.userRole;
    
    try {
        // Determine which API endpoint to use and prepare the data
        switch(type) {
            case "course":
                api_call = "/api/save_course/";
                requestData = serializeCourse(entry);
                headers['Content-Type'] = 'application/json';
                break;
            case "textbook":
                api_call = "/api/save_textbook/";
                requestData = serializeTextbook(entry);
                headers['Content-Type'] = 'application/json';
                break;
            case "question":
                api_call = "/api/save_question/";
                requestData = serializeQuestion(entry, identity);
                headers['Content-Type'] = 'application/json';
                break;
                
            case "template":
                api_call = "/api/save_template/";
                requestData = serializeTemplate(entry, identity);
                headers['Content-Type'] = 'application/json';
                break;
                
            case "coverPage":
                api_call = "/api/save_cpage/";
                requestData = serializeCoverPage(entry, identity);
                headers['Content-Type'] = 'application/json';
                break;
                
            case "test":
                api_call = "/api/save_test/";
                requestData = serializeTest(entry, identity);
                headers['Content-Type'] = 'application/json';
                break;
                
            case "attachment":
                api_call = "/api/save_attachment/";
                const formData = new FormData();
                formData.append('attachment_name', entry.name || 'Unnamed Attachment');
                
                
                if (entry.file instanceof File || entry.file instanceof Blob) {
                    formData.append('attachment_file', entry.file);
                } else {
                    showErrorMessage("Missing or invalid file for attachment");
                    return Promise.reject(new Error("Missing or invalid file"));
                }
                
                if (entry.url) formData.append('attachment_url', entry.url);
                if (courseID) formData.append('courseID', courseID);
                if (isbn) formData.append('isbn', isbn);
                formData.append('ownerRole', ownerRole);
                return sendFormData(api_call, formData);
                
            default:
                throw new Error(`Invalid type to save: ${type}`);
        }

        
        if (!api_call) {
            throw new Error("API endpoint not specified");
        }

        const response = await fetch(api_call, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(requestData)
        });
        
        
        let data;
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
            data = await response.json();
        } else {
            const text = await response.text();
            try {
                data = JSON.parse(text);
            } catch (e) {
                data = { message: text || "Unknown server response" };
            }
        }
        
        if (!response.ok) {
            throw new Error(data.message || data.error || `Server returned ${response.status}: ${response.statusText}`);
        }
        
        showSuccessMessage(`Saved ${type} successfully!`);
        reloadData();
        return data;
    } catch (error) {
        console.error('Error:', error);
        showErrorMessage(error.message || 'An error occurred while saving your data');
        throw error;
    }
}


async function sendFormData(url, formData) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || data.error || 'An error occurred while saving your data');
        }
        
        reloadData();
        return data;
    } catch (error) {
        console.error('Error:', error);
        showErrorMessage(error.message || 'An error occurred while saving your data');
        throw error;
    }
}


function showSuccessMessage(message) {
    const messageElement = document.getElementById('successMessage') || 
                          document.getElementById('statusMessage');
    if (messageElement) {
        messageElement.innerText = message;
        messageElement.style.display = 'block';
        setTimeout(() => {
            messageElement.style.display = 'none';
        }, 3000);
    } 
}


function showErrorMessage(message) {
    const errorElement = document.getElementById('errorText') || 
                        document.getElementById('errorMessage');
    if (errorElement) {
        errorElement.innerText = message;
        errorElement.style.display = 'block';
    } else {
        alert(`Error: ${message}`);
    }
}

/**
 * Serialize a course object for the API
 */
function serializeCourse(course) {
    const ownerRole = "teacher";
    
    // Build the request data
    const requestData = {
        ownerRole: ownerRole,
        course: {
            id: course.dbid || null,
            course_id: course.course_id || '',
            name: course.name || 'Untitled Course',
            crn: course.crn || '',
            sem: course.sem || '',
            published: course.published || false
        }
    };
    
    

    return requestData;
}

function serializeTextbook(textbook){
    // Build the request data
    const requestData = {
        ownerRole: "publisher",
        textbook: {
            id: textbook.id || null,
            title: textbook.title || 'Unknown Title',
            author: textbook.author || 'Unknown Author',
            version: textbook.version || 'Unknown Version',
            isbn: textbook.isbn || '',
            link: textbook.link || '',
            published: textbook.published || false
        }
    };
    
    return requestData;
} // update the published value of all related things on the backend when a test is published

/**
 * Serialize a template object for the API
 */
function serializeTemplate(template, identity) {
    const ownerRole = window.userRole;
    // Build the request data
    const requestData = {
        ownerRole: ownerRole,
        courseID: Boolean(ownerRole=="teacher") ? identity : null,
        isbn: Boolean(ownerRole=="teacher") ? null : identity,
        template: {
            id: template.id || null,
            name: template.name || 'Untitled Template',
            titleFont: template.titleFont || 'Arial',
            titleFontSize: parseInt(template.titleFontSize) || 48,
            subtitleFont: template.subtitleFont || 'Arial',
            subtitleFontSize: parseInt(template.subtitleFontSize) || 24,
            bodyFont: template.bodyFont || 'Arial',
            bodyFontSize: parseInt(template.bodyFontSize) || 12,
            pageNumbersInHeader: template.pageNumbersInHeader || false,
            pageNumbersInFooter: template.pageNumbersInFooter || false,
            headerText: template.headerText || '',
            footerText: template.footerText || '',
            nameTag: template.nameTag || '',
            dateTag: template.dateTag || '',
            courseTag: template.courseTag || '',
            coverPageID: template.coverPageID || 0,
            partStructure: template.partStructure || null,
            bonusSection: template.bonusSection || false,
            bonusQuestions: template.bonusQuestions || [],
            published: template.published || false
        }
    };

    return requestData;
}

/**
 * Serialize a cover page object for the API
 */
function serializeCoverPage(coverPage, identity) {
    const ownerRole = window.userRole;
    
    // Build the request data
    const requestData = {
        ownerRole: ownerRole,
        courseID: Boolean(ownerRole=="teacher") ? identity : null,
        isbn: Boolean(ownerRole=="teacher") ? null : identity,
        coverPage: {
            id: coverPage.id || null,
            name: coverPage.name || 'Untitled Cover Page',
            testNum: coverPage.testNum || '',
            date: coverPage.date || null,
            file: coverPage.file || '',
            showFilename: coverPage.showFilename || false,
            blank: coverPage.blank || 'TL',
            instructions: coverPage.instructions || null,
            published: Boolean(coverPage.published) || false
        }
    };
    
    return requestData;
}


/**
 * Serialize a question object for the API
 * Fixed to handle null values and improve data validation
 */
function serializeQuestion(question, identity) {
    const ownerRole = window.userRole;
    console.log(identity);
    // Build the base request data
    const requestData = {
        ownerRole: ownerRole,
        courseID: Boolean(ownerRole=="teacher") ? identity : null,
        isbn: Boolean(ownerRole=="teacher") ? null : identity,
    };
    
    // Format the question data with proper type checking
    requestData.question = {
        id: question.id || null,
        qtype: question.qtype || 'mc',
        text: question.text || '',
        eta: parseInt(question.eta) || 1, 
        directions: question.directions || null,
        reference: question.reference || null,
        requiredRefs: question.reqRefs || null,
        comments: question.comments || null,
        score: parseFloat(question.score) || 1.0, 
        chapter: parseInt(question.chapter) || 0, 
        section: parseInt(question.section) || 0, 
        published: Boolean(question.published), 
        img: question.img || null,
        ansimg: question.ansimg || null
    };
    
    // Format answers
    requestData.answer = {};
    switch(question.qtype){
        case "tf": 
            requestData.answer = {
                value: question.answer.value || null
            };
            break;
        case "ma":
            requestData.answer = {};
            if (question.answer) {
                Object.keys(question.answer).forEach(key => {
                    requestData.answer[key] = {
                        text: question.answer[key].text || null
                    };
                });
            }
            break;
        case "ms":
            requestData.answer = {};
            if (question.answer) {
                Object.keys(question.answer).forEach(key => {
                    requestData.answer[key] = {
                        value: question.answer[key].value || null
                    };
                });
            }
            break;
        case "mc":
            requestData.answer = {
                value: question.answer.value || null
            };
            break;
        case "fb":
            requestData.answer = {};
            if (question.answer) {
                Object.keys(question.answer).forEach(key => {
                    requestData.answer[key] = {
                        value: question.answer[key].value || null
                    };
                });
            }
            break;
        case "es":
            requestData.answer = {
                value: question.answer.value || null
            };
            break;
        case "sa":
            requestData.answer = {
                value: question.answer.value || null
            };
            break;
    }
    
    // Format options
    requestData.options = {};
    switch(question.qtype){
        case "tf": 
            requestData.options = {
                true: {text: "True", order: 1},
                false: {text: "False", order: 2}
            };
            break;
        case "ma":
            requestData.options = {};
            if (question.options) {
                Object.keys(question.options).forEach(key => {
                    if (key === "numPairs" || key === "numDistractions") {
                        requestData.options[key] = question.options[key];
                    } else if (key.startsWith("pair")) {
                        requestData.options[key] = {
                            left: question.options[key].left || null,
                            right: question.options[key].right || null,
                            pairNum: question.options[key].pairNum || null
                        };
                    } else if (key.startsWith("distraction")) {
                        requestData.options[key] = {
                            text: question.options[key].text || null,
                            order: question.options[key].order || null
                        };
                    }
                });
            }
            break;
        case "ms":
            requestData.options = {};
            if (question.options) {
                Object.keys(question.options).forEach(key => {
                    if (key.startsWith("option")) {
                        requestData.options[key] = {
                            text: question.options[key].text || null,
                            order: question.options[key].order || null
                        };
                    }
                });
            }
            break;
        case "mc":
            requestData.options = {};
            const mcOptions = ['A', 'B', 'C', 'D'];
            if (question.options) {
                mcOptions.forEach(letter => {
                    if (question.options[letter]) {
                        requestData.options[letter] = {
                            text: question.options[letter].text || null,
                            order: question.options[letter].order || mcOptions.indexOf(letter) + 1
                        };
                    }
                });
            }
            break;
        case "fb":
            // Fill in the blank typically doesn't have options
            requestData.options = {};
            break;
        case "es":
            // Essay questions typically don't have options
            requestData.options = {};
            break;
        case "sa":
            // Short answer questions typically don't have options
            requestData.options = {};
            break;
    }
    
    // Format feedback if available
    if (Array.isArray(question.feedback) && question.feedback.length > 0) {
        requestData.feedback = question.feedback
            .filter(fb => fb) // FIX: Filter out null/undefined values
            .map(fb => ({
                id: fb.id || null,
                username: fb.username || null,
                rating: fb.rating || null,
                averageScore: fb.averageScore || null,
                comments: fb.comments || null,
                time: fb.time || null,
                responses: Array.isArray(fb.responses) ? fb.responses
                    .filter(resp => resp) 
                    .map(resp => ({
                        id: resp.id || null,
                        username: resp.username || null,
                        text: resp.text || null,
                        date: resp.date || null
                    })) : []
            }));
    }
    console.log("Serialized requestData:", requestData);
    return requestData;
}

/**
 * Serialize a test object for the API
 * Fixed to handle null values and improve data transformation
 */
 function serializeTest(test, identity) {
    const ownerRole = window.userRole;

    // Build the base request data
    const requestData = {
        ownerRole: ownerRole,
        courseID: Boolean(ownerRole=="teacher") ? identity : null,
        isbn: Boolean(ownerRole=="teacher") ? null : identity,
    };
    
    let template = masterTemplateList[identity][test.templateID];
    let coverPage = masterCoverPageList[identity][template.coverPageID];
    console.log(JSON.stringify(coverPage));
    requestData.test = {
        id: test.id || null,
        name: test.name || 'Untitled Test',
        date: test.date || null,
        refText: test.refText || null,
        filename: coverPage.file || null,
        is_final: Boolean(test.published), 
        attachments: test.attachments || null,
        templateID: parseInt(test.templateID) || 0
    };
    
     // Format parts, sections, and questions
    requestData.parts = [];
    if (Array.isArray(test.parts) && test.parts.length > 0) {
        requestData.parts = test.parts.map((part, partIndex) => {
            const serializedPart = {
                part_number: part.part_number || part.partNumber || (partIndex + 1),
                sections: []
            };
            
            if (Array.isArray(part.sections) && part.sections.length > 0) {
                serializedPart.sections = part.sections.map((section, sectionIndex) => {
                    const serializedSection = {
                        section_number: section.section_number || section.sectionNumber || (sectionIndex + 1),
                        question_type: section.question_type || section.questionType || 'unknown',
                        questions: []
                    };
                    
                    for(let i=0; i<section.questions.length;i++){
                        let question = {
                            "id": section.questions[i].id,
                            "assigned_points":section.questions[i].assigned_points,
                            "order": i
                        };
                        serializedSection.questions.push(question);
                    }
                    return serializedSection;
                });
            }
            
            return serializedPart;
        });

        if (Array.isArray(test.feedback) && test.feedback.length > 0) {
            requestData.feedback = test.feedback
                .filter(fb => fb) 
                .map(fb => ({
                    id: fb.id || null,
                    username: fb.username || null,
                    rating: fb.rating || null,
                    averageScore: fb.averageScore || null,
                    comments: fb.comments || null,
                    time: fb.time || null,
                    responses: Array.isArray(fb.responses) ? fb.responses
                        .filter(resp => resp) 
                        .map(resp => ({
                            id: resp.id || null,
                            username: resp.username || null,
                            text: resp.text || null,
                            date: resp.date || null
                        })) : []
                }));
        }
    }
    
    console.log(JSON.stringify(requestData));
    return requestData;
}




function renderUserData(data){
        masterQuestionList = data.question_list;
        masterAttachmentList = data.attachment_list;
        masterTemplateList = data.template_list;
        masterTestList = data.test_list;
        console.log(window.userRole);
        DBCourseList = data.course_list;
        DBTextbookList = data.textbook_list;
        if(window.userRole == "teacher"){
            courseList = data.container_list;
        }else{
            textbookList = data.container_list;
        }
        
        masterCoverPageList = data.cpage_list;
        refreshData();
        if(window.userRole == "teacher"){
            populateExistingSelectors();
        }
        
}

function refreshData(){
    if(window.userRole == "teacher"){
        const courseContainer = document.getElementById("courseList");
        courseContainer.innerHTML = "";
        for(const [key,value] of Object.entries(courseList)){
            loadContent(key);
        }
    }else{
        const textbookContainer = document.getElementById("textbookList");
        textbookContainer.innerHTML = "";
        for(const [key,value] of Object.entries(textbookList)){
            loadContent(key);
        }
    }
}

function loadContent(identity) {
    
    let courseID, courseName, courseCRN, courseSemester;
    let title, version, isbn

    if (window.userRole === "teacher") {
        let course = courseList[identity];
        courseID = course.courseID;
        courseName = course.name;
        courseCRN = course.crn;
        courseSemester = course.sem;
    } else {
        let textbook = textbookList[identity]
        title = textbook.title;
        version = textbook.version;
        isbn = textbook.isbn;
        courseID = courseName = courseCRN = courseSemester = null;
    }  

    let formdata = `
        <details>`
        if(window.userRole=='teacher'){
            formdata +=`<summary><strong>${courseName}</strong> (CourseID: ${identity}, CRN: ${courseCRN}, SEM: ${courseSemester})</summary>
            <details>`;
        }else{
            formdata +=`<summary><strong>${title}</strong> (ISBN: ${identity}, Version: ${version})</summary>
            <details>`;
        }
        formdata +=`
                <summary>Questions</summary>
            <button class="add-btn" onclick="openEditor('Question', '${identity}')">Add Question</button>
            <div class="tab-container">
                <div class="tabs">
                    <div class="tab active" onclick="switchTab(event, 'tf-${identity}')">True/False</div>
                    <div class="tab" onclick="switchTab(event, 'mc-${identity}')">Multiple Choice</div>
                    <div class="tab" onclick="switchTab(event, 'sa-${identity}')">Short Answer</div>
                    <div class="tab" onclick="switchTab(event, 'es-${identity}')">Essay</div>
                    <div class="tab" onclick="switchTab(event, 'ma-${identity}')">Matching</div>
                    <div class="tab" onclick="switchTab(event, 'ms-${identity}')">Multiple Selection</div>
                    <div class="tab" onclick="switchTab(event, 'fb-${identity}')">Fill in the Blank</div>
                </div>
                <div class="tab-content active" id="tf-${identity}"><p>True/False questions go here...</p></div>
                <div class="tab-content" id="es-${identity}"><p>Essay questions go here...</p></div>
                <div class="tab-content" id="mc-${identity}"><p>Multiple Choice questions go here...</p></div>
                <div class="tab-content" id="sa-${identity}"><p>Short Answer questions go here...</p></div>
                <div class="tab-content" id="ma-${identity}"><p>Matching questions go here...</p></div>
                <div class="tab-content" id="ms-${identity}"><p>Multiple Selection questions go here...</p></div>
                <div class="tab-content" id="fb-${identity}"><p>Fill in the Blank questions go here...</p></div>
            </div>
            </details>

            <details>
                <summary>Cover Pages</summary>
                    <button class="add-btn" onclick="openEditor('Cover Page', '${identity}')">Add Cover Page</button>
                    <div id="coverpages-${identity}"><p>You have not added any cover pages yet...</div>
            </details>

            <details>
                <summary>Templates</summary>
                    <button class="add-btn" onclick="openEditor('Template', '${identity}')">Add Template</button>
                    <div id="templates-${identity}"><p>You have not added any templates yet...</p></div>
            </details>

            <details>
                <summary>Tests</summary>
                <button class="add-btn" onclick="openEditor('Test', '${identity}')">Add Test</button>`;
                if(window.userRole=="teacher"){
                    formdata += `<button class="add-btn" onclick="openImporter('${identity}', '${courseName}', '${courseCRN}', '${courseSemester}')">Import Test</button>
                    <input type="file" id="fileInput-${identity}">`;
                }
                formdata += `
                <div class="tab-container">
                <div class="tabs">
                    <div class="tab active" onclick="switchTab(event, 'drafts-${identity}')">Drafts</div>
                    <div class="tab" onclick="switchTab(event, 'published-${identity}')">Published Tests</div>
                </div>
                <div class="tab-content active" id="drafts-${identity}"><p>Saved drafts go here...</p></div>
                <div class="tab-content" id="published-${identity}"><p>Published tests go here...</p></div>
            </div>
            </details>

            <details>
                <summary>Attachments</summary>
                <button class="add-btn" onclick="openEditor('Attachment', '${identity}')">Add Attachment</button>
                <div id="attachments-${identity}"><p>You have not uploaded any attachments yet...</p></div>
            </details>`;
            if(window.userRole=="teacher"){
                formdata += `<button class="remove-btn" onclick="confirmRemoveContent('${identity}')">Leave Course</button>`;
            }else{  
                formdata += `<button class="remove-btn" onclick="confirmRemoveContent('${identity}')">Delete Textbook</button>`;
            }
        formdata += `</details>`;

    if(window.userRole=="teacher"){
        document.getElementById('courseID').value = "";
        document.getElementById('courseName').value = "";
        document.getElementById('courseCRN').value = "";
        document.getElementById('courseSemester').value = "";
    }else{  
        document.getElementById('title').value = "";
        document.getElementById('author').value = "";
        document.getElementById('version').value = "";
        document.getElementById('isbn').value = "";
        document.getElementById('link').value = "";
    }

    masterTemplateList[identity].bonusQuestions = [];

    const contentContainer = document.createElement('div');
    contentContainer.dataset.identity = identity;
    
   contentContainer.dataset.courseID = courseID || null;
   contentContainer.dataset.isbn = isbn || null;
   contentContainer.innerHTML = formdata;

   if(window.userRole=="teacher"){
        contentContainer.classList.add('course-container');
        document.getElementById("courseList").appendChild(contentContainer);
   }else{
        contentContainer.classList.add('textbook-container');
        document.getElementById("textbookList").appendChild(contentContainer);
   }


    updateCoverPages(identity);
    updateTemplates(identity);
    ['tf', 'ma', 'es', 'sa', 'ms', 'fb', 'mc'].forEach(type => updateQuestionTabs(type, identity));
    updateTestTabs(identity);
    updateAttachments(identity);
}

function questionTypeLabel(type) {
    switch (type) {
        case 'tf': return 'True/False';
        case 'mc': return 'Multiple Choice';
        case 'sa': return 'Short Answer';
        case 'es': return 'Essay';
        case 'ma': return 'Matching';
        case 'ms': return 'Multiple Selection';
        case 'fb': return 'Fill in the Blank';
        default: return type;
    }
}


function openImporter(id, name, crn, semester) {
    let fileInput = document.getElementById(`fileInput-${id}`);
    let file = fileInput.files[0];

    if (!file) {
        alert("Please select a file!");
        return;
    }

    let formData = new FormData();
    formData.append("file", file);
    formData.append("courseID", id);
    formData.append("courseName", name);
    formData.append("courseCRN", crn);
    formData.append("courseSemester", semester);

    //let templateId = "1";
    //formData.append("templateId", templateId);

    fetch(window.quizpressSettings.parseQTIUrl, {
        method: "POST",
        body: formData,
        headers: {
            "X-CSRFToken": window.quizpressSettings.csrfToken
        }
    })
        .then(response => response.json())
        .then(data => {
            console.log("Imported questions:", data);
            if (data.success) {
                alert(data.success);
                reloadData();
            } else {
                alert("Error: " + data.error);
            }

        })
        .catch(error => console.error("Error:", error));
}


function updateTestTabs(identity) {
    const draftsContainer = document.getElementById(`drafts-${identity}`);
    const publishedContainer = document.getElementById(`published-${identity}`);
    draftsContainer.innerHTML = ''; 
    publishedContainer.innerHTML = ''; 

    if(!masterTestList[identity]){
        masterTestList[identity] = {};
    }
    if(!masterTestList[identity].drafts){
        masterTestList[identity].drafts = {};
    }
    if(!masterTestList[identity].published){
        masterTestList[identity].published = {};
    }
    const drafts = masterTestList[identity].drafts;
    const published = masterTestList[identity].published;

    if (Object.keys(drafts).length === 0) {
        draftsContainer.innerHTML = '<p>No drafts available...</p>';
    } else {
        for(const key in drafts){
            let test = drafts[key];
            const testDiv = document.createElement('div');
            testDiv.style.backgroundColor = '#d0d0d0';
            testDiv.style.padding = '5px';
            testDiv.style.marginBottom = '8px';
            testDiv.style.borderBottom = '1px solid #ccc';
            testDiv.classList.add('context-menu-target');
            testDiv.dataset.itemType = 'test';
            testDiv.dataset.itemID = test.id;
            testDiv.dataset.identity = identity;
            testDiv.dataset.testType = 'drafts';

            testDiv.innerHTML = `
                <p><strong>${test.name}</strong></p>
                <p>Template: ${test.templateName}</p>
                <p>Parts: ${test.parts.length}</p>
            `;

            draftsContainer.appendChild(testDiv);
        }
    }

    if (Object.keys(published).length === 0) {
        publishedContainer.innerHTML = '<p>No published tests available...</p>';
    } else {
        for(const key in published){
            let test = published[key];
            const testDiv = document.createElement('div');
            testDiv.style.backgroundColor = '#d0d0d0';
            testDiv.style.padding = '5px';
            testDiv.style.marginBottom = '8px';
            testDiv.style.borderBottom = '1px solid #ccc';
            testDiv.classList.add('context-menu-target');
            testDiv.dataset.itemType = 'test';
            testDiv.dataset.itemID = test.id;
            testDiv.dataset.identity = identity;
            testDiv.dataset.testType = 'published';

            testDiv.innerHTML = `
                <p><strong>${test.name}</strong></p>
                <p>Template: ${test.templateName}</p>
                <p>Parts: ${test.parts.length}</p>
                <button class="add-btn" onclick="exportTestToHTML('${identity}', '${test.id}')">Export Test</button>
                <button class="add-btn" onclick="exportTestKeyToHTML('${identity}', '${test.id}')">Export Test Key</button>
            `;

            publishedContainer.appendChild(testDiv);
        }
    }
}

/**
 * exportTestToHTML
 * Exports the test with inline images (questions, answers, and reference materials),
 * inlines all images as Data URIs, and prints question‐level references and test‐wide
 * reference materials exactly as exportTestKeyToHTML does.
 */
async function exportTestToHTML(identity, testID) {
    // 1) grab the published test
    const published = masterTestList[identity].published;
    if (!published || !published[testID]) {
      alert("Test not found!");
      return;
    }
    const test = published[testID];
  
    // 2) grab the template and cover page
    const template = masterTemplateList[identity][test.templateID];
    if (!template) {
      alert("Invalid template!");
      return;
    }
    const cp = masterCoverPageList[identity][template.coverPageID];
    if (!cp) {
      alert("Invalid cover page!");
      return;
    }
  
    // 3) collect all image URLs (question images, answer images, test attachments)
    const urls = [];
    test.parts.forEach(part =>
      part.sections.forEach(section =>
        section.questions.forEach(qRef => {
          const Q = masterQuestionList[identity][qRef.qtype][qRef.id];
          if (Q.img)    urls.push(masterAttachmentList[identity][Q.img].url);
          if (Q.ansimg) urls.push(masterAttachmentList[identity][Q.ansimg].url);
        })
      )
    );
    if (Array.isArray(test.attachments)) {
      test.attachments.forEach(attID => {
        const att = masterAttachmentList[identity][attID];
        if (att && att.url) urls.push(att.url);
      });
    }
  
    // 4) dedupe and fetch into Data URIs
    const uniqueUrls = Array.from(new Set(urls));
    const urlToDataURI = {};
    await Promise.all(uniqueUrls.map(url =>
      fetch(url)
        .then(r => r.blob())
        .then(blob => new Promise(resolve => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result);
          reader.readAsDataURL(blob);
        }))
        .then(dataUri => { urlToDataURI[url] = dataUri; })
        .catch(() => {/* ignore missing */})
    ));
  
    // 5) start building HTML
    let html = `
  <!DOCTYPE html>
  <html>
  <head>
    <meta charset="UTF-8">
    <title>${test.name} – Test</title>
    <style>
      body { font-family: ${template.bodyFont}, sans-serif; font-size: ${template.bodyFontSize}px; margin:20px; }
      .test-title { font-family: ${template.titleFont}, sans-serif; font-size: ${template.titleFontSize}px; text-align:center; margin-bottom:20px; }
      .cover-page { border:1px solid #ccc; padding:15px; margin-bottom:20px; }
      .page-break { page-break-before: always; }
  
      /* flatten imported wrapper DIVs */
      .question > div:not(.question-img):not(.answer-space):not(.answer-img) { display: contents; margin:0; padding:0; }
      .question > div p { display:inline; margin:0; padding:0; }
  
      .q-num { font-weight:bold; margin-right:0.5em; }
  
      /* image styling */
      .question-img img,
      .answer-img img,
      .attachment-image img {
        display:block;
        border:1px solid #ccc;
        padding:4px;
        max-width:100%;
        margin:1em 0;
      }
  
      /* reference text styling */
      .question-ref-text { font-style:italic; margin-bottom:0.5em; }
      .question-req-refs { font-weight:bold; margin-bottom:0.5em; }
  
      /* test-wide references */
      .test-reference-materials { margin-top:2em; }
      .test-reference-materials h2 { font-size:1.5em; margin-bottom:0.5em; }
      .ref-text, .attachment-text { margin-bottom:1em; }
  
      .part { margin-bottom:30px; }
      .part-title { font-size:20px; margin-top:20px; }
      .section-title { font-size:18px; margin-top:15px; }
      .question { margin-bottom:15px; }
      .answer-space { border-bottom:1px solid #000; margin-top:5px; }
      ul { list-style-type:none; padding-left:0; }
    </style>
  </head>
  <body>
    ${template.headerText ? `<div>${template.headerText}</div>` : ""}
    <h1 class="test-title">${test.name}</h1>
  
    <!-- COVER PAGE -->
    <div class="cover-page">
      <h2>${cp.name}</h2>
      <p>Test Number: ${cp.testNum}</p>
      <p>Date:        ${cp.date}</p>
      <p>Filename:    ${cp.file}</p>
      <p>Instructions:${cp.instructions}</p>
    </div>
    <div class="page-break"></div>
  `;
  const typeMap = {
    tf: "True/False",
    mc: "Multiple Choice",
    ms: "Multiple Selection",
    ma: "Matching",
    es: "Essay",
    sa: "Short Answer",
    fb: "Fill in the Blank"
};
    // 6) render questions with references/images
    let questionNumber = 1;
    for (let p = 0; p < test.parts.length; p++) {
      html += `<div class="part"><h2 class="part-title">Part ${p+1}</h2>`;
      const part = test.parts[p];
  
      for (let s = 0; s < part.sections.length; s++) {
        const section = part.sections[s];
        let typeCode = section.questionType.toLowerCase();
        let type = typeMap[typeCode] || "Unknown Type";
        html += `<div><h3 class="section-title">${type}</h3>`;
  
        for (let q = 0; q < section.questions.length; q++) {
          const { id: Qid, qtype } = section.questions[q];
          const Q = masterQuestionList[identity][qtype][Qid];
  
          html += `<div class="question">`;
  
          // question-level reference text
          if (Q.reference)   html += `<div class="question-ref-text">${Q.reference}</div>`;
          if (Q.requiredRefs) html += `<div class="question-req-refs">${Q.requiredRefs}</div>`;
  
          // question-level image
          if (Q.img) {
            const src = masterAttachmentList[identity][Q.img].url;
            const du  = urlToDataURI[src];
            if (du) html += `<div class="question-img"><img src="${du}" alt="" /></div>`;
          }
  
          // number + text
          html += `<span class="q-num">${questionNumber++}.</span>${Q.text}`;
  
          // answer-space or options
          if (Q.qtype === 'mc') {
            html += '<ul>';
            Object.entries(Q.options).forEach(([key,opt]) => {
              html += `<li>${key}: ${opt.text}</li>`;
            });
            html += '</ul>';
          }
          else if (Q.qtype === 'ms') {
            html += '<ul>';
            Object.values(Q.options).forEach(opt => {
              html += `<li>- ${opt.text}</li>`;
            });
            html += '</ul>';
          }
          else if (Q.qtype === 'ma') {
            html += '<ul>';
            const arr = [];
            Object.values(Q.options).forEach(opt => {
              if (opt.pairNum) { arr.push(opt.left, opt.right); }
              else              { arr.push(opt.text); }
            });
            arr.forEach(item => html += `<li>- ${item}</li>`);
            html += '</ul>';
          }
          else if (Q.qtype === 'tf') {
            html += `<p>True ___ False ___</p>`;
          }
          else if (Q.qtype === 'sa' || Q.qtype === 'fb') {
            html += `<div class="answer-space" style="height:1.5em;"></div>`;
          }
          else if (Q.qtype === 'es') {
            html += `<div class="answer-space" style="height:6em;"></div>`;
          }
  
          // answer-level image? (if you ever use in test)
          if (Q.ansimg) {
            const src = masterAttachmentList[identity][Q.ansimg].url;
            const du  = urlToDataURI[src];
            if (du) html += `<div class="answer-img"><img src="${du}" alt="" /></div>`;
          }
  
          html += `</div>`; // close question
        }
  
        html += `</div>`; // close section
      }
  
      html += `</div>`; // close part
    }
  
    // 7) test-wide Reference Materials at bottom
    html += `
    <div class="page-break"></div>
    <div class="test-reference-materials">
      <h2>Reference Materials</h2>
  `;
    if (test.refText) {
      html += `  <div class="ref-text">${test.refText}</div>`;
    }
    if (Array.isArray(test.attachments)) {
      test.attachments.forEach(attID => {
        const att = masterAttachmentList[identity][attID];
        if (!att) return;
        if (att.url) {
          const du = urlToDataURI[att.url];
          if (du) html += `<div class="attachment-image"><img src="${du}" alt="${att.name||''}" /></div>`;
        } else if (att.text) {
          html += `<div class="attachment-text">${att.text}</div>`;
        }
      });
    }
    html += `</div>`;
  
    // 8) footer + download
    html += `
    ${template.footerText ? `<div>${template.footerText}</div>` : ""}
  </body>
  </html>
  `;
  
    const blob = new Blob([html], { type: 'text/html' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `${test.name}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
  
  

/**
 * exportTestKeyToHTML
 * Exports the answer key with grading instructions (in blue) and correct answers (in red),
 * and prefixes each question with its number.
 */

async function exportTestKeyToHTML(identity, testID) {
    // 1) grab the published test
    const published = masterTestList[identity].published;
    if (!published || !published[testID]) {
      alert("Test not found!");
      return;
    }
    const test = published[testID];
    const typeMap = {
        tf: "True/False",
        mc: "Multiple Choice",
        ms: "Multiple Selection",
        ma: "Matching",
        es: "Essay",
        sa: "Short Answer",
        fb: "Fill in the Blank"
    };
    // 2) grab the template and cover page
    const template = masterTemplateList[identity][test.templateID];
    if (!template) { alert("Invalid template!"); return; }
    const cp = masterCoverPageList[identity][template.coverPageID];
    if (!cp) { alert("Invalid cover page!"); return; }
  
    // 3) collect all image URLs (question + answer + test attachments)
    const urls = [];
    test.parts.forEach(part =>
      part.sections.forEach(section =>
        section.questions.forEach(qRef => {
          const Q = masterQuestionList[identity][qRef.qtype][qRef.id];
          if (Q.img)    urls.push(masterAttachmentList[identity][Q.img].url);
          if (Q.ansimg) urls.push(masterAttachmentList[identity][Q.ansimg].url);
        })
      )
    );
    if (Array.isArray(test.attachments)) {
      test.attachments.forEach(attID => {
        const att = masterAttachmentList[identity][attID];
        if (att && att.url) urls.push(att.url);
      });
    }
  
    // 4) dedupe and fetch into Data URIs
    const uniqueUrls = Array.from(new Set(urls));
    const urlToDataURI = {};
    await Promise.all(uniqueUrls.map(url =>
      fetch(url)
        .then(r => r.blob())
        .then(blob => new Promise(resolve => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result);
          reader.readAsDataURL(blob);
        }))
        .then(dataUri => { urlToDataURI[url] = dataUri; })
        .catch(() => {/* ignore missing */})
    ));
  
    // 5) build HTML
    let html = `
  <!DOCTYPE html>
  <html>
  <head>
    <meta charset="UTF-8">
    <title>${test.name} – Answer Key</title>
    <style>
      /* don't flatten our image and reference divs */
      .question > div:not(.answer-space):not(.question-img):not(.answer-img) {
        display: contents; margin: 0; padding: 0;
      }
      .q-num { font-weight: bold; margin-right: 0.5em; }
      body { font-family: ${template.bodyFont}, sans-serif; font-size: ${template.bodyFontSize}px; margin:20px; }
      .test-title { font-family: "${template.titleFont}", sans-serif; font-size: ${template.titleFontSize}px; text-align:center; }
      .cover-page { border:1px solid #ccc; padding:15px; margin-bottom:20px; }
      .part { margin-bottom:30px; }
      .part-title { font-size:20px; margin-top:20px; }
      .section-title { font-size:18px; margin-top:15px; }
      .question { margin-bottom:15px; }
      .correct-answer { color: red; font-weight:bold; }
      .grading-instructions { color: blue; font-style:italic; }
      .page-break { page-break-before: always; }
      .answer-header { color: red; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
  
      /* image styling */
      .question-img img,
      .answer-img img,
      .attachment-image img {
        display: block;
        border: 1px solid #ccc;
        padding: 4px;
        max-width: 100%;
        margin: 1em 0;
      }
  
      /* reference text styling */
      .question-ref-text { font-style: italic; margin-bottom: 0.5em; }
      .question-req-refs { font-weight: bold; margin-bottom: 0.5em; }
  
      /* test-wide references */
      .test-reference-materials { margin-top: 2em; }
      .test-reference-materials h2 { font-size: 1.5em; margin-bottom: 0.5em; }
      .ref-text, .attachment-text { margin-bottom: 1em; }
    </style>
  </head>
  <body>
    ${template.headerText ? `<div>${template.headerText}</div>` : ""}
    <h2 class="answer-header">Answer Key</h2>
    <h1 class="test-title">${test.name} – Answer Key</h1>
  
    <div class="cover-page">
      <h2>${cp.name}</h2>
      <p>Test Number: ${cp.testNum}</p>
      <p>Date: ${cp.date}</p>
      <p>Filename: ${cp.file}</p>
      <p class="grading-instructions">Instructions: ${cp.instructions}</p>
    </div>
    <div class="page-break"></div>
  `;
  
    // question loop
    let questionNumber = 1;
    for (let p = 0; p < test.parts.length; p++) {
      html += `<div class="part"><h2 class="part-title">Part ${p + 1}</h2>`;
      const part = test.parts[p];
      for (let s = 0; s < part.sections.length; s++) {
        const section = part.sections[s];
        let typeCode = section.questionType.toLowerCase();
        let type = typeMap[typeCode] || "Unknown Type";
        html += `<div><h3 class="section-title">${type}</h3>`;
        for (let q = 0; q < section.questions.length; q++) {
          const { id: Qid, qtype } = section.questions[q];
          const Q = masterQuestionList[identity][qtype][Qid];
  
          html += `<div class="question">`;
  
          // per-question references/images
          if (Q.reference)   html += `<div class="question-ref-text">${Q.reference}</div>`;
          if (Q.requiredRefs) html += `<div class="question-req-refs">${Q.requiredRefs}</div>`;
          if (Q.img) {
            const src = masterAttachmentList[identity][Q.img].url;
            const du  = urlToDataURI[src];
            if (du) html += `<div class="question-img"><img src="${du}" alt="" /></div>`;
          }
  
          // question number + text
          html += `<span class="q-num">${questionNumber++}.</span>${Q.text}`;
          
          // correct answer(s)
          html += `<p class="correct-answer">Answer:`;
          if (["es","sa","tf"].includes(Q.qtype)) {
            html += ` ${Q.answer.value}`;
          } else if(Q.qtype=="mc"){
            let answerLetter = Q.answer.value;
            console.log(answerLetter);
            console.log(JSON.stringify(Q.options));
            let answer = "";
            if(!Q.answer.value){
                answer = "No answer provided!";
            }else if(!Q.options[Q.answer.value]){
                answer = "Answer provided does not match any options!"
            }else{
                answer = Q.options[Q.answer.value].text;
            }
            html+= `${answer}`;       
          }else {
            Object.values(Q.answer).forEach(ans => {
              const val = ans.value || ans.text;
              html += ` ${val}<br>`;
            });
          }
          html += `</p>`;
  
          // answer image if any
          if (Q.ansimg) {
            const src = masterAttachmentList[identity][Q.ansimg].url;
            const du  = urlToDataURI[src];
            if (du) html += `<div class="answer-img"><img src="${du}" alt="" /></div>`;
          }
  
          // grading instructions
          html += `<p class="grading-instructions">Grading: ${Q.directions || ""}</p>`;
          html += `</div>`; // close question
        }
        html += `</div>`; // close section
      }
      html += `</div>`; // close part
    }
  
    // test-wide references at end
    html += `
    <div class="page-break"></div>
    <div class="test-reference-materials">
      <h2>Reference Materials</h2>`;
    if (test.refText) {
      html += `<div class="ref-text">${test.refText}</div>`;
    }
    if (Array.isArray(test.attachments)) {
      test.attachments.forEach(attID => {
        const att = masterAttachmentList[identity][attID];
        if (!att) return;
        if (att.url) {
          const du = urlToDataURI[att.url];
          if (du) html += `<div class="attachment-image"><img src="${du}" alt="${att.name||""}" /></div>`;
        } else if (att.text) {
          html += `<div class="attachment-text">${att.text}</div>`;
        }
      });
    }
    html += `</div>`;
  
    // footer
    html += `
    ${template.footerText ? `<div>${template.footerText}</div>` : ""}
  </body>
  </html>
  `;
  
    // download
    const blob = new Blob([html], { type: 'text/html' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `${test.name}-Key.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
  

function updateCoverPages(identity) {
    const coverPageContainer = document.getElementById(`coverpages-${identity}`);
    coverPageContainer.innerHTML = ''; // Clear existing content

    if (!masterCoverPageList[identity] || masterCoverPageList[identity].length === 0) {
        coverPageContainer.innerHTML = '<p>You have not added any cover pages yet...</p>';
        return;
    }
    cpages = masterCoverPageList[identity];
    for(const key in cpages){
        let coverPage = cpages[key];
        const coverPageDiv = document.createElement('div');
        coverPageDiv.style.backgroundColor = '#d0d0d0';
        coverPageDiv.style.padding = '5px';
        coverPageDiv.style.marginBottom = '8px';
        coverPageDiv.style.borderBottom = '1px solid #ccc';
        coverPageDiv.classList.add('context-menu-target');
        coverPageDiv.dataset.itemType = 'coverPage';
        coverPageDiv.dataset.itemID = coverPage.id; //RED TASK: MAKE UNIQUE ON BACKEND, SERVE ID for IDENTITY
        coverPageDiv.dataset.identity = identity;

        coverPageDiv.innerHTML = `
            <p><strong>${coverPage.name}</strong> (Test Number: ${coverPage.testNum}, Date: ${coverPage.date})</p>
            <p>Filename: ${coverPage.file}</p>
            <p>Grading Instructions: ${coverPage.instructions}</p>
        `;

        coverPageContainer.appendChild(coverPageDiv);
    }
}


function updateTemplates(identity) {
    const templateContainer = document.getElementById(`templates-${identity}`);
    templateContainer.innerHTML = ''; 

    if (!masterTemplateList[identity] || masterTemplateList[identity].length === 0) {
        templateContainer.innerHTML = '<p>You have not added any templates yet...</p>';
        return;
    }

    let templates = masterTemplateList[identity];
    for(const key in templates){
        if(key == "bonusQuestions"){
            continue;
        }
        let template = templates[key];
        const templateDiv = document.createElement('div');
        templateDiv.style.backgroundColor = '#d0d0d0';
        templateDiv.style.padding = '5px';
        templateDiv.style.marginBottom = '8px';
        templateDiv.style.borderBottom = '1px solid #ccc';
        templateDiv.classList.add('context-menu-target');
        templateDiv.dataset.itemType = 'template';
        templateDiv.dataset.itemID = template.id;
        templateDiv.dataset.identity = identity;

        templateDiv.innerHTML = `
            <p><strong>${template.name}</strong></p>
        `;

        templateContainer.appendChild(templateDiv);
    }
}


function updateGraphicSelectors(identity) {
    const qGraphicField = document.getElementById('qGraphicField');
    const ansGraphicField = document.getElementById('ansGraphicField');

    qGraphicField.innerHTML = '<option value="" disabled selected>Select a graphic</option>';
    ansGraphicField.innerHTML = '<option value="" disabled selected>Select a graphic</option>';


    for(const key in masterAttachmentList[identity]){
        let attachment = masterAttachmentList[identity][key];
        const option = document.createElement('option');
        option.value = attachment.id;
        option.textContent = attachment.name;
        qGraphicField.appendChild(option);

        const ansOption = document.createElement('option');
        ansOption.value = attachment.id;
        ansOption.textContent = attachment.name;
        ansGraphicField.appendChild(ansOption);
    }
}

function updateTestAttachments(identity) {
    const testGraphicField = document.getElementById('testGraphicField');
    
    // Clear the dropdown first
    testGraphicField.innerHTML = '<option value="" disabled>Select required attachments</option>';
    
    // Populate with attachment options
    for(const key in masterAttachmentList[identity]){
        let attachment = masterAttachmentList[identity][key];
        const option = document.createElement('option');
        option.value = attachment.id;
        option.textContent = attachment.name || attachment.url;
        testGraphicField.appendChild(option);
    }
}

/**
 * This function is called when the user clicks the delete button in the context menu.
 * It determines the type of item being deleted and calls the appropriate delete function.
 * Precondition: context menu is open, delete button is clicked, and is not published
 * Postcondition: item is deleted from the master list, if it is not published
*/
async function deleteItem() {
    const contextMenu = document.getElementById('contextMenu');
    const itemType = contextMenu.dataset.itemType;
    const itemID = contextMenu.dataset.itemID;
    const identity = contextMenu.dataset.identity;
    const questionType = contextMenu.dataset.questionType;
    const testType = contextMenu.dataset.testType;
    const username = window.username;
    let type =itemType;
    

    let itemToDelete;
    switch(itemType) {
        case 'question':
            type="Question"
            itemToDelete = masterQuestionList[identity][questionType][String(itemID)];
            break;
        case 'test':
            type="Test"
            console.log("Trying to delete:", {
                identity: identity,
                testType,
                itemID,
                masterTestList: masterTestList[identity],
                test: masterTestList[identity][testType]
            });
            itemToDelete = masterTestList[identity][testType][String(itemID)];
            break;
        case 'template':
            type = "Template"
            itemToDelete = masterTemplateList[identity][String(itemID)];
            break;
        case 'coverPage':
            type="CoverPage"
            itemToDelete = masterCoverPageList[identity][String(itemID)];
            break;
        case 'attachment':
            type="Attachment"
            itemToDelete = masterAttachmentList[identity][String(itemID)];
            break;
        default:
            console.error('Unknown item type:', type);
            return;
    }
    
    if(itemToDelete.published){
        if(itemToDelete.published==1){
            alert("You cannot delete published items! Contact the administrators if you must!");
            return;
        }
    }


    // Confirm deletion
    if (!confirm(`Are you sure you want to delete this ${type}?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/delete_item/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                model_type: type,
                id: itemToDelete.id,
                username: username,
                identity: identity
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Remove the item from the local array
            switch(type) {
                case 'question':
                    delete masterQuestionList[identity][questionType][itemID];
                    break;
                case 'test':
                    delete masterTestList[identity][testType][itemID];
                    break;
                case 'template':
                    delete masterTemplateList[identity][itemID];
                    break;
                case 'coverPage':  
                    delete masterCoverPageList[identity][itemID];
                    break;
                case 'attachment':
                    delete masterAttachmentList[identity][itemID];
                    break;
            }

            reloadData();
            
            // Show success message
            alert(data.message || `${type} successfully deleted.`);
        } else {
            alert(data.message || 'An error occurred while deleting the item.');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while connecting to the server.');
    }
}

