/**
 * Обработчик формы генерации резюме.
 * Отправляет данные на сервер и выводит результат.
 */
document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('resume-form');
    var resumeOutput = document.getElementById('resume');

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
            })
            .catch(function () {
                resumeOutput.value = 'Произошла ошибка. Попробуйте снова.';
            });
    });
});
