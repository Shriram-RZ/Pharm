// Initialize EmailJS with your User ID
emailjs.init("SA94YAu4DcoUJGVba");

// Function to send the checkout email
function sendCheckoutEmail(userEmail, total_price, cart_products) {
    // Check if cart_products is not null and is an array
    if (Array.isArray(cart_products) && cart_products.length > 0) {
        // Prepare email data
        var emailData = {
            user_email: userEmail,
            total_price: total_price,
            cart_product_name: cart_products.map(product => product.name || ''),
            cart_product_description: cart_products.map(product => product.description || ''),
            cart_product_price: cart_products.map(product => product.price || '')
        };

        // Send email using EmailJS
        emailjs.send("service_pq92lnd", "template_xw6lmxn", emailData)
            .then(function(response) {
                console.log("Email sent:", response);
                // Handle success - display a success message
                alert("Email sent successfully!");
            }, function(error) {
                console.error("Email sending failed:", error);
                // Handle error - display an error message
                alert("Failed to send email. Please try again later.");
            });
    } else {
        // Handle invalid or empty cart_products
        console.error("Invalid cart products data.");
        alert("Failed to send email. Invalid or empty cart products.");
    }
}

// Add event listener when DOM content is loaded
document.addEventListener("DOMContentLoaded", function() {
    var checkoutBtn = document.getElementById("checkout-btn");
    var userEmailInput = document.getElementById("user-email");

    checkoutBtn.addEventListener("click", function() {
        var userEmail = userEmailInput.value;
        var cart_products_str = '{{ cart_products | tojson }}';

        // Parse the JSON string to an array
        var cart_products = [];
        try {
            cart_products = JSON.parse(cart_products_str);
        } catch (error) {
            console.error("Error parsing cart products JSON:", error);
            alert("Error parsing cart products data. Please try again.");
            return; // Exit early if parsing fails
        }

        // Now you can use total_price, cart_products, and userEmail in your sendCheckoutEmail function
        sendCheckoutEmail(userEmail, total_price, cart_products);
    });
});