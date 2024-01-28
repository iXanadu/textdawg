$(document).ready(function() {
    $("#send-button").click(sendMessage);
    $("#user-input").keypress(handleKeyPress);

    function sendMessage() {
        var phoneNumber = $("#phone-number").val().trim();
        var userInput = $("#user-input").val().trim();

        if (!phoneNumber || !userInput) {
            alert("Both phone number and message are required.");
            return;
        }

        // Format and append the user's message to chat display
        appendMessage(userInput, 'user-message');

        // Format the phone number for backend compatibility
        if (!phoneNumber.startsWith('+1')) {
            phoneNumber = '+1' + phoneNumber;
        }

        // AJAX request to the backend
        $.ajax({
            url: '/webhook/smsweb_receiver/', // Ensure this is the correct endpoint
            type: 'POST',
            contentType: 'application/x-www-form-urlencoded',
            data: constructDataObject(phoneNumber, userInput),
            success: function(response) {
                console.log(response)
                appendServerMessage(response.output, response.userId,
                    response.serverMsgId, response.previousMsgId);
            },
            error: function(xhr, status, error) {
                console.error("Error occurred:", status, error);
                alert("Error sending message: " + error);
            }
        });

        $("#user-input").val(''); // Clear input field after sending
    }

    function appendServerMessage(message, userId, serverMsgId, previousMsgId) {
    var markButton = $("<button>")
        .addClass('mark-message-btn btn btn-secondary btn-sm')
        .text('Mark')
        .attr('data-userid', userId)
        .attr('data-servermsgid', serverMsgId)
        .attr('data-previousmsgid', previousMsgId)
        .click(function() {
            markSMSMessage(serverMsgId, previousMsgId);
        });

    var messageDiv = $("<div>")
        .addClass('message response-message')
        .append(markButton)
        .append($("<span>").text(message));

    $("#chat-display").append(messageDiv).scrollTop($("#chat-display")[0].scrollHeight);
}


    function handleKeyPress(event) {
        if (event.keyCode === 13) {  // Enter key
            event.preventDefault();
            sendMessage();
        }
    }

    function appendMessage(message, className) {
        var messageDiv = $("<div>").addClass('message').addClass(className).text(message);
        $("#chat-display").append(messageDiv).scrollTop($("#chat-display")[0].scrollHeight);
    }

    function constructDataObject(phoneNumber, userInput) {
        return {
            // Original data parameters
            ToCountry: 'US',
            ToState: 'VA',
            SmsMessageSid: generateRandomID(34),
            NumMedia: '0',
            ToCity: 'CHESAPEAKE',
            FromZip: '23708',
            SmsSid: generateRandomID(34),
            FromState: 'VA',
            SmsStatus: 'received',
            FromCity: 'NORFOLK',
            Body: userInput,
            FromCountry: 'US',
            To: '+17579083929',
            ToZip: '23320',
            NumSegments: '1',
            MessageSid: generateRandomID(34),
            AccountSid: 'AC7f9ebf704092eb721560e3755b41c9cd',
            From: phoneNumber,
            ApiVersion: '2010-04-01'
        };
    }

    function generateRandomID(length) {
        var result = '';
        var characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        var charactersLength = characters.length;
        for (var i = 0; i < length; i++) {
            result += characters.charAt(Math.floor(Math.random() * charactersLength));
        }
        return result;
    }

    function markSMSMessage(messageId, precedingMessageId) {
        // Open the modal
        $("#commentModal").show();

        // When the submit button is clicked
        $("#submitComment").off('click').on('click', function() {
            var userComment = $("#userComment").val().trim();
            if (userComment) {
                // AJAX call to send data
                $.ajax({
                    url: '/webhook/api/mark_sms_message/',
                    method: 'POST',
                    data: {
                        'message_id': messageId,
                        'previousmsgid': precedingMessageId,
                        'comment': userComment
                    },
                    success: function(response) {
                        console.log("SMS message marked successfully:", response);
                        $("#commentModal").hide(); // Close the modal
                        $("#userComment").val(''); // Clear the textarea
                    },
                    error: function(error) {
                        console.error("Error marking SMS message:", error);
                    }
                });
            }
        });
    }

// Close modal on clicking the 'X'
$(".close").click(function() {
    $("#commentModal").hide();
});


});
