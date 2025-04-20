//Can be used for session-level storage and testing
var masterQuestionList = {};
var masterTestList = {};
var masterTemplateList = {};
var masterAttachmentList = {};
var courseList = {};
var masterCoverPageList = {};
var masterTextbookList = {};


/**
 * getUserIdentity to determine identity based on user role
*/
function getUserIdentity(courseID, isbn) {
  const ownerRole = document.getElementById('userRole')?.value;
  if (ownerRole === 'teacher' || ownerRole === 'webmaster') {
    return courseID;
  } else if (ownerRole === 'publisher') {
    return isbn;
  }
  // fallback to whichever is defined
  return courseID || isbn;
}

/**
 * This function is called to update the question content inside the question containers whenever a question is saved
 * Precondition: valid questionType, courseID
 * Postcondition: question content is updated in the question containers
*/
function updateQuestionTabs(questionType, courseID, isbn) {
    const identity = getUserIdentity(courseID, isbn);
    const tabContent = document.getElementById(`${questionType}-${identity}`);
    tabContent.innerHTML = ''; // Clear existing content

    const questions = masterQuestionList[identity][questionType];

    if (questions.length === 0) {
        tabContent.innerHTML = `<p>No ${questionType.toUpperCase()} questions available...</p>`;
    } else {
        for(const key in questions){
            let question = questions[key];
            const questionDiv = document.createElement('div');
            questionDiv.style.backgroundColor = '#d0d0d0';
            questionDiv.style.padding = '5px';
            questionDiv.style.marginBottom = '8px';
            questionDiv.style.borderBottom = '1px solid #ccc';
            questionDiv.classList.add('context-menu-target');
            questionDiv.dataset.itemType = 'question';
            questionDiv.dataset.itemID = question.id;
            questionDiv.dataset.identity = identity;
            questionDiv.dataset.courseID = courseID;
            questionDiv.dataset.isbn = isbn;
            questionDiv.dataset.questionType = questionType;

            questionDiv.innerHTML = `
                <p><strong>${question.text}</strong></p>
                <p>Points: ${question.score}</p>
                <p>Estimated Time: ${question.eta} minutes</p>
            `;

            tabContent.appendChild(questionDiv);
        }
    }
}



