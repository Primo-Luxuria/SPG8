/**
 * This closes the context menu when the user clicks anywhere on the document.
 * Precondition: context menu is open
 * Postcondition: context menu is closed
*/
document.addEventListener('click', function () {
    const contextMenu = document.getElementById('contextMenu');
    contextMenu.style.display = 'none';
});



document.addEventListener("DOMContentLoaded", function(){
    reloadData()
});

/**
 * This function grabs the courseSemester selector at the top of the course addition page
 * and updates it to include the current school year rather than a standard set of seasons.
 * For example, in the 2024-2025 school year the values would be Fall 2024, Winter 2024, Spring 2025, Summer 2025
 * Precondition: courseSemester selector exists
 * Postcondition: courseSemester selector should have values equal to the current school year
*/
function updateSemesterOptions() {
    if(!(window.userRole=="teacher")){
        return;
    }
    const select = document.getElementById('courseSemester');
    select.innerHTML = ''; // Clear existing options
    const option = document.createElement('option');

    // Create an initial disabled option in the selector
    option.value = '';
    option.textContent = 'Please Choose a Semester';
    option.disabled = true;
    select.appendChild(option);
    option.selected = true;

    // Get the current date
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1; 

    let N, N_plus_1; 
    if (month < 6) { 
        N = year - 1;
        N_plus_1 = year;
    } else { 
        N = year;
        N_plus_1 = year + 1;
    }

    let semesters;
    if (month >= 6 && month <= 8) {
        semesters = [
            `Fall ${N}`,
            `Winter ${N}`,
            `Spring ${N_plus_1}`,
            `Summer ${N_plus_1}`
        ];
    } else {
        semesters = [
            `Fall ${N}`,
            `Winter ${N}`,
            `Spring ${N_plus_1}`,
            `Summer ${N_plus_1}`
        ];
    }

    // Append semester options to the dropdown
    semesters.forEach(semester => {
        const option = document.createElement('option');
        option.value = semester;
        option.textContent = semester;
        select.appendChild(option);
    });
}



document.addEventListener("DOMContentLoaded", updateSemesterOptions);

/**
 * Opens up a context menu on right click when the user is on a context-menu-target element.
 * This context menu is used to edit or delete items, or to add/view feedback for questions and tests.
 * Precondition: context-menu-target element 
 * Postcondition: context menu is displayed with options to edit or delete the item
*/
document.addEventListener('contextmenu', function (event) {
    const target = event.target.closest('.context-menu-target');
    if (target) {
        event.preventDefault();
        const contextMenu = document.getElementById('contextMenu');
        contextMenu.style.top = `${event.clientY}px`;
        contextMenu.style.left = `${event.clientX}px`;
        contextMenu.style.display = 'block';

        // Store the relevant data in the context menu for later use
        contextMenu.dataset.itemType = target.dataset.itemType;
        contextMenu.dataset.itemID = target.dataset.itemID;
        contextMenu.dataset.identity = target.dataset.identity;
        contextMenu.dataset.questionType = target.dataset.questionType;
        contextMenu.dataset.testType = target.dataset.testType;

        console.log(`Context menu opened for target:`, target);
    } else {
        const contextMenu = document.getElementById('contextMenu');
        contextMenu.style.display = 'none';
    }
});


/**
 * This triggers whenever reloading or exiting the page/tab, and gives a warning 
 * that some of the data may not be saved.
 * Precondition: NA
 * Postcondition: Warning message displayed
*/
window.onbeforeunload = function(event){
    event.returnValue = "Warning! Data entered may not be saved! Are you sure you want to exit?";
};
