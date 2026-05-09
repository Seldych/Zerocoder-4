document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('resume-form');
    var resumeOutput = document.getElementById('resume');
    var editToggle = document.getElementById('edit-toggle');
    var charCount = document.getElementById('char-count');

    function updateCharCount() {
        charCount.textContent = resumeOutput.value.length;
    }

    resumeOutput.addEventListener('input', updateCharCount);

    document.getElementById('pdf-btn').addEventListener('click', function () {
        var text = resumeOutput.value;
        if (!text || text === 'Генерация...' || text === resumeOutput.placeholder) {
            alert('Сначала сгенерируйте резюме.');
            return;
        }
        var form = document.createElement('form');
        form.method = 'POST';
        form.action = '/download-pdf';
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'text';
        input.value = text;
        form.appendChild(input);
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
    });

    document.getElementById('vk-btn').addEventListener('click', function () {
        var text = resumeOutput.value;
        var vkStatus = document.getElementById('vk-status');

        if (!text || text === 'Генерация...' || text === resumeOutput.placeholder) {
            vkStatus.textContent = 'Сначала сгенерируйте резюме.';
            vkStatus.className = 'vk-status vk-status-error';
            return;
        }

        vkStatus.textContent = 'Публикация...';
        vkStatus.className = 'vk-status';

        fetch('/post-to-vk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        })
            .then(function (res) { return res.json(); })
            .then(function (result) {
                if (result.error) {
                    vkStatus.textContent = 'Ошибка: ' + result.error;
                    vkStatus.className = 'vk-status vk-status-error';
                } else {
                    vkStatus.innerHTML = 'Опубликовано! <a href="' + result.url + '" target="_blank">Открыть пост</a>';
                    vkStatus.className = 'vk-status vk-status-ok';
                }
            })
            .catch(function () {
                vkStatus.textContent = 'Ошибка сети. Попробуйте снова.';
                vkStatus.className = 'vk-status vk-status-error';
            });
    });

    editToggle.addEventListener('click', function () {
        var isReadonly = resumeOutput.hasAttribute('readonly');
        if (isReadonly) {
            resumeOutput.removeAttribute('readonly');
            resumeOutput.classList.add('editable');
            editToggle.textContent = 'Заблокировать';
        } else {
            resumeOutput.setAttribute('readonly', '');
            resumeOutput.classList.remove('editable');
            editToggle.textContent = 'Редактировать';
        }
    });

    form.addEventListener('submit', function (event) {
        event.preventDefault();

        var data = {
            name: document.getElementById('name').value,
            vacancy: document.getElementById('vacancy').value,
            competencies: document.getElementById('competencies').value,
            age: document.getElementById('age').value,
            style: document.getElementById('style').value
        };

        resumeOutput.value = 'Генерация...';

        fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
            .then(function (response) {
                return response.json();
            })
            .then(function (result) {
                resumeOutput.value = result.text;
                updateCharCount();
            })
            .catch(function () {
                resumeOutput.value = 'Произошла ошибка. Попробуйте снова.';
            });
    });
});
