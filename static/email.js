// Initialize EmailJS with your User ID
emailjs.init("SA94YAu4DcoUJGVba");

// Function to send the checkout email
function sendCheckoutEmail(userEmail, total_price, cart_products) {
    // Prepare email data
    var emailData = {
        user_email: userEmail,
        total_price: total_price,
        cart_product_name: cart_products.map(product => product.name),
        cart_product_description: cart_products.map(product => product.description),
        cart_product_price: cart_products.map(product => product.price)
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
}

// Wait for the DOM to be fully loaded
document.addEventListener("DOMContentLoaded", function() {
    // Get the checkout button
    var checkoutBtn = document.getElementById("checkout-btn");

    // Add a click event listener to the checkout button
    checkoutBtn.addEventListener("click", function() {
        // Get the user's email from the form
        var userEmail = document.getElementById("user-email").value;

        // Call the sendCheckoutEmail function with the user's email and other data
        sendCheckoutEmail(userEmail, total_price, cart_products);
    });
});
