jQuery(document).ready(function ($) {

    let currentSortColumn = 'key';
    let currentSortDirection = 'asc'; // 'asc' or 'desc'
    let originalVersion = 0; // To store the original version of the prompt being edited
    modelPermissions = fetchModelPermissions('OpenAIPrompt');
    $('#sortKey').click(function () {
        sortTable('key');
    });

    $('#sortPromptText').click(function () {
        sortTable('prompt_text');
    });

    $('#selectAllPrompts').click(function () {
        let isChecked = $(this).is(':checked');
        $('.prompt-select-checkbox').prop('checked', isChecked);
    });

    // Function to load prompts from the server and display them
    function loadPrompts() {
        $.ajax({
            url: '/main/prompts/list',
            method: 'GET',
            dataType: 'json',
            data: {
                sort_column: currentSortColumn,
                sort_direction: currentSortDirection
            },
            success: function (response) {
                let promptsTable = $('#promptsTable tbody');
                promptsTable.empty();

                let data = JSON.parse(response); // Parse the serialized data

                data.forEach(function (item) {
                    let prompt = item.fields; // Access the fields of the prompt
                    let truncatedPromptText = prompt.prompt_text.length > 50 ? prompt.prompt_text.substring(0, 47) + '...' : prompt.prompt_text;
                    let isActiveIndicator = prompt.isActive ? "<strong>*" + prompt.key + "</strong>" : prompt.key; // Making the key bold and adding * if active
                    let Version = prompt.version
                    let row = $('<tr class="editable-prompt" data-id="' + item.pk + '" data-key="' + prompt.key + '" data-full_prompt_text="' + prompt.prompt_text + '" data-truncated_text="' + truncatedPromptText + '" data-description="' + prompt.description + '" data-category="' + prompt.category + '" data-isactive="' + prompt.isActive + '" data-version="' + prompt.version + '">');
                    row.append($('<td>').html('<input type="checkbox" class="prompt-select-checkbox" value="' + item.pk + '">'));
                    row.append($('<td>').html(isActiveIndicator)); // Changed .text() to .html() to render HTML
                    row.append($('<td>').text(Version)); // Display truncated text
                    row.append($('<td>').text(truncatedPromptText)); // Display truncated text
                    promptsTable.append(row);
                });
            },
            error: function () {
                alert('Error loading prompts. Please try again.');
            }
        });
    }

    // Initial load of prompts
    loadPrompts();

    $('#addPromptBtn').click(function () {
        let isActive = $('#newPromptIsActive').is(':checked');

        $('#addPromptModalLabel').text('Add New Prompt');
        if (check_perm('OpenAIPrompt', 'change'))
            $('#modalSubmitButton').text('Add').data('mode', 'add').removeData('promptId');  // Ensure 'promptId' data is cleared
        $('#addPromptForm').trigger('reset');
        $('#addPromptModal').modal('show');
    });

    // Prevent checkbox click from triggering row click
    $(document).on('click', '.prompt-select-checkbox', function (event) {
        event.stopPropagation();
    });

    // Event listener for opening the modal in 'Edit' mode
    $(document).on('click', '.editable-prompt', function () {
        let promptData = $(this).data();
        let id = $(this).data('id');
        fetchFullText(id); // Fetch full text and store original version
        $('#addPromptModalLabel').text('Edit Prompt');
        if (check_perm('OpenAIPrompt', 'change')) {
            $('#modalSubmitButton').text('Save').data('mode', 'edit').data('promptId', promptData.id);
        }
        $('#newPromptKey').val(promptData.key);
        $('#newPromptDescription').val(promptData.description);
        $('#newPromptCategory').val(promptData.category);
        $('#newPromptIsActive').prop('checked', promptData.isactive);
        $('#newPromptVersion').val(promptData.version);
        originalVersion = promptData.version; // Store the original version
        $('#addPromptModal').modal('show');
    });

    // Function to fetch full prompt text
    function fetchFullText(id) {
        $.ajax({
            url: '/main/prompts/get_full_prompt/' + id,
            method: 'GET',
            success: function (response) {
                $('#newPromptText').val(response.prompt_text);
            },
            error: function () {
                console.error("Error fetching full text");
            }
        });
    }

    // Handle Form Submission for Add, Edit, and New Version
    $('#addPromptForm').submit(function (event) {
        event.preventDefault();
        let mode = "";
        let promptId = 0;
        if (check_perm('OpenAIPrompt', 'change')) {
            mode = $('#modalSubmitButton').data('mode');
            promptId = mode === 'edit' ? $('#modalSubmitButton').data('promptId') : '';
        }
        let currentVersion = parseInt($('#newPromptVersion').val());

        let url = (mode === 'add' || currentVersion !== originalVersion) ? '/main/prompts/add/' : '/main/prompts/edit/' + promptId + '/';
        const promptData = {
            key: $('#newPromptKey').val(),
            version: currentVersion,
            prompt_text: $('#newPromptText').val(),
            description: $('#newPromptDescription').val(),
            category: $('#newPromptCategory').val(),
            is_active: $('#newPromptIsActive').is(':checked'),
        };

        $.ajax({
            url: url,
            method: 'POST',
            data: JSON.stringify(promptData),
            contentType: "application/json; charset=utf-8",
            dataType: 'json',
            beforeSend: function (xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
            success: function (response) {
                $('#addPromptModal').modal('hide');
                loadPrompts();
            },
            error: function () {
                alert('Error processing prompt. Please try again.');
            }
        });
    });

    // Event handler for the delete button
    $('#deletePromptsBtn').click(function () {
        let selectedPrompts = $('.prompt-select-checkbox:checked').map(function () {
            return $(this).val(); // Assuming the value of each checkbox is the prompt's ID
        }).get();

        if (selectedPrompts.length === 0) {
            alert("Please select at least one prompt to delete.");
            return;
        }

        let confirmDelete = confirm("Are you sure you want to delete the selected prompts?");
        if (confirmDelete) {
            // Proceed with deletion
            $.ajax({
                url: '/main/prompts/delete/',
                method: 'POST',
                data: JSON.stringify({'promptIds': selectedPrompts}),
                contentType: "application/json; charset=utf-8",
                dataType: 'json',
                beforeSend: function (xhr) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                },
                success: function (response) {
                    // Reload or update prompts list
                    loadPrompts();
                },
                error: function () {
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