/**
 * Defines the UI for a given course, used to interact with everything else
 * Preconditions: requires users provide all of the course addition data
 * Postconditions: Creates a course UI with panes for question and test data
*/
async function addCourse() {
    const courseID = document.getElementById('courseID').value.trim();
    const courseName = document.getElementById('courseName').value.trim();
    const courseCRN = document.getElementById('courseCRN').value.trim();
    const courseSemester = document.getElementById('courseSemester').value;
    const textbookTitle = document.getElementById('courseTextbookTitle').value.trim();
    const textbookAuthor = document.getElementById('courseTextbookAuthor').value.trim();
    const textbookVersion = document.getElementById('courseTextbookVersion').value.trim();
    const textbookISBN = document.getElementById('courseTextbookISBN').value.trim();
    const textbookLink = document.getElementById('courseTextbookLink').value.trim();
    const isbn = null;

    if (!courseID || !courseName || !courseCRN || !courseSemester || !textbookTitle || !textbookAuthor || !textbookISBN || !textbookVersion || !textbookLink) {
        alert("All fields (Course ID, Name, CRN, Semester, and Textbook Title/Author/Version/ISBN/Link) are required.");
        return;
    }

    if (courseList[courseID]) {
        alert("Error: A course with that ID already exists.");
        return;
    }

    const courseContainer = document.createElement('div');
    courseContainer.classList.add('course-container');
    const identity = getUserIdentity(courseID, isbn);
    courseContainer.dataset.identity = identity;
    courseContainer.dataset.courseID = courseID;
    courseContainer.dataset.isbn = isbn;
    courseContainer.innerHTML = `
        <details>
            <summary><strong>${courseName}</strong> (ID: ${identity}, CRN: ${courseCRN}, ${courseSemester})</summary>
            <details>
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
                <button class="add-btn" onclick="openEditor('Test', '${identity}')">Add Test</button>
                <button class="add-btn" onclick="openImporter('${identity}', '${courseName}', '${courseCRN}', '${courseSemester}', '${textbookTitle}', '${textbookAuthor}', '${textbookVersion}', '${textbookISBN}', '${textbookLink}')">Import Test</button>
                <input type="file" id="fileInput">
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
            </details>
            <button class="remove-btn" onclick="confirmRemoveCourse('${identity}')">Remove Course</button>
        </details>
    `;

    document.getElementById('courseList').appendChild(courseContainer);
    document.getElementById('courseID').value = "";
    document.getElementById('courseName').value = "";
    document.getElementById('courseCRN').value = "";
    document.getElementById('courseSemester').value = "";
    document.getElementById('courseTextbookTitle').value = "";
    document.getElementById('courseTextbookAuthor').value = "";
    document.getElementById('courseTextbookVersion').value = "";
    document.getElementById('courseTextbookISBN').value = "";
    document.getElementById('courseTextbookLink').value = "";

    const questionList = {
        'tf': [],
        'mc': [],
        'sa': [],
        'es': [],
        'ma': [],
        'ms': [],
        'fb': []
    };
    const testList = {
        'drafts': {},
        'published': {}
    };

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

    masterQuestionList[identity] = questionList;
    masterTestList[identity] = testList;
    masterCoverPageList[identity] = {};
    masterTemplateList[identity] = {};
    masterTemplateList[identity].bonusQuestions = [];

    const coverPageDefault = {
        name: "Default 1st Test",
        testNum: 1,
        date: `${year}-${month}-${date}`,
        file: "defaultpage",
        showFilename: true,
        blank: "TR",
        instructions: "Grade according to the rubric, giving partial credit where indicated",
        published: 1
    };

    const coverPageDefault2 = {
        name: "Default 2nd Test",
        testNum: 2,
        date: `${year}-${month}-${date}`,
        file: "defaultpage_2",
        showFilename: true,
        blank: "TR",
        instructions: "Grade according to the rubric, giving partial credit where indicated",
        published: 1
    };

    const coverPageDefault3 = {
        name: "Default 3rd Test",
        testNum: 3,
        date: `${year}-${month}-${date}`,
        file: "defaultpage_3",
        showFilename: true,
        blank: "TR",
        instructions: "Grade according to the rubric, giving partial credit where indicated",
        published: 1
    };

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
        coverPageID: 0,
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

   
    if(!masterTextbookList[textbookISBN]){
        let textbook = {
            questions: [],
            title: textbookTitle,
            author: textbookAuthor,  
            version: textbookVersion,    
            isbn: textbookISBN,  
            link: textbookLink  
        };
        masterTextbookList[textbookISBN] = textbook;
    }

    if(!masterAttachmentList[identity]){
        let attachmentList = {};
        masterAttachmentList[identity] = attachmentList;
    }

    const thisCourse = {
        course_id: courseID,
        name: courseName,
        crn: courseCRN,
        sem: courseSemester,
        textbook: masterTextbookList[textbookISBN]
    };

    try {
        await saveData("course", thisCourse, identity);
        await saveData("coverPage", coverPageDefault, identity);
        await saveData("coverPage", coverPageDefault2, identity);
        await saveData("coverPage", coverPageDefault3, identity);
        await saveData("template", templateDefault, identity);
        updateCoverPages(identity);
        updateTemplates(identity); 

    } catch (error) {
        console.error("Error saving course data:", error);
        alert("There was an error saving your course. Please try again.");
    }
}


