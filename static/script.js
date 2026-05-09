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
