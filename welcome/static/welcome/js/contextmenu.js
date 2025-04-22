

/**
 * This function opens up the modal to produce a feedback form
 * It allows the user to leave a rating out of five stars, the average score, average time taken, and comments
 * Precondition: valid courseID, questionType, questionIndex
 * Postcondition: feedback form is opened 
*/
function addFeedback() {
    const contextMenu = document.getElementById('contextMenu');
    const itemType = contextMenu.dataset.itemType;
    const itemID = contextMenu.dataset.itemID;
    const courseID = contextMenu.dataset.courseID;
    const questionType = contextMenu.dataset.questionType;

    // Open the feedback modal and populate it with the feedback form
    const modal = document.getElementById('editModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    modalTitle.innerText = 'Add Feedback';

    let formContent = `
        <label>Rating (1-5):</label><br/>
        <input type="number" id="feedbackRating" min="1" max="5"><br><br>
        <label>Class Average Score:</label><br/>
        <input type="number" id="feedbackAverageScore" min="0" step=0.01><br><br>
        <label>Class Average Time Taken (in Minutes):</label><br/>
        <input type="number" id="feedbackAverageTime" min="0" step=0.01><br><br>
        <label>Comments:</label><br/>
        <textarea id="feedbackComments" rows="4"></textarea><br><br>
        `;

    if (itemType === 'question') {
        formContent += `<button class="add-btn" onclick="submitFeedback('${courseID}', '${questionType}', ${itemID})">Submit Feedback</button>`;
    } else if (itemType === 'test') {
        formContent += `<button class="save-btn" onclick="submitTestFeedback('${courseID}', ${itemID})">Submit Feedback</button>`;
    } else {
        alert("Feedback can only be added to questions and tests.");
    }
    modalBody.innerHTML = formContent;
    modal.style.display = 'flex';
    setTimeout(() => {
        modal.style.opacity = '1';
    }, 10);
   

        
    
}

/**
 * This function is called to submit feedback for a question
 * Precondition: valid courseID, questionType, questionIndex
 * Postcondition: feedback is submitted and saved in the master list
*/
function submitFeedback(courseID, questionType, questionID) {
    const rating = parseInt(document.getElementById('feedbackRating').value);
    const averageScore = parseFloat(document.getElementById('feedbackAverageScore').value);
    const comments = document.getElementById('feedbackComments').value.trim();
    const time = parseFloat(document.getElementById('feedbackAverageTime').value);

    if (isNaN(rating) || rating < 1 || rating > 5) {
        alert("Please enter a valid rating between 1 and 5.");
        return;
    }
    if (isNaN(averageScore) || averageScore < 0) {
        alert("Please enter a valid, non-negative class average score.");
        return;
    }
    if (!comments) {
        alert("Comments are required.");
        return;
    }
    if(!time){
        alert("Average time is required! Just put 0 for less than a minute, and estimate otherwise!");
        return;
    }
    const username = window.username;
    const feedback = {
        username: username, 
        rating: rating,
        averageScore: averageScore,
        comments: comments,
        time: time,
        date: new Date().toLocaleString(),
        responses: []
    };

    const question = masterQuestionList[courseID][questionType][questionID];
    if (!question.feedback) {
        question.feedback = [];
    }
    question.feedback.push(feedback);

    closeModal();
    viewQuestionFeedback(courseID, questionType, questionID);
}

/**
 * This function is called to submit feedback for a test
 * Precondition: valid courseID, testIndex
 * Postcondition: feedback is submitted and saved in the master list
*/
function submitTestFeedback(courseID, testID) {
    const rating = parseInt(document.getElementById('feedbackRating').value);
    const averageScore = parseFloat(document.getElementById('feedbackAverageScore').value);
    const comments = document.getElementById('feedbackComments').value.trim();
    const time = parseFloat(document.getElementById('feedbackAverageTime').value);

    if (isNaN(rating) || rating < 1 || rating > 5) {
        alert("Please enter a valid rating between 1 and 5.");
        return;
    }
    if (isNaN(averageScore) || averageScore < 0) {
        alert("Please enter a valid, non-negative class average score.");
        return;
    }
    if (!comments) {
        alert("Comments are required.");
        return;
    }
    if(!time){
        alert("Average time is required! Just put 0 for less than a minute, and estimate otherwise!");
        return;
    }

    const username = window.username;
    const feedback = {
        username: username, 
        rating: rating,
        averageScore: averageScore,
        comments: comments,
        time:time,
        date: new Date().toLocaleString(),
        responses: []
    };

    const test = masterTestList[courseID]['drafts'][testID] || masterTestList[courseID]['published'][testID];
    if (!test.feedback) {
        test.feedback = [];
    }
    test.feedback.push(feedback);

    closeModal();
    viewTestFeedback(courseID, testID);
}

/**
 * This function is called to view feedback for a question or test
 * It opens up an amazon review-like page
 * Precondition: valid courseID, questionType (for questions), questionIndex stored in context menu
 * Postcondition: feedback is displayed in the modal
*/
function viewFeedback() {
    const contextMenu = document.getElementById('contextMenu');
    const itemType = contextMenu.dataset.itemType;
    const itemID = contextMenu.dataset.itemID;
    const courseID = contextMenu.dataset.courseID;
    const questionType = contextMenu.dataset.questionType;
    if (itemType === 'question') {
        viewQuestionFeedback(courseID, questionType, itemID);
    } else if (itemType === 'test') {
        viewTestFeedback(courseID, itemID);
    } else {
        alert("Feedback can only be viewed for questions and tests.");
    }
}

/**
 * This function is called to view the feedback to questions, it is called by viewFeedback
 * Precondition: valid courseID, questionType, questionIndex
 * Postcondition: feedback is displayed in the modal
*/
function viewQuestionFeedback(courseID, questionType, questionIndex) {
    const question = masterQuestionList[courseID][questionType][questionIndex];

    // Open the feedback modal and populate it with the feedback reviews
    const modal = document.getElementById('editModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    modalTitle.innerText = 'View Feedback';

    let feedbackContent = '<h3>Feedback Reviews:</h3>';
    if (!question.feedback || question.feedback.length === 0) {
        feedbackContent += '<p>No feedback available for this question.</p>';
    } else {
        question.feedback.forEach((feedback, feedbackIndex) => {
            feedbackContent += `
                <div style="border-bottom: 1px solid #ccc; padding: 10px;">
                    <p><strong>${feedback.username}</strong> (${feedback.date})</p>
                    <p>Rating: ${feedback.rating}/5</p>
                    <p>Class Average Score: ${feedback.averageScore}/${question.score}</p>
                    <p>Comments: ${feedback.comments}</p>
                    <p>Time: ${feedback.time}</p>
                    <div id="responses-${feedbackIndex}">
                        ${feedback.responses.map(response => `
                            <div style="margin-left: 20px; border-top: 1px solid #ccc; padding-top: 10px;">
                                <p><strong>${response.username}</strong> (${response.date})</p>
                                <p>${response.text}</p>
                            </div>
                        `).join('')}
                    </div>
                    <textarea id="responseText-${feedbackIndex}" rows="2" placeholder="Add a response..."></textarea><br>
                    <button class="add-btn" onclick="submitResponse('${courseID}', '${questionType}', ${questionIndex}, ${feedbackIndex})">Submit Response</button>
                </div>
            `;
        });
    }

    modalBody.innerHTML = feedbackContent;
    modal.style.display = 'flex';
    setTimeout(() => {
        modal.style.opacity = '1';
    }, 10);
}

/**
 * This function is called to view the feedback to tests, it is called by viewFeedback
 * Precondition: valid courseID, testIndex
 * Postcondition: feedback is displayed in the modal
*/
function viewTestFeedback(courseID, testIndex) {
    const test = masterTestList[courseID]['drafts'][testIndex] || masterTestList[courseID]['published'][testIndex];

    // Open the feedback modal and populate it with the feedback reviews
    const modal = document.getElementById('editModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    modalTitle.innerText = 'View Feedback';

    let feedbackContent = '<h3>Feedback Reviews:</h3>';
    if (!test.feedback || test.feedback.length === 0) {
        feedbackContent += '<p>No feedback available for this test.</p>';
    } else {
        test.feedback.forEach((feedback, feedbackIndex) => {
            feedbackContent += `
                <div style="border-bottom: 1px solid #ccc; padding: 10px;">
                    <p><strong>${feedback.username}</strong> (${feedback.date})</p>
                    <p>Rating: ${feedback.rating}/5</p>
                    <p>Class Average Score: ${feedback.averageScore}</p>
                    <p>Comments: ${feedback.comments}</p>
                    <p>Time: ${feedback.time}</p>
                    <div id="responses-${feedbackIndex}">
                        ${feedback.responses.map(response => `
                            <div style="margin-left: 20px; border-top: 1px solid #ccc; padding-top: 10px;">
                                <p><strong>${response.username}</strong> (${response.date})</p>
                                <p>${response.text}</p>
                            </div>
                        `).join('')}
                    </div>
                    <textarea id="responseText-${feedbackIndex}" rows="2" placeholder="Add a response..."></textarea><br>
                    <button class="add-btn" onclick="submitTestResponse('${courseID}', ${testIndex}, ${feedbackIndex})">Submit Response</button>
                </div>
            `;
        });
    }

    modalBody.innerHTML = feedbackContent;
    modal.style.display = 'flex';
    setTimeout(() => {
        modal.style.opacity = '1';
    }, 10);
}

/**
 * This function is called to submit response inside of the feedback modal
 * Precondition: valid courseID, questionType, questionIndex, feedbackIndex
 * Postcondition: response is submitted and saved in the master list, displayed on the review page
*/
function submitResponse(courseID, questionType, questionIndex, feedbackIndex) {
    const responseText = document.getElementById(`responseText-${feedbackIndex}`).value.trim();

    if (!responseText) {
        alert("Response text is required.");
        return;
    }

    const username = window.username;
    const response = {
        username: username, 
        text: responseText,
        date: new Date().toLocaleString()
    };

    const question = masterQuestionList[courseID][questionType][questionIndex];
    question.feedback[feedbackIndex].responses.push(response);

    viewQuestionFeedback(courseID, questionType, questionIndex);
}

/**
 * This function is called to submit response inside of the feedback modal for tests
 * Precondition: valid courseID, testIndex, feedbackIndex
 * Postcondition: response is submitted and saved in the master list, displayed on the review page
*/
function submitTestResponse(courseID, testIndex, feedbackIndex) {
    const responseText = document.getElementById(`responseText-${feedbackIndex}`).value.trim();

    if (!responseText) {
        alert("Response text is required.");
        return;
    }

    const username = window.username;
    const response = {
        username: username, 
        text: responseText,
        date: new Date().toLocaleString()
    };

    const test = masterTestList[courseID]['drafts'][testIndex] || masterTestList[courseID]['published'][testIndex];
    test.feedback[feedbackIndex].responses.push(response);

    viewTestFeedback(courseID, testIndex);
}