/**
 * Used to remove a course 
 * Precondition: the course exists
 * Postcondition: the course no longer exists
 * 
*/
async function confirmRemoveCourse(courseID, isbn) {
    const identity = getUserIdentity(courseID, isbn);
    if (confirm("Are you sure you want to delete this course? This action cannot be undone.")) {
        try {
        let username = window.username;
        let itemToDelete=courseList[identity];
        let type = "Course"
        const response = await fetch('/api/delete_item/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                model_type: type,
                id: itemToDelete.dbid,
                username: username,
                identity: identity
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Remove the item from the local array
            delete courseList[identity];
            if(Object.keys(courseList).length === 0 && courseList.constructor === Object){
            document.getElementById('courseList').innerHTML = "";
            console.log("No courses to load");
            return;
            }else{
                reloadData();
            }
            
            
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

/**
 * Save data to the server based on type.  - Note: this function and its children have been modified by Claude 3.7 Sonnet!
 * @param {string} type - The type of data to save (e.g., 'test', 'question')
 * @param {Object} entry - The data to save
 * @param {string} courseID - Course ID for teacher content
 * @param {string} isbn - ISBN for publisher content (optional)
 * @returns {Promise} A promise that resolves with the server response
 */
 /**
 * Save data to the server based on type.
 * Fixed to improve error handling and data validation
 */
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
    
    const ownerRole = document.getElementById('userRole')?.value || "teacher";
    
    try {
        // Determine which API endpoint to use and prepare the data
        switch(type) {
            case "course":
                api_call = "/api/save_course/";
                requestData = serializeCourse(entry);
                headers['Content-Type'] = 'application/json';
                break;
                
            case "question":
                api_call = "/api/save_question/";
                requestData = await serializeQuestion(entry, courseID, isbn);
                headers['Content-Type'] = 'application/json';
                break;
                
            case "template":
                api_call = "/api/save_template/";
                requestData = serializeTemplate(entry, courseID, isbn);
                headers['Content-Type'] = 'application/json';
                break;
                
            case "coverPage":
                api_call = "/api/save_cpage/";
                requestData = serializeCoverPage(entry, courseID, isbn);
                headers['Content-Type'] = 'application/json';
                break;
                
            case "test":
                api_call = "/api/save_test/";
                requestData = await serializeTest(entry, courseID, isbn);
                headers['Content-Type'] = 'application/json';
                break;
                
            case "attachment":
                api_call = "/api/save_attachment/";
                const formData = new FormData();
                formData.append('attachment_name', entry.name || 'Unnamed Attachment');
                
                // FIX: Validate file exists before trying to append it
                if (entry.file instanceof File || entry.file instanceof Blob) {
                    formData.append('attachment_file', entry.file);
                } else {
                    showErrorMessage("Missing or invalid file for attachment");
                    return Promise.reject(new Error("Missing or invalid file"));
                }
                
                if (entry.url) formData.append('attachment_url', entry.url);
                formData.append('courseID', courseID || '');
                if (isbn) formData.append('isbn', isbn);
                formData.append('ownerRole', ownerRole);
                return sendFormData(api_call, formData);
                
            default:
                throw new Error(`Invalid type to save: ${type}`);
        }

        // FIX: Validate api_call is set
        if (!api_call) {
            throw new Error("API endpoint not specified");
        }

        const response = await fetch(api_call, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(requestData)
        });
        
        // FIX: Better error handling for non-JSON responses
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

/**
 * Helper function to send form data
 */
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

/**
 * Display success message
 */
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

/**
 * Display error message
 */
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
    const ownerRole = document.getElementById('userRole')?.value || "teacher";
    
    // Build the request data
    const requestData = {
        ownerRole: ownerRole,
        course: {
            id: course.id || null,
            course_id: course.course_id || '',
            name: course.name || 'Untitled Course',
            crn: course.crn || '',
            sem: course.sem || '',
            published: course.published || false
        }
    };
    
    // Format the textbook data if available
    if (course.textbook) {
        requestData.textbook = {
            id: course.textbook.id || null,
            title: course.textbook.title || '',
            author: course.textbook.author || '',
            version: course.textbook.version || '',
            isbn: course.textbook.isbn || '',
            link: course.textbook.link || null,
            published: course.textbook.published || false
        };
    }

    return requestData;
}

/**
 * Serialize a template object for the API
 */
function serializeTemplate(template, courseID = null, isbn = null) {
    const ownerRole = document.getElementById('userRole')?.value || "teacher";
    
    // Build the request data
    const requestData = {
        ownerRole: ownerRole,
        courseID: courseID || null,
        isbn: isbn || null,
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

    confirm(JSON.stringify(template));
    return requestData;
}

/**
 * Serialize a cover page object for the API
 */
function serializeCoverPage(coverPage, courseID = null, isbn=null) {
    const ownerRole = document.getElementById('userRole')?.value || "teacher";
    
    // Build the request data
    const requestData = {
        ownerRole: ownerRole,
        courseID: courseID || null,
        isbn: isbn || null,
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
function serializeQuestion(question, courseID=null, isbn=null) {
    const ownerRole = document.getElementById('userRole')?.value || "teacher";
    
    // Build the base request data
    const requestData = {
        ownerRole: ownerRole,
        courseID: courseID,
        isbn: isbn
    };
    
    
    // Format the question data with proper type checking
    requestData.question = {
        id: question.id || null,
        qtype: question.qtype || 'mc',
        text: question.text || '',
        eta: parseInt(question.eta) || 1, 
        directions: question.directions || null,
        reference: question.reference || null,
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
                username: fb.username || null,
                rating: fb.rating || null,
                averageScore: fb.averageScore || null,
                comments: fb.comments || null,
                time: fb.time || null,
                responses: Array.isArray(fb.responses) ? fb.responses
                    .filter(resp => resp) 
                    .map(resp => ({
                        username: resp.username || null,
                        text: resp.text || null,
                        date: resp.date || null
                    })) : []
            }));
    }
    
    return requestData;
}




/**
 * Serialize a test object for the API
 * Fixed to handle null values and improve data transformation
 */
 function serializeTest(test, courseID=null, isbn=null) {
    const ownerRole = document.getElementById('userRole')?.value || "teacher";
    console.log(test, courseID, isbn);

    // Build the base request data
    const requestData = {
        ownerRole: ownerRole,
        courseID: courseID,
        isbn: isbn
    };
    
    // Format the test data
    requestData.test = {
        id: test.id || null,
        name: test.name || 'Untitled Test',
        date: test.date || null,
        filename: masterCoverPageList[courseID][test.template.coverPageID].file || masterCoverPageList[isbn][test.template.coverPageID].file|| null,
        is_final: Boolean(test.published), 
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
                    username: fb.username || null,
                    rating: fb.rating || null,
                    averageScore: fb.averageScore || null,
                    comments: fb.comments || null,
                    time: fb.time || null,
                    responses: Array.isArray(fb.responses) ? fb.responses
                        .filter(resp => resp) 
                        .map(resp => ({
                            username: resp.username || null,
                            text: resp.text || null,
                            date: resp.date || null
                        })) : []
                }));
        }
    }
    
    // Format attachments if available
    if (Array.isArray(test.attachments) && test.attachments.length > 0) {
        requestData.attachments = test.attachments
            .filter(attachment => attachment) // Filter out null/undefined values
            .map(attachment => {
                return typeof attachment === 'object' && attachment !== null 
                    ? (attachment.id || null) 
                    : attachment;
            })
            .filter(id => id !== null); // Filter out null or undefined values
    }
    
    console.log(JSON.stringify(requestData));
    return requestData;
}


