<?php
// File to store user data
$file = 'users.txt';

// Function to sanitize user inputs
function sanitizeInput($data) {
    return htmlspecialchars(stripslashes(trim($data)));
}

// Check if the form is submitted
if ($_SERVER["REQUEST_METHOD"] === "POST") {
    // Collect and sanitize inputs
    $username = sanitizeInput($_POST['username']);
    $password = sanitizeInput($_POST['password']);
    $passwordconfirm = sanitizeInput($_POST['passwordconfirm']);
    $role = sanitizeInput($_POST['role']);

    // Basic validation
    if (empty($username) || empty($password) || empty($passwordconfirm) || empty($role)) {
        die("All fields are required. Please go back and fill out the form.");
    }

    if ($password !== $passwordconfirm) {
        die("Passwords do not match. Please go back and try again.");
    }

    // Check if the user already exists
    if (file_exists($file)) {
        $users = file($file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        foreach ($users as $user) {
            list($savedUsername) = explode('|', $user);
            if ($savedUsername === $username) {
                die("Username already exists. Please choose a different username.");
            }
        }
    }

    // Save the new user to the file
    $hashedPassword = password_hash($password, PASSWORD_BCRYPT); // Securely hash the password
    $userData = "$username|$hashedPassword|$role\n";
    file_put_contents($file, $userData, FILE_APPEND);

    echo "Sign-up successful! You can now log in.";
} else {
    echo "Invalid request.";
}
?>
