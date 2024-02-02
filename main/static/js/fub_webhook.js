jQuery(document).ready(function ($) {
    fetchWebhooks();
    modelPermissions = fetchModelPermissions('FubWebhook');

    $('#addWebhook').click(function () {
        // Clear form fields for a new entry
        $('#webhookURL').val('');
        $('#webhookEvent').prop('readonly', false).val(''); // Enable and clear the event field for adding
        $('#editWebhookModal').modal('show');
        $('#editWebhookForm').attr('data-webhookId', ''); // Clear ID to indicate a new entry
    });
    $('#editWebhookForm').submit(function(e) {
        e.preventDefault(); // Prevent the default form submission
        const url = $('#webhookURL').val();
        const event = $('#webhookEvent').val(); // Capture the event value
        createWebhook(url, event); // Call createWebhook with URL and event
    });

    $('body').on('click', '.delete-webhook', function () {
        const id = $(this).data('id');
        deleteWebhook(id);
    });

    $('#deleteSelected').click(function () {
        $('.webhook-select:checked').each(function () {
            deleteWebhook($(this).val());
        });
    });
});

function fetchWebhooks() {
    $.ajax({
        url: '/main/fub_webhooks/fub_webhook_list',
        method: 'GET',
        success: function (data) {
            $('#webhookList').empty();
            console.log("fetchWebHooks: ", data)
            data.webhooks.forEach(function (webhook) {
                $('#webhookList').append(`
                    <tr>
                        <td><input type="checkbox" class="webhook-select" value="${webhook.id}"></td>
                        <td>${webhook.webhookId}</td>
                        <td>${webhook.event}</td>
                        <td><button class="btn btn-sm ${webhook.status === 'Active' ? 'btn-success' : 'btn-secondary'} toggle-status" data-id="${webhook.id}">${webhook.status}</button></td>
                        <td>${webhook.url.substr(-30)}</td>
                        <td>
                            <button class="btn btn-danger btn-sm delete-webhook" data-id="${webhook.id}">Delete</button>
                        </td>
                    </tr>
                `);
            });
        },
        error: function (xhr, status, error) {
            console.error("Error fetching webhooks: ", error);
        }
    });
}

$('#webhookList').on('click', '.toggle-status', function() {
    const id = $(this).data('id');
    const status = $(this).data('status'); // Assuming 'status' is stored as a data attribute
    toggleWebhookStatus(id, status); // Pass both ID and status to the function
});


function toggleWebhookStatus(id, currentStatus) {
    $.ajax({
        url: '/main/fub_webhooks/fub_webhook_toggle',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            id: id,
            status: currentStatus
        }),
        beforeSend: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken); // Ensure csrftoken is correctly defined
        },
        success: function() {
            fetchWebhooks(); // Reload webhook list to reflect changes
        },
        error: function(xhr, status, error) {
            console.error("Error toggling webhook status: ", error);
        }
    });
}


// function openEditModal(id) {
//     $.ajax({
//         url: `/main/fub_webhooks/fub_webhook_get/${id}`,
//         method: 'GET',
//         beforeSend: function (xhr) {
//                 xhr.setRequestHeader("X-CSRFToken", csrftoken);
//             },
//         success: function(data) {
//             $('#webhookURL').val(data.url);
//             $('#webhookEvent').prop('readonly', true).val(data.event); // Set readonly and populate for edit
//             $('#editWebhookForm').attr('data-webhookId', webhookId);
//             $('#editWebhookModal').modal('show');
//         },
//         error: function(xhr, status, error) {
//             console.error("Error opening edit modal: ", error);
//         }
//     });
// }

function createWebhook(url,event) {
    $.ajax({
        url: '/main/fub_webhooks/fub_webhook_add',
        method: 'POST',
        data: {
            url: url,
            event: event // Make sure this line is correctly capturing the event input's value
        },
        beforeSend: function (xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
        success: function () {
            $('#editWebhookModal').modal('hide');
            fetchWebhooks();
        },
        error: function (xhr, status, error) {
            console.error("Error creating webhook: ", error);
        }
    });
}

function deleteWebhook(webhookId) {
    $.ajax({
        url: `/main/fub_webhooks/fub_webhook_delete/${webhookId}`,
        method: 'POST',
        beforeSend: function (xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
        success: function () {
            fetchWebhooks();
        },
        error: function (xhr, status, error) {
            console.error("Error deleting webhook: ", error);
        }
    });
}
