

function addFeedback() {
    const contextMenu = document.getElementById('contextMenu');
    const itemType = contextMenu.dataset.itemType;
    const itemID = contextMenu.dataset.itemID;
    const identity = contextMenu.dataset.identity;
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
        formContent += `<button class="add-btn" onclick="submitFeedback('${identity}', '${questionType}', ${itemID})">Submit Feedback</button>`;
    } else if (itemType === 'test') {
        formContent += `<button class="save-btn" onclick="submitTestFeedback('${identity}', ${itemID})">Submit Feedback</button>`;
    } else {
        alert("Feedback can only be added to questions and tests.");
        return;
    }
    modalBody.innerHTML = formContent;
    modal.style.display = 'flex';
    setTimeout(() => {
        modal.style.opacity = '1';
    }, 10);
   

        
    
}

function submitFeedback(identity, questionType, questionID) {
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

    const question = masterQuestionList[identity][questionType][questionID];
    if (!question.feedback) {
        question.feedback = [];
    }
    question.feedback.push(feedback);
    if(window.userRole=="teacher"){
        saveData("question",question,identity);
    }else{
        saveData("question",question,{}, identity);
    }
    viewFeedback();
    
}

function submitTestFeedback(identity, testID) {
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

    const test = masterTestList[identity]['drafts'][testID] || masterTestList[identity]['published'][testID];
    if (!test.feedback) {
        test.feedback = [];
    }
    test.feedback.push(feedback);
    if(window.userRole=="teacher"){
        saveData("test",test,identity);
    }else{
        saveData("test",test,{}, identity);
    }
    viewFeedback();
}


function viewFeedback() {
    const contextMenu = document.getElementById('contextMenu');
    const itemType = contextMenu.dataset.itemType;
    const itemID = contextMenu.dataset.itemID;
    const identity = contextMenu.dataset.identity;
    const questionType = contextMenu.dataset.questionType;
    if (itemType === 'question') {
        viewQuestionFeedback(identity, questionType, itemID);
    } else if (itemType === 'test') {
        viewTestFeedback(identity, itemID);
    } else {
        alert("Feedback can only be viewed for questions and tests.");
    }
}

function viewQuestionFeedback(identity, questionType, questionIndex) {
    const question = masterQuestionList[identity][questionType][questionIndex];

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
                    <button class="add-btn" onclick="submitResponse('${identity}', '${questionType}', ${questionIndex}, ${feedbackIndex})">Submit Response</button>
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


function viewTestFeedback(identity, testIndex) {
    const test = masterTestList[identity]['drafts'][testIndex] || masterTestList[identity]['published'][testIndex];

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
                    <button class="add-btn" onclick="submitTestResponse('${identity}', ${testIndex}, ${feedbackIndex})">Submit Response</button>
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


function submitResponse(identity, questionType, questionIndex, feedbackIndex) {
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

    const question = masterQuestionList[identity][questionType][questionIndex];
    question.feedback[feedbackIndex].responses.push(response);
    if(window.userRole=="teacher"){
        saveData("question",question,identity);
    }else{
        saveData("question",question,{}, identity);
    }
    viewQuestionFeedback(identity, questionType, questionIndex);
}


function submitTestResponse(identity, testIndex, feedbackIndex) {
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

    const test = masterTestList[identity]['drafts'][testIndex] || masterTestList[identity]['published'][testIndex];
    test.feedback[feedbackIndex].responses.push(response);
    if(window.userRole=="teacher"){
        saveData("test",test,identity);
    }else{
        saveData("test",test,{}, identity);
    }
    viewTestFeedback(identity, testIndex);
}