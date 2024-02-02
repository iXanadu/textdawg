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
        e.preventDefault();
        const url = $('#webhookURL').val();
        const event = $('#webhookEvent').val(); // Ensure you're capturing the event value
        const webhookId = $(this).data('webhook-id');

        if (webhookId) {
            updateWebhook(webhookId, url);
        } else {
            createWebhook(url, event); // Pass both URL and event here
        }
    });


    $('body').on('click', '.edit-webhook', function () {
        const id = $(this).data('id');
        openEditModal(id);
    });

    $('body').on('click', '.delete-webhook', function () {
        const id = $(this).data('id');
        deleteWebhook(id);
    });

    $('#selectAll').click(function () {
        $('.webhook-select').prop('checked', this.checked);
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
                            <button class="btn btn-info btn-sm edit-webhook" data-id="${webhook.id}">Edit</button>
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

function toggleWebhookStatus(webhookId) {
    $.ajax({
        url: `/main/fub_webhooks/fub_webhook_toggle/${webhookId}`,
        method: 'POST',
        beforeSend: function (xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
        success: function () {
            fetchWebhooks();
        },

        error: function (xhr, status, error) {
            console.error("Error toggling status: ", error);
        }
    });
}

function openEditModal(id) {
    $.ajax({
        url: `/main/fub_webhooks/fub_webhook_get/${id}`,
        method: 'GET',
        beforeSend: function (xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
        success: function(data) {
            $('#webhookURL').val(data.url);
            $('#webhookEvent').prop('readonly', true).val(data.event); // Set readonly and populate for edit
            $('#editWebhookForm').attr('data-webhookId', webhookId);
            $('#editWebhookModal').modal('show');
        },
        error: function(xhr, status, error) {
            console.error("Error opening edit modal: ", error);
        }
    });
}


function updateWebhook(webhookId, url) {
    $.ajax({
        url: `/main/fub_webhooks/fub_webhook_change/${webhookId}`,
        method: 'POST',
        data: {url: url},
        beforeSend: function (xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
        success: function () {
            $('#editWebhookModal').modal('hide');
            fetchWebhooks();
        },
        error: function (xhr, status, error) {
            console.error("Error updating webhook: ", error);
        }
    });
}

function createWebhook(url,event) {
    $.ajax({
        url: '/main/fub_webhooks/fub_webhook_register',
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