function renderUserData(data){
        masterQuestionList = data.question_list;
        masterAttachmentList = data.attachment_list;
        masterTemplateList = data.template_list;
        masterTestList = data.test_list;
        console.log(masterTestList);
        courseList = data.container_list;
        masterCoverPageList = data.cpage_list;
        console.log("Cover Pages:", masterCoverPageList);
        refreshData();
        
}

function refreshData(){
    const courseContainer = document.getElementById("courseList");
        courseContainer.innerHTML = "";
        for(const [key,value] of Object.entries(courseList)){
            loadCourse(key);
        }
}

function loadCourse(courseID){
    let course = courseList[courseID];
    let courseName = course.name;
    let courseCRN = course.crn;
    let courseSemester = course.sem;
    let textbookTitle = course.textbook.title;
    let textbookAuthor = course.textbook.author;
    let textbookVersion = course.textbook.version;
    let textbookISBN = course.textbook.isbn;
    let textbookLink = course.textbook.link;

    const courseContainer = document.createElement('div');
        courseContainer.classList.add('course-container');
        courseContainer.innerHTML = `
        <details>
            <summary><strong>${courseName}</strong> (ID: ${courseID}, CRN: ${courseCRN}, ${courseSemester})</summary>
            <details>
                <summary>Questions</summary>
            <button class="add-btn" onclick="openEditor('Question', '${courseID}')">Add Question</button>
            <div class="tab-container">
                <div class="tabs">
                    <div class="tab active" onclick="switchTab(event, 'tf-${courseID}')">True/False</div>
                    <div class="tab" onclick="switchTab(event, 'mc-${courseID}')">Multiple Choice</div>
                    <div class="tab" onclick="switchTab(event, 'sa-${courseID}')">Short Answer</div>
                    <div class="tab" onclick="switchTab(event, 'es-${courseID}')">Essay</div>
                    <div class="tab" onclick="switchTab(event, 'ma-${courseID}')">Matching</div>
                    <div class="tab" onclick="switchTab(event, 'ms-${courseID}')">Multiple Selection</div>
                    <div class="tab" onclick="switchTab(event, 'fb-${courseID}')">Fill in the Blank</div>
                </div>
                <div class="tab-content active" id="tf-${courseID}"><p>True/False questions go here...</p></div>
                <div class="tab-content" id="es-${courseID}"><p>Essay questions go here...</p></div>
                <div class="tab-content" id="mc-${courseID}"><p>Multiple Choice questions go here...</p></div>
                <div class="tab-content" id="sa-${courseID}"><p>Short Answer questions go here...</p></div>
                <div class="tab-content" id="ma-${courseID}"><p>Matching questions go here...</p></div>
                <div class="tab-content" id="ms-${courseID}"><p>Multiple Selection questions go here...</p></div>
                <div class="tab-content" id="fb-${courseID}"><p>Fill in the Blank questions go here...</p></div>
            </div>
            </details>

            <details>
                <summary>Cover Pages</summary>
                    <button class="add-btn" onclick="openEditor('Cover Page', '${courseID}')">Add Cover Page</button>
                    <div id="coverpages-${courseID}"><p>You have not added any cover pages yet...</p></div>
            </details>

            <details>
                <summary>Templates</summary>
                    <button class="add-btn" onclick="openEditor('Template', '${courseID}')">Add Template</button>
                    <div id="templates-${courseID}"><p>You have not added any templates yet...</p></div>
            </details>

            <details>
                <summary>Tests</summary>
                <button class="add-btn" onclick="openEditor('Test', '${courseID}')">Add Test</button>
                <button class="add-btn" onclick="openImporter('${courseID}', '${courseName}', '${courseCRN}', '${courseSemester}', '${textbookTitle}', '${textbookAuthor}', '${textbookVersion}', '${textbookISBN}', '${textbookLink}')">Import Test</button>
                <input type="file" id="fileInput">
                <div class="tab-container">
                <div class="tabs">
                    <div class="tab active" onclick="switchTab(event, 'drafts-${courseID}')">Drafts</div>
                    <div class="tab" onclick="switchTab(event, 'published-${courseID}')">Published Tests</div>
                </div>
                <div class="tab-content active" id="drafts-${courseID}"><p>Saved drafts go here...</p></div>
                <div class="tab-content" id="published-${courseID}"><p>Published tests go here...</p></div>
            </div>
            </details>

            <details>
                <summary>Attachments</summary>
                <button class="add-btn" onclick="openEditor('Attachment', '${courseID}')">Add Attachment</button>
                <div id="attachments-${courseID}"><p>You have not uploaded any attachments yet...</p></div>
            </details>
            <button class="remove-btn" onclick="confirmRemoveCourse('${courseID}')">Remove Course</button>
        </details>
        `;

        document.getElementById('courseList').appendChild(courseContainer);
        document.getElementById('courseID').value = "";
        document.getElementById('courseName').value = "";
        document.getElementById('courseCRN').value = "";
        document.getElementById('courseSemester').value = "";
        document.getElementById('courseTextbookTitle').value = "";
        document.getElementById('courseTextbookAuthor').value = "";
        document.getElementById('courseTextbookVersion').value = "";
        document.getElementById('courseTextbookISBN').value = "";
        document.getElementById('courseTextbookLink').value = "";

        updateCoverPages(courseID);
        updateTemplates(courseID);
        updateQuestionTabs("tf",courseID);
        updateQuestionTabs("ma",courseID);
        updateQuestionTabs("es",courseID);
        updateQuestionTabs("sa",courseID);
        updateQuestionTabs("ms",courseID);
        updateQuestionTabs("fb",courseID);
        updateQuestionTabs("mc",courseID);
        updateTestTabs(courseID);
        updateAttachments(courseID);
}



