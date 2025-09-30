function togglePassword() {
    const pwdField = document.getElementById('password');
    pwdField.type = pwdField.type === 'password' ? 'text' : 'password';
}


// REPLACE the existing function in static/js/script.js with this one.

document.addEventListener('DOMContentLoaded', function() {
    const flashMessagesContainer = document.getElementById('flash-messages');
    if (flashMessagesContainer) {
        const messages = flashMessagesContainer.children;
        
        for (let i = 0; i < messages.length; i++) {
            const category = messages[i].getAttribute('data-category');
            const message = messages[i].getAttribute('data-message');
            
            // --- Create our custom HTML node ---
            const notificationNode = document.createElement('div');
            notificationNode.className = 'toastify-content-custom';

            const iconSpan = document.createElement('span');
            iconSpan.className = 'toast-icon';
            
            const textSpan = document.createElement('span');
            textSpan.textContent = message;

            let backgroundColor;
            
            switch (category) {
                case 'success':
                    iconSpan.textContent = '✅';
                    backgroundColor = "linear-gradient(to right, #81C784, #66BB6A)";
                    break;
                case 'danger':
                    iconSpan.textContent = '❌';
                    backgroundColor = "linear-gradient(to right, #E57373, #EF5350)";
                    break;
                case 'info':
                    iconSpan.textContent = 'ℹ️';
                    backgroundColor = "linear-gradient(to right, #64B5F6, #42A5F5)";
                    break;
                case 'warning':
                    iconSpan.textContent = '⚠️';
                    backgroundColor = "linear-gradient(to right, #FFD54F, #FFCA28)";
                    break;
                default:
                    backgroundColor = "linear-gradient(to right, #6c757d, #5a6268)";
            }

            // Add the icon and text to our custom div
            notificationNode.appendChild(iconSpan);
            notificationNode.appendChild(textSpan);
            
            Toastify({
                node: notificationNode, // Use our custom HTML node
                duration: 5000,
                close: true,
                gravity: "top",
                position: "center",
                stopOnFocus: true,
                className: "toastify-ribbon",
                style: {
                    background: backgroundColor,
                    // Remove padding from the library's default styles
                    padding: '0px' 
                },
                animation: { in: "toastify-in", out: "toastify-out" }
            }).showToast();
        }
    }
});