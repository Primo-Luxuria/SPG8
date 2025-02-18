<?php
// login_handler.php
ini_set('display_errors', 1);
error_reporting(E_ALL);

$file = 'users.txt';

function sanitizeInput($data) {
    return htmlspecialchars(stripslashes(trim($data)));
}

header('Content-Type: application/json'); // Set response type to JSON

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $username = sanitizeInput($_POST['username']);
    $password = sanitizeInput($_POST['password']);

    if (empty($username) || empty($password)) {
        echo json_encode(['status' => 'error', 'message' => 'Both username and password are required.']);
        exit;
    }

    if (file_exists($file)) {
        $users = file($file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        foreach ($users as $user) {
            list($savedUsername, $savedPasswordHash, $role) = explode('|', $user);

            // Validate username and password
            if ($savedUsername === $username && password_verify($password, $savedPasswordHash)) {
                echo json_encode(['status' => 'success', 'role' => strtolower($role)]);
                exit;
            }
        }
    }

    // If no match is found
    echo json_encode(['status' => 'error', 'message' => 'Invalid username or password.']);
} else {
    echo json_encode(['status' => 'error', 'message' => 'Invalid request.']);
}
?>