// Imports a QTI file into the MySQL database
function openImporter(id, name, crn, semester, textTitle, textAuthor, textVersion, isbn, link) {
    let fileInput = document.getElementById("fileInput");
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
    formData.append("courseTextbookTitle", textTitle);
    formData.append("courseTextbookAuthor", textAuthor);
    formData.append("courseTextbookVersion", textVersion);
    formData.append("courseTextbookISBN", isbn);
    formData.append("courseTextbookLink", link);

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
        // You could loop through data.questions and inject them into the DOM here


        // I thought these would refresh the tests automatically, but they don't seem to actually do that when called like this.
        //reloadData();
        //updateTestTabs(courseID);

        if (data.success) {
            alert(data.success);
        } else {
            alert("Error: " + data.error);
        }

    })
    .catch(error => console.error("Error:", error));
}




/**
 * This function is called to update the test content inside of the test containers whenever a test is saved
 * Precondition: valid courseID
 * Postcondition: test content is updated in the test containers    
*/ 
function updateTestTabs(courseID) {
    const draftsContainer = document.getElementById(`drafts-${courseID}`);
    const publishedContainer = document.getElementById(`published-${courseID}`);
    draftsContainer.innerHTML = ''; // Clear existing content
    publishedContainer.innerHTML = ''; // Clear existing content
    console.log("TEST LIST:");
    console.log(masterTestList);
    if(!masterTestList[courseID]){
        masterTestList[courseID] = {};
    }
    if(!masterTestList[courseID].drafts){
        masterTestList[courseID].drafts = {};
    }
    if(!masterTestList[courseID].published){
        masterTestList[courseID].published = {};
    }
    const drafts = masterTestList[courseID].drafts;
    const published = masterTestList[courseID].published;

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
            testDiv.dataset.courseID = courseID;
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
            testDiv.dataset.courseID = courseID;
            testDiv.dataset.testType = 'published';

            testDiv.innerHTML = `
                <p><strong>${test.name}</strong></p>
                <p>Template: ${test.templateName}</p>
                <p>Parts: ${test.parts.length}</p>
                <button class="add-btn" onclick="exportTestToHTML('${courseID}', '${test.id}')">Export Test</button>
                <button class="add-btn" onclick="exportTestKeyToHTML('${courseID}', '${test.id}')">Export Test Key</button>
            `;

            publishedContainer.appendChild(testDiv);
        }
    }
}


