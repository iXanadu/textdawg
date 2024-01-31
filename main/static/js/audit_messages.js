$(document).ready(function() {
    // Function to load marked messages from the server
    function loadMarkedMessages() {
        $.ajax({
            url: '/main/audit/get_messages/',
            method: 'GET',
            dataType: 'json',
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
            success: function(data) {
                var messagesTable = $('#auditTable tbody');
                messagesTable.empty(); // Clear existing rows
                var parsedData = JSON.parse(data); // Parse the JSON string
                parsedData.forEach(function(message) {
                    console.log("Load Messages-message(", message, ")");
                    var resolvedStatus = message.resolved ? '✓' : '';
                    var row = $('<tr>').addClass(message.resolved ? 'resolved-message' : '');
                    var checkbox = $('<input>').attr({
                        type: "checkbox",
                        class: "marked-message-checkbox",
                        value: message.pk
                    }).click(function(event) {
                        // Stop the event from propagating to parent elements
                        event.stopPropagation();
                    });

                    row.append($('<td>').append(checkbox));
                    // row.append($('<td>').html('<input type="checkbox" class="marked-message-checkbox" value="' + message.pk + '">'));
                    row.append($('<td>').text(new Date(message.created_at).toLocaleString('en-US', { year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })));
                    row.append($('<td>').text(message.comment.substring(0, 30)));
                    row.append($('<td>').text(message.server_message.substring(0, 30)));
                    row.append($('<td>').text(resolvedStatus));

                    row.click(function() {
                        showModal(message.pk);
                    });

                    messagesTable.append(row);
                });

            },
            error: function() {
                alert('Error loading marked messages. Please try again.');
            }
        });
    }

    // Function to display the modal with message details
   function showModal(messageId) {
        $.ajax({
            url: `/main/audit/message/${messageId}/`,
            method: 'GET',
            dataType: 'json',
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
            success: function(data) {
                // Clear existing content in the modal body
                var modalBody = $('#messageDetailModal .modal-body');
                modalBody.empty();
                console.log("showModal data: ", data)
                // Append user message
                var userMessageDiv = $('<div>').addClass('message user-message').text("User: " + data.preceding_user_message);
                modalBody.append(userMessageDiv);

                // Append server message
                var serverMessageDiv = $('<div>').addClass('message server-message').text("Server: " + data.server_message);
                modalBody.append(serverMessageDiv);

                $('#resolveButton').data('message-id', messageId);
                $('#messageDetailModal').modal('show');
            },
            error: function() {
                alert('Error fetching message details. Please try again.');
            }
        });
    }

// Event handler for the delete button
	$('#deleteAuditMsgBtn').click(function() {
		var selectedMessages = $('.marked-message-checkbox:checked').map(function() {
			return $(this).val(); // Assuming the value of each checkbox is the prompt's ID
		}).get();

		if (selectedMessages.length === 0) {
			alert("Please select at least one prompt to delete.");
			return;
		}

		var confirmDelete = confirm("Are you sure you want to delete the selected messages");
		if (confirmDelete) {
			// Proceed with deletion
			$.ajax({
				url: '/main/audit/delete_messages/',
				method: 'POST',
				data: JSON.stringify({ 'messageIds': selectedMessages }),
				contentType: "application/json; charset=utf-8",
				dataType: 'json',
				beforeSend: function(xhr) {
					xhr.setRequestHeader("X-CSRFToken", csrftoken);
				},
				success: function(response) {
					// Reload or update prompts list
					loadMarkedMessages();
				},
				error: function() {
					alert('Error deleting nessages. Please try again.');
				}
			});
		}
	});


    $('#resolveButton').click(function() {
        var messageId = $(this).data('message-id');
        $.ajax({
            url: '/main/audit/resolve_message/',
            method: 'POST',
            data: {
                message_id: messageId,
                resolved_status: true
            },
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
            success: function() {
                // Close the modal and then reload the messages list
                $('#messageDetailModal').modal('hide');
                loadMarkedMessages();
            },
            error: function() {
                alert('Error resolving message. Please try again.');
            }
        });
    });



    // Initial load of marked messages
    loadMarkedMessages();
});
