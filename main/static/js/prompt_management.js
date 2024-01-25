jQuery(document).ready(function($) {

	var currentSortColumn = 'key'
	var currentSortDirection = 'asc'; // 'asc' or 'desc'

    $('#sortKey').click(function() {
        sortTable('key');
    });

    $('#sortPromptText').click(function() {
        sortTable('prompt_text');
    });


    // Function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    // Function to load prompts from the server and display them
    function loadPrompts() {
        $.ajax({
            url: '/main/prompts/list',
            method: 'GET',
            data: {
                sort_column: currentSortColumn,
                sort_direction: currentSortDirection
            },
            dataType: 'json',
            success: function(data) {
                var promptsTable = $('#promptsTable tbody');
                promptsTable.empty();

                data.forEach(function(prompt) {
                    var row = $('<tr class="editable-prompt" data-id="' + prompt.id + '" data-key="' + prompt.key + '" data-prompt_text="' + prompt.prompt_text + '" data-description="' + prompt.description + '" data-category="' + prompt.category + '" data-isactive="' + prompt.isActive + '" data-version="' + prompt.version + '">');
		    row.append($('<td>').html('<input type="checkbox" class="prompt-select-checkbox" value="' + prompt.id + '">'));
                    row.append($('<td>').text(prompt.key));
                    row.append($('<td>').text(prompt.prompt_text));
                    promptsTable.append(row);
                });
            },
            error: function() {
                alert('Error loading prompts. Please try again.');
            }
        });
    }

    // Initial load of prompts
    loadPrompts();

	$('#addPromptBtn').click(function() {
	    $('#addPromptModalLabel').text('Add New Prompt');
	    $('#modalSubmitButton').text('Add').data('mode', 'add').removeData('promptId');  // Ensure 'promptId' data is cleared
	    $('#addPromptForm').trigger('reset');
	    $('#addPromptModal').modal('show');
	});

    // Event listener for opening the modal in 'Edit' mode
    $(document).on('click', '.editable-prompt', function() {
        var promptData = $(this).data();
	$('#addPromptModalLabel').text('Edit Prompt');
	$('#modalSubmitButton').text('Save').data('mode', 'edit').data('promptId', promptData.id);
        $('#newPromptKey').val(promptData.key);
        $('#newPromptText').val(promptData.prompt_text);
        $('#newPromptDescription').val(promptData.description);
        $('#newPromptCategory').val(promptData.category);
        $('#newPromptIsActive').prop('checked', promptData.isactive);
        $('#newPromptVersion').val(promptData.version);
        $('#addPromptModal').modal('show');
    });
    // Prevent checkbox click from triggering row click
    $(document).on('click', '.prompt-select-checkbox', function(event) {
	    event.stopPropagation();
    });

		// Event handler for the 'Select All' checkbox
		$('#selectAllPrompts').click(function() {
			var isChecked = $(this).is(':checked');
			$('.prompt-select-checkbox').prop('checked', isChecked);
		});



    // Handle Form Submission for Add and Edit
    $('#addPromptForm').submit(function(event) {
        event.preventDefault();
	var mode = $('#modalSubmitButton').data('mode');
	var promptId = mode === 'edit' ? $('#modalSubmitButton').data('promptId') : '';
	var url = mode === 'add' ? '/main/prompts/add/' : '/main/prompts/edit/' + promptId + '/';

        const promptData = {
            key: $('#newPromptKey').val(),
            prompt_text: $('#newPromptText').val(),
            description: $('#newPromptDescription').val(),
            category: $('#newPromptCategory').val(),
            isactive: $('#newPromptIsActive').is(':checked'),
            version: $('#newPromptVersion').val()
        };

        $.ajax({
            url: url,
            method: 'POST',
            data: JSON.stringify(promptData),
            contentType: "application/json; charset=utf-8",
            dataType: 'json',
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
            success: function(response) {
                $('#addPromptModal').modal('hide');
                loadPrompts();
            },
            error: function() {
                alert('Error processing prompt. Please try again.');
            }
        });
    });
	// Event handler for the delete button
	$('#deletePromptsBtn').click(function() {
		var selectedPrompts = $('.prompt-select-checkbox:checked').map(function() {
			return $(this).val(); // Assuming the value of each checkbox is the prompt's ID
		}).get();

		if (selectedPrompts.length === 0) {
			alert("Please select at least one prompt to delete.");
			return;
		}

		var confirmDelete = confirm("Are you sure you want to delete the selected prompts?");
		if (confirmDelete) {
			// Proceed with deletion
			$.ajax({
				url: '/main/prompts/delete/',
				method: 'POST',
				data: JSON.stringify({ 'promptIds': selectedPrompts }),
				contentType: "application/json; charset=utf-8",
				dataType: 'json',
				beforeSend: function(xhr) {
					xhr.setRequestHeader("X-CSRFToken", csrftoken);
				},
				success: function(response) {
					// Reload or update prompts list
					loadPrompts();
				},
				error: function() {
					alert('Error deleting prompts. Please try again.');
				}
			});
		}
	});


	function sortTable(columnName) {
	    if (currentSortColumn === columnName) {
		// Flip the direction
				currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
	    } else {
		// New column, start with ascending
				currentSortColumn = columnName;
				currentSortDirection = 'asc';
	    }
	    loadPrompts();
	}





});