/**
 * exportTestToHTML
 * Exports a test (without answers or grading instructions) to HTML.
 * Customizations (fonts, header/footer, cover page, etc.) are taken from the test's template.
 */
function exportTestToHTML(courseID, testIndex) {
    // Retrieve the published test
    const publishedTests = masterTestList[courseID].published;
    if (!publishedTests || testIndex >= publishedTests.length) {
        alert("Test not found!");
        return;
    }
    const test = publishedTests[testIndex];
    const template = masterTextbookList[test.templateID] || 1;

    // Begin building HTML with custom CSS from the template
    let htmlOutput = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${test.name} - Exported Test</title>
  <style>
    body {
      font-family: ${template.bodyFont}, sans-serif;
      font-size: ${template.bodyFontSize}px;
      margin: 20px;
    }
    .header-text {
      text-align: center;
      margin-bottom: 20px;
      font-size: ${template.headerFontSize || 16}px;
    }
    .test-title {
      font-family: ${template.titleFont}, sans-serif;
      font-size: ${template.titleFontSize}px;
      color: #0077C8;
      text-align: center;
      margin-bottom: 10px;
    }
    .test-subtitle {
      font-family: ${template.subtitleFont}, sans-serif;
      font-size: ${template.subtitleFontSize}px;
      text-align: center;
      margin-bottom: 20px;
    }
    .cover-page {
      border: 1px solid #ccc;
      padding: 10px;
      margin-bottom: 20px;
    }
    .part {
      margin-bottom: 30px;
    }
    .part-title {
      font-size: 20px;
      margin-top: 20px;
    }
    .section-title {
      font-size: 18px;
      margin-top: 15px;
    }
    .question {
      margin-bottom: 15px;
    }
    .footer-text {
      text-align: center;
      margin-top: 30px;
      font-size: ${template.footerFontSize || 16}px;
    }
  </style>
</head>
<body>
  ${template.headerText ? `<div class="header-text">${template.headerText}</div>` : ""}
  <h1 class="test-title">${test.name}</h1>
  ${template.subtitleText ? `<h2 class="test-subtitle">${template.subtitleText}</h2>` : ""}
`;

    // Optionally include cover page details if defined
    if (template.coverPage) {
        const cp = template.coverPage;
        htmlOutput += `
  <div class="cover-page">
    <h2>${cp.name}</h2>
    <p>Test Number: ${cp.testNum}</p>
    <p>Date: ${cp.date}</p>
    <p>Filename: ${cp.file}</p>
    <p>Instructions: ${cp.instructions}</p>
  </div>
`;
    }

    // Loop through each Part, Section, and Question (fixed looping)
    for (let p = 0; p < test.parts.length; p++) {
        const part = test.parts[p];
        htmlOutput += `<div class="part"><h2 class="part-title">Part ${p + 1}</h2>`;
        for (let s = 0; s < part.sections.length; s++) {
            const section = part.sections[s];
            htmlOutput += `<div class="section"><h3 class="section-title">Section ${s + 1} (${section.questionType.toUpperCase()})</h3>`;
            for (let q = 0; q < section.questions.length; q++) {
                const questionData = section.questions[q];
                const question = masterQuestionList[courseID][questionData.qtype][questionData.id];
                htmlOutput += `
    <div class="question">
      <p>${question.text}</p>
    </div>
                `;
            }
            htmlOutput += `</div>`;
        }
        htmlOutput += `</div>`;
    }

    htmlOutput += `
  ${template.footerText ? `<div class="footer-text">${template.footerText}</div>` : ""}
</body>
</html>
    `;

    // Create a Blob and trigger download
    const blob = new Blob([htmlOutput], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${test.name}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * exportTestKeyToHTML
 Exports the test key (answer key) as HTML.
 * In the answer key export, grading instructions (in blue) and correct answers (in red) are displayed.
 */
function exportTestKeyToHTML(courseID, testIndex) {
    // Retrieve the published test
    const publishedTests = masterTestList[courseID].published;
    if (!publishedTests || testIndex >= publishedTests.length) {
        alert("Test not found!");
        return;
    }
    const test = publishedTests[testIndex];
    const template = masterTextbookList[test.templateID] || 1;

    let htmlOutput = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${test.name} - Exported Test Key</title>
  <style>
    body {
      font-family: ${template.bodyFont}, sans-serif;
      font-size: ${template.bodyFontSize}px;
      margin: 20px;
    }
    .header-text {
      text-align: center;
      margin-bottom: 20px;
      font-size: ${template.headerFontSize || 16}px;
    }
    .test-title {
      font-family: ${template.titleFont}, sans-serif;
      font-size: ${template.titleFontSize}px;
      color: #0077C8;
      text-align: center;
      margin-bottom: 10px;
    }
    .test-subtitle {
      font-family: ${template.subtitleFont}, sans-serif;
      font-size: ${template.subtitleFontSize}px;
      text-align: center;
      margin-bottom: 20px;
    }
    .cover-page {
      border: 1px solid #ccc;
      padding: 10px;
      margin-bottom: 20px;
    }
    .part {
      margin-bottom: 30px;
    }
    .part-title {
      font-size: 20px;
      margin-top: 20px;
    }
    .section-title {
      font-size: 18px;
      margin-top: 15px;
    }
    .question {
      margin-bottom: 15px;
    }
    .grading-instructions {
      color: blue;
      font-style: italic;
    }
    .correct-answer {
      color: red;
      font-weight: bold;
    }
    .footer-text {
      text-align: center;
      margin-top: 30px;
      font-size: ${template.footerFontSize || 16}px;
    }
  </style>
</head>
<body>
  ${template.headerText ? `<div class="header-text">${template.headerText}</div>` : ""}
  <h1 class="test-title">${test.name} - Answer Key</h1>
  ${template.subtitleText ? `<h2 class="test-subtitle">${template.subtitleText}</h2>` : ""}
`;

    // Optionally include cover page details if defined in the template
    if (template.coverPage) {
        const cp = template.coverPage;
        htmlOutput += `
  <div class="cover-page">
    <h2>${cp.name}</h2>
    <p>Test Number: ${cp.testNum}</p>
    <p>Date: ${cp.date}</p>
    <p>Filename: ${cp.file}</p>
    <p class="grading-instructions">Instructions: ${cp.instructions}</p>
  </div>
`;
    }

    // Loop through each part, section, and question. Grading instructions and correct answers are only included here.
    for (let p = 0; p < test.parts.length; p++) {
        const part = test.parts[p];
        htmlOutput += `<div class="part"><h2 class="part-title">Part ${p + 1}</h2>`;
        for (let s = 0; s < part.sections.length; s++) {
            const section = part.sections[s];
            htmlOutput += `<div class="section"><h3 class="section-title">Section ${s + 1} (${section.questionType.toUpperCase()})</h3>`;
            for (let q = 0; q < section.questions.length; q++) {
                const questionData = section.questions[q];
                const question = masterQuestionList[courseID][questionData.qtype][questionData.id];
                
                htmlOutput += `
    <div class="question">
      <p>${question.text}</p>
      <p class="correct-answer">Correct Answer: ${question.answer.value}</p>
      <p class="grading-instructions">Grading Instructions: ${question.directions}</p>
    </div>
                `;
            }
            htmlOutput += `</div>`;
        }
        htmlOutput += `</div>`;
    }

    htmlOutput += `
  ${template.footerText ? `<div class="footer-text">${template.footerText}</div>` : ""}
</body>
</html>
    `;

    // Create a Blob and trigger download for the key export
    const blob = new Blob([htmlOutput], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${test.name}-Key.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}


/**
 * This function is called to update the coverpage options inside any template editor
 * Precondition: valid courseID
 * Postcondition: cover page options are updated in the template editor
*/
function updateCoverPages(courseID) {
    const coverPageContainer = document.getElementById(`coverpages-${courseID}`);
    coverPageContainer.innerHTML = ''; // Clear existing content

    if (!masterCoverPageList[courseID] || masterCoverPageList[courseID].length === 0) {
        coverPageContainer.innerHTML = '<p>You have not added any cover pages yet...</p>';
        return;
    }
    cpages = masterCoverPageList[courseID];
    for(const key in cpages){
        let coverPage = cpages[key];
        const coverPageDiv = document.createElement('div');
        coverPageDiv.style.backgroundColor = '#d0d0d0';
        coverPageDiv.style.padding = '5px';
        coverPageDiv.style.marginBottom = '8px';
        coverPageDiv.style.borderBottom = '1px solid #ccc';
        coverPageDiv.classList.add('context-menu-target');
        coverPageDiv.dataset.itemType = 'coverPage';
        coverPageDiv.dataset.itemID = coverPage.id;
        coverPageDiv.dataset.courseID = courseID;

        coverPageDiv.innerHTML = `
            <p><strong>${coverPage.name}</strong> (Test Number: ${coverPage.testNum}, Date: ${coverPage.date})</p>
            <p>Filename: ${coverPage.file}</p>
            <p>Grading Instructions: ${coverPage.instructions}</p>
        `;

        coverPageContainer.appendChild(coverPageDiv);
    }
}

/**
 * This function updates the templates inside of the template container UI when a template is saved/edited
 * Precondition: valid courseID
 * Postcondition: templates are updated in the template container
*/
function updateTemplates(courseID) {
    const templateContainer = document.getElementById(`templates-${courseID}`);
    templateContainer.innerHTML = ''; // Clear existing content

    if (!masterTemplateList[courseID] || masterTemplateList[courseID].length === 0) {
        templateContainer.innerHTML = '<p>You have not added any templates yet...</p>';
        return;
    }

    let templates = masterTemplateList[courseID];
    for(const key in templates){
        let template = templates[key];
        const templateDiv = document.createElement('div');
        templateDiv.style.backgroundColor = '#d0d0d0';
        templateDiv.style.padding = '5px';
        templateDiv.style.marginBottom = '8px';
        templateDiv.style.borderBottom = '1px solid #ccc';
        templateDiv.classList.add('context-menu-target');
        templateDiv.dataset.itemType = 'template';
        templateDiv.dataset.itemID = template.id;
        templateDiv.dataset.courseID = courseID;

        templateDiv.innerHTML = `
            <p><strong>${template.name}</strong></p>
        `;

        templateContainer.appendChild(templateDiv);
    }
}


    
/**
 * This function is called to update the graphics fields in the editor modal with the available graphics for the course.
 * This version of the function is used when the user is first creating a question.
 * Precondition: valid courseID, attachments exist in the course attachment list
 * Postcondition: graphics fields are updated with the available graphics for the course in the edit modal
*/
function updateGraphicSelectors(courseID) {
    const qGraphicField = document.getElementById('qGraphicField');
    const ansGraphicField = document.getElementById('ansGraphicField');

    qGraphicField.innerHTML = '<option value="" disabled selected>Select a graphic</option>';
    ansGraphicField.innerHTML = '<option value="" disabled selected>Select a graphic</option>';


    for(const key in masterAttachmentList[courseID]){
        let attachment = masterAttachmentList[courseID][key];
        const option = document.createElement('option');
        option.value = attachment.id;
        option.textContent = attachment.url;
        qGraphicField.appendChild(option);

        const ansOption = document.createElement('option');
        ansOption.value = attachment.id;
        ansOption.textContent = attachment.url;
        ansGraphicField.appendChild(ansOption);
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
    const courseID = contextMenu.dataset.courseID;
    const questionType = contextMenu.dataset.questionType;
    const testType = contextMenu.dataset.testType;
    const username = window.username;
    let type =itemType;
    

    let itemToDelete;
    switch(itemType) {
        case 'question':
            type="Question"
            itemToDelete = masterQuestionList[courseID][questionType][String(itemID)];
            break;
        case 'test':
            type="Test"
            console.log("Trying to delete:", {
                courseID,
                testType,
                itemID,
                masterTestList: masterTestList[courseID],
                test: masterTestList[courseID][testType]
            });
            itemToDelete = masterTestList[courseID][testType][String(itemID)];
            break;
        case 'template':
            type = "Template"
            itemToDelete = masterTemplateList[courseID][String(itemID)];
            break;
        case 'coverPage':
            type="CoverPage"
            itemToDelete = masterCoverPageList[courseID][String(itemID)];
            break;
        case 'attachment':
            type="Attachment"
            itemToDelete = masterAttachmentList[courseID][String(itemID)];
            break;
        default:
            console.error('Unknown item type:', type);
            return;
    }
    
    if(itemToDelete.published){
        if(itemToDelete.published==1){
            alert("You cannot delete published items.");
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
                identity: courseID
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Remove the item from the local array
            switch(type) {
                case 'question':
                    delete masterQuestionList[courseID][questionType][itemID];
                    break;
                case 'test':
                    delete masterTestList[courseID][testType][itemID];
                    break;
                case 'template':
                    delete masterTemplateList[courseID][itemID];
                    break;
                case 'coverPage':  // also fix the casing to match `case` block
                    delete masterCoverPageList[courseID][itemID];
                    break;
                case 'attachment':
                    delete masterAttachmentList[courseID][itemID];
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

