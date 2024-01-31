let modelPermissions = {};
const csrftoken = getCookie('csrftoken');
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

function fetchModelPermissions(modelNames) {
    $.ajax({
        url: '/main/get_perms/',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ models: modelNames }),
        beforeSend: function (xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
        success: function(response) {
            modelPermissions = response;
            console.log('Permissions fetched:', modelPermissions);
        },
        error: function(error) {
            console.error('Error fetching permissions:', error);
        }
    });
}
function check_perm(modelName, action) {
    return modelPermissions[modelName] && modelPermissions[modelName][`can_${action}`];
}